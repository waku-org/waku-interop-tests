import os
import pytest
import requests
from src.libs.common import delay
from src.libs.custom_logger import get_custom_logger
from tenacity import retry, stop_after_delay, wait_fixed
from src.node.api_clients.rest import REST
from src.node.docker_mananger import DockerManager
from src.env_vars import DOCKER_LOG_DIR
from src.data_storage import DS

logger = get_custom_logger(__name__)


class WakuNode:
    def __init__(self, docker_image, docker_log_prefix=""):
        self._image_name = docker_image
        self._log_path = os.path.join(DOCKER_LOG_DIR, f"{docker_log_prefix}__{self._image_name.replace('/', '_')}.log")
        self._docker_manager = DockerManager(self._image_name)
        self._container = None
        logger.debug(f"WakuNode instance initialized with log path {self._log_path}")

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def start(self, **kwargs):
        logger.debug("Starting Node...")
        self._docker_manager.create_network()
        self._ext_ip = self._docker_manager.generate_random_ext_ip()
        self._ports = self._docker_manager.generate_ports()
        self._rest_port = self._ports[0]
        self._tcp_port = self._ports[1]
        self._websocket_port = self._ports[2]
        self._discv5_port = self._ports[3]
        self._metrics_port = self._ports[4]
        self._api = REST(self._rest_port)
        self._volumes = []

        default_args = {
            "listen-address": "0.0.0.0",
            "rest": "true",
            "rest-admin": "true",
            "websocket-support": "true",
            "log-level": "TRACE",
            "rest-relay-cache-capacity": "100",
            "websocket-port": self._websocket_port,
            "rest-port": self._rest_port,
            "tcp-port": self._tcp_port,
            "discv5-udp-port": self._discv5_port,
            "rest-address": "0.0.0.0",
            "nat": f"extip:{self._ext_ip}",
            "peer-exchange": "true",
            "discv5-discovery": "true",
            "cluster-id": "0",
            "rln-creds": {},
            "rln-register-only": False,
        }

        if self.is_gowaku():
            go_waku_args = {
                "min-relay-peers-to-publish": "1",
                "legacy-filter": "false",
                "log-level": "DEBUG",
                "rest-filter-cache-capacity": "50",
            }
            default_args.update(go_waku_args)
        elif self.is_nwaku():
            nwaku_args = {
                "metrics-server": "true",
                "metrics-server-address": "0.0.0.0",
                "metrics-server-port": self._metrics_port,
                "metrics-logging": "true",
            }
            default_args.update(nwaku_args)
        else:
            raise NotImplementedError("Not implemented for this node type")

        for key, value in kwargs.items():
            key = key.replace("_", "-")
            default_args[key] = value

        rln_args = {}
        rln_register_only = default_args["rln-register-only"]
        rln_credentials_set = all(value is not None for value in default_args["rln-creds"].values())

        if rln_credentials_set and len(default_args["rln-creds"] > 0):
            logger.warn(f"RLN credentials are not set properly, starting without RLN")

        if rln_credentials_set:
            if self.is_gowaku():
                if rln_register_only:
                    rln_args["generate-rln-credentials"] = None

                self._volumes.extend(["/go-waku_rln_tree:/etc/rln_tree", "/go-waku_keystore:/keystore"])

                rln_args.update(
                    {
                        "eth-client-address": default_args["rln-creds"]["eth_client_address"],
                        "eth-account-private-key": default_args["rln-creds"]["eth_client_private_key"],
                        "cred-password": default_args["rln-creds"]["keystore_password"],
                        "eth-contract-address": default_args["rln-creds"]["eth_contract_address"],
                        "cred-path": "/keystore/keystore.json",
                    }
                )

            elif self.is_nwaku():
                if rln_register_only:
                    rln_args["generateRlnKeystore"] = None
                    rln_args["--execute"] = None

                self._volumes.extend(["/nwaku_rln_tree:/etc/rln_tree", "/nwaku_keystore:/keystore"])

                rln_args.update(
                    {
                        "rln-relay-eth-client-address": default_args["rln-creds"]["eth_client_address"],
                        "rln-relay-eth-private-key": default_args["rln-creds"]["eth_client_private_key"],
                        "rln-relay-cred-password": default_args["rln-creds"]["keystore_password"],
                        "rln-relay-eth-contract-address": default_args["rln-creds"]["eth_contract_address"],
                        "rln-relay-cred-path": "/keystore/keystore.json",
                    }
                )

            default_args.update(rln_args)

        del default_args["rln-creds"]
        del default_args["rln-register-only"]

        if rln_register_only:
            self._container = self._docker_manager.start_container(
                self._docker_manager.image, self._ports, rln_args, self._log_path, self._ext_ip, self._volumes
            )
            logger.debug(f"Executed container from image {self._image_name}. REST: {self._rest_port} to register RLN")

        else:
            self._container = self._docker_manager.start_container(
                self._docker_manager.image, self._ports, default_args, self._log_path, self._ext_ip, self._volumes
            )
            logger.debug(f"Started container from image {self._image_name}. REST: {self._rest_port} with RLN enabled")
            DS.waku_nodes.append(self)
            delay(1)  # if we fire requests to soon after starting the node will sometimes fail to start correctly
            try:
                self.ensure_ready()
            except Exception as ex:
                logger.error(f"REST service did not become ready in time: {ex}")
                raise

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def stop(self):
        if self._container:
            logger.debug(f"Stopping container with id {self._container.short_id}")
            self._container.stop()
            self._container = None
            logger.debug("Container stopped.")

    def restart(self):
        if self._container:
            logger.debug(f"Restarting container with id {self._container.short_id}")
            self._container.restart()

    def pause(self):
        if self._container:
            logger.debug(f"Pausing container with id {self._container.short_id}")
            self._container.pause()

    def unpause(self):
        if self._container:
            logger.debug(f"Unpause container with id {self._container.short_id}")
            self._container.unpause()

    @retry(stop=stop_after_delay(10), wait=wait_fixed(0.1), reraise=True)
    def ensure_ready(self):
        self.info_response = self.info()
        logger.info("REST service is ready !!")

    def get_enr_uri(self):
        try:
            return self.info_response["enrUri"]
        except Exception as ex:
            raise AttributeError(f"Could not find enrUri in the info call because of error: {str(ex)}")

    def get_multiaddr_with_id(self):
        addresses = self.info_response.get("listenAddresses", [])
        ws_address = next((addr for addr in addresses if "/ws" not in addr), None)
        if ws_address:
            identifier = ws_address.split("/p2p/")[-1]
            new_address = f"/ip4/{self._ext_ip}/tcp/{self._tcp_port}/p2p/{identifier}"
            return new_address
        else:
            raise AttributeError("No '/ws' address found")

    def info(self):
        return self._api.info()

    def set_relay_subscriptions(self, pubsub_topics):
        return self._api.set_relay_subscriptions(pubsub_topics)

    def delete_relay_subscriptions(self, pubsub_topics):
        return self._api.delete_relay_subscriptions(pubsub_topics)

    def send_relay_message(self, message, pubsub_topic):
        return self._api.send_relay_message(message, pubsub_topic)

    def get_relay_messages(self, pubsub_topic):
        return self._api.get_relay_messages(pubsub_topic)

    def set_filter_subscriptions(self, subscription):
        return self._api.set_filter_subscriptions(subscription)

    def update_filter_subscriptions(self, subscription):
        return self._api.update_filter_subscriptions(subscription)

    def delete_filter_subscriptions(self, subscription):
        return self._api.delete_filter_subscriptions(subscription)

    def delete_all_filter_subscriptions(self, request_id):
        return self._api.delete_all_filter_subscriptions(request_id)

    def ping_filter_subscriptions(self, request_id):
        return self._api.ping_filter_subscriptions(request_id)

    def get_filter_messages(self, content_topic, pubsub_topic=None):
        return self._api.get_filter_messages(content_topic, pubsub_topic)

    def get_metrics(self):
        if self.is_nwaku():
            metrics = requests.get(f"http://localhost:{self._metrics_port}/metrics")
            metrics.raise_for_status()
            return metrics.content.decode("utf-8")
        else:
            pytest.skip(f"This method doesn't exist for node {self.type()}")

    @property
    def image(self):
        return self._image_name

    def type(self):
        if self.is_nwaku():
            return "nwaku"
        elif self.is_gowaku():
            return "gowaku"
        else:
            raise ValueError("Unknown node type!!!")

    def is_nwaku(self):
        return "nwaku" in self.image

    def is_gowaku(self):
        return "go-waku" in self.image
