import errno
import json
import os
import shutil

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


def select_private_key(prv_keys, key_id):
    for key in prv_keys:
        if key.endswith(key_id):
            return key

    raise ValueError("No matching key was found")


def sanitize_docker_flags(input_flags):
    output_flags = {}
    for key, value in input_flags.items():
        key = key.replace("_", "-")
        output_flags[key] = value

    return output_flags


@retry(stop=stop_after_delay(180), wait=wait_fixed(0.5), reraise=True)
def rln_credential_store_ready(creds_file_path):
    if os.path.exists(creds_file_path):
        return True
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), creds_file_path)


def peer_info2multiaddr(peer, is_nwaku=True):
    if is_nwaku:
        return peer["multiaddr"]
    else:
        return peer["multiaddrs"][0]


def peer_info2id(peer, is_nwaku=True):
    return peer_info2multiaddr(peer, is_nwaku).split("/")[-1]


def multiaddr2id(multiaddr):
    return multiaddr.split("/")[-1]


def resolve_sharding_flags(kwargs):
    if "pubsub_topic" in kwargs:
        pubsub_topic = kwargs["pubsub_topic"]
        if not "cluster_id" in kwargs:
            try:
                if isinstance(pubsub_topic, list):
                    pubsub_topic = pubsub_topic[0]
                cluster_id = pubsub_topic.split("/")[4]
                logger.debug(f"Cluster id was resolved to: {cluster_id}")
                kwargs["cluster_id"] = cluster_id
            except Exception as ex:
                raise Exception("Could not resolve cluster_id from pubsub_topic")
    return kwargs


class WakuNode:
    def __init__(self, docker_image, docker_log_prefix=""):
        self._image_name = docker_image
        self._log_path = os.path.join(DOCKER_LOG_DIR, f"{docker_log_prefix}__{self._image_name.replace('/', '_')}.log")
        self._docker_manager = DockerManager(self._image_name)
        self._container = None
        logger.debug(f"WakuNode instance initialized with log path {self._log_path}")

    @retry(stop=stop_after_delay(60), wait=wait_fixed(0.1), reraise=True)
    def start(self, wait_for_node_sec=20, **kwargs):
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
            "rln-creds-id": None,
            "rln-creds-source": None,
        }

        if self.is_gowaku():
            go_waku_args = {
                "min-relay-peers-to-publish": "1",
                "log-level": "DEBUG",
                "rest-filter-cache-capacity": "50",
                "peer-store-capacity": "10",
            }
            default_args.update(go_waku_args)
        elif self.is_nwaku():
            nwaku_args = {
                "shard": "0",
                "metrics-server": "true",
                "metrics-server-address": "0.0.0.0",
                "metrics-server-port": self._metrics_port,
                "metrics-logging": "true",
            }
            default_args.update(nwaku_args)
        else:
            raise NotImplementedError("Not implemented for this node type")

        if "remove_container" in kwargs:
            remove_container = kwargs["remove_container"]
            del kwargs["remove_container"]
        else:
            remove_container = True

        kwargs = self.parse_peer_persistence_config(kwargs)
        kwargs = resolve_sharding_flags(kwargs)

        default_args.update(sanitize_docker_flags(kwargs))

        rln_args, rln_creds_set, keystore_path = self.parse_rln_credentials(default_args, False)

        del default_args["rln-creds-id"]
        del default_args["rln-creds-source"]

        if rln_creds_set:
            rln_credential_store_ready(keystore_path)
            default_args.update(rln_args)
        else:
            logger.info(f"RLN credentials not set or credential store not available, starting without RLN")

        logger.debug(f"Using volumes {self._volumes}")

        self._container = self._docker_manager.start_container(
            self._docker_manager.image,
            ports=self._ports,
            args=default_args,
            log_path=self._log_path,
            container_ip=self._ext_ip,
            volumes=self._volumes,
            remove_container=remove_container,
        )

        logger.debug(f"Started container from image {self._image_name}. REST: {self._rest_port}")
        DS.waku_nodes.append(self)
        delay(1)  # if we fire requests to soon after starting the node will sometimes fail to start correctly
        try:
            self.ensure_ready(timeout_duration=wait_for_node_sec)
        except Exception as ex:
            logger.error(f"REST service did not become ready in time: {ex}")
            raise

    @retry(stop=stop_after_delay(250), wait=wait_fixed(0.1), reraise=True)
    def register_rln(self, **kwargs):
        logger.debug("Registering RLN credentials...")
        self._docker_manager.create_network()
        self._ext_ip = self._docker_manager.generate_random_ext_ip()
        self._ports = self._docker_manager.generate_ports()
        self._rest_port = self._ports[0]
        self._api = REST(self._rest_port)
        self._volumes = []

        default_args = {
            "rln-creds-id": None,
            "rln-creds-source": None,
        }

        default_args.update(sanitize_docker_flags(kwargs))

        rln_args, rln_creds_set, keystore_path = self.parse_rln_credentials(default_args, True)

        if rln_creds_set:
            self._container = self._docker_manager.start_container(
                self._docker_manager.image, self._ports, rln_args, self._log_path, self._ext_ip, self._volumes
            )

            logger.debug(f"Executed container from image {self._image_name}. REST: {self._rest_port} to register RLN")

            logger.debug(f"Waiting for keystore {keystore_path}")
            try:
                rln_credential_store_ready(keystore_path)
            except Exception as ex:
                logger.error(f"File {keystore_path} with RLN credentials did not become available in time {ex}")
                raise
        else:
            logger.warn("RLN credentials not set, no action performed")

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def stop(self):
        if self._container:
            logger.debug(f"Stopping container with id {self._container.short_id}")
            self._container.stop()
            try:
                self._container.remove()
            except:
                pass
            self._container = None
            logger.debug("Container stopped.")

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def kill(self):
        if self._container:
            logger.debug(f"Killing container with id {self._container.short_id}")
            self._container.kill()
            try:
                self._container.remove()
            except:
                pass
            self._container = None
            logger.debug("Container killed.")

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

    def ensure_ready(self, timeout_duration=10):
        @retry(stop=stop_after_delay(timeout_duration), wait=wait_fixed(0.1), reraise=True)
        def check_healthy(node=self):
            self.health_response = node.health()
            if self.health_response == b"Node is healthy":
                logger.info("Node is healthy !!")
                return

            try:
                self.health_response = json.loads(self.health_response)
            except Exception as ex:
                raise AttributeError(f"Unknown health response format {ex}")

            if self.health_response.get("nodeHealth") != "Ready":
                raise AssertionError("Waiting for the node health status: Ready")

            for p in self.health_response.get("protocolsHealth"):
                if p.get("Rln Relay") != "Ready":
                    raise AssertionError("Waiting for the Rln relay status: Ready")

            logger.info("Node protocols are initialized !!")

        @retry(stop=stop_after_delay(timeout_duration), wait=wait_fixed(0.1), reraise=True)
        def check_ready(node=self):
            node.info_response = node.info()
            logger.info("REST service is ready !!")

        if self.is_nwaku():
            check_healthy()
        check_ready()

    def get_id(self):
        try:
            return self.info_response["listenAddresses"][0].split("/")[-1]
        except Exception as ex:
            raise AttributeError(f"Could not find ID in the info call because of error: {str(ex)}")

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

    def health(self):
        return self._api.health()

    def get_peers(self):
        return self._api.get_peers()

    def add_peers(self, peers):
        return self._api.add_peers(peers)

    def set_relay_subscriptions(self, pubsub_topics):
        return self._api.set_relay_subscriptions(pubsub_topics)

    def set_relay_auto_subscriptions(self, content_topics):
        return self._api.set_relay_auto_subscriptions(content_topics)

    def delete_relay_subscriptions(self, pubsub_topics):
        return self._api.delete_relay_subscriptions(pubsub_topics)

    def delete_relay_auto_subscriptions(self, content_topics):
        return self._api.delete_relay_auto_subscriptions(content_topics)

    def send_relay_message(self, message, pubsub_topic):
        return self._api.send_relay_message(message, pubsub_topic)

    def send_relay_auto_message(self, message):
        return self._api.send_relay_auto_message(message)

    def send_light_push_message(self, payload):
        return self._api.send_light_push_message(payload)

    def get_relay_messages(self, pubsub_topic):
        return self._api.get_relay_messages(pubsub_topic)

    def get_relay_auto_messages(self, content_topic):
        return self._api.get_relay_auto_messages(content_topic)

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

    def get_store_messages(
        self,
        peer_addr=None,
        include_data=None,
        pubsub_topic=None,
        content_topics=None,
        start_time=None,
        end_time=None,
        hashes=None,
        cursor=None,
        page_size=None,
        ascending=None,
        store_v="v3",
        **kwargs,
    ):
        return self._api.get_store_messages(
            peer_addr=peer_addr,
            include_data=include_data,
            pubsub_topic=pubsub_topic,
            content_topics=content_topics,
            start_time=start_time,
            end_time=end_time,
            hashes=hashes,
            cursor=cursor,
            page_size=page_size,
            ascending=ascending,
            store_v=store_v,
            **kwargs,
        )

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

    def parse_rln_credentials(self, default_args, is_registration):
        rln_args = {}
        keystore_path = None

        rln_creds_source = default_args["rln-creds-source"]
        selected_id = default_args["rln-creds-id"]

        if rln_creds_source is None or selected_id is None:
            logger.debug(f"RLN credentials were not set")
            return rln_args, False, keystore_path

        imported_creds = json.loads(rln_creds_source)

        if len(imported_creds) < 4 or any(value is None for value in imported_creds.values()):
            logger.warn(f"One or more of required RLN credentials were not set properly")
            return rln_args, False, keystore_path

        eth_private_key = select_private_key(imported_creds, selected_id)

        current_working_directory = os.getcwd()

        if self.is_nwaku():
            if is_registration:
                rln_args.update(
                    {
                        "generateRlnKeystore": None,
                        "--execute": None,
                    }
                )
            else:
                rln_args.update(
                    {
                        "rln-relay": "true",
                    }
                )

            rln_args.update(
                {
                    "rln-relay-cred-path": "/keystore/keystore.json",
                    "rln-relay-cred-password": imported_creds["rln-relay-cred-password"],
                    "rln-relay-eth-client-address": imported_creds["rln-relay-eth-client-address"],
                    "rln-relay-eth-contract-address": imported_creds["rln-relay-eth-contract-address"],
                    "rln-relay-eth-private-key": imported_creds[eth_private_key],
                }
            )

            keystore_path = current_working_directory + "/keystore_" + selected_id + "/keystore.json"

            self._volumes.extend(
                [
                    current_working_directory + "/rln_tree_" + selected_id + ":/etc/rln_tree",
                    current_working_directory + "/keystore_" + selected_id + ":/keystore",
                ]
            )

        else:
            raise NotImplementedError("Not implemented for type other than Nim Waku ")

        return rln_args, True, keystore_path

    def parse_peer_persistence_config(self, kwargs):
        if kwargs.get("peer_persistence") == "true":
            if self.is_gowaku():
                kwargs["persist_peers"] = kwargs["peer_persistence"]
                del kwargs["peer_persistence"]

            cwd = os.getcwd()
            # Please note, as of now, peerdb is stored directly at / which is not shareable between containers.
            # Volume related code is usable after https://github.com/waku-org/nwaku/issues/2792 would be resolved.
            self._volumes.extend(
                [
                    cwd + "/peerdb" + ":/shared",
                ]
            )

            shutil.rmtree(cwd + "/peerdb")

        return kwargs

    @property
    def container(self):
        return self._container
