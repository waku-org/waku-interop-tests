import os

import pytest
from src.libs.common import delay
from src.libs.custom_logger import get_custom_logger
from tenacity import retry, stop_after_delay, wait_fixed
from src.node.api_clients.rpc import RPC
from src.node.api_clients.rest import REST
from src.node.docker_mananger import DockerManager
from src.env_vars import DOCKER_LOG_DIR, DEFAULT_PUBSUB_TOPIC, PROTOCOL
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
        self._rpc_port = self._ports[1]
        self._websocket_port = self._ports[3]
        self._tcp_port = self._ports[2]

        if PROTOCOL == "RPC":
            self._api = RPC(self._rpc_port, self._image_name)
        elif PROTOCOL == "REST":
            self._api = REST(self._rest_port)
        else:
            raise ValueError(f"Unknown protocol: {PROTOCOL}")

        default_args = {
            "listen-address": "0.0.0.0",
            "rpc": "true",
            "rpc-admin": "true",
            "rest": "true",
            "rest-admin": "true",
            "websocket-support": "true",
            "log-level": "TRACE",
            "rest-relay-cache-capacity": "100",
            "websocket-port": str(self._ports[3]),
            "rpc-port": self._rpc_port,
            "rest-port": self._rest_port,
            "tcp-port": str(self._ports[2]),
            "discv5-udp-port": str(self._ports[4]),
            "rpc-address": "0.0.0.0",
            "rest-address": "0.0.0.0",
            "nat": f"extip:{self._ext_ip}",
            "peer-exchange": "true",
            "discv5-discovery": "true",
        }

        if "go-waku" in self._docker_manager.image:
            go_waku_args = {
                "min-relay-peers-to-publish": "1",
                "legacy-filter": "false",
                "log-level": "DEBUG",
            }
            default_args.update(go_waku_args)

        for key, value in kwargs.items():
            key = key.replace("_", "-")
            default_args[key] = value

        self._container = self._docker_manager.start_container(self._docker_manager.image, self._ports, default_args, self._log_path, self._ext_ip)
        logger.debug(
            f"Started container from image {self._image_name}. RPC: {self._rpc_port} REST: {self._rest_port} WebSocket: {self._websocket_port} TCP: {self._tcp_port}"
        )
        DS.waku_nodes.append(self)
        delay(1)  # if we fire requests to soon after starting the node will sometimes fail to start correctly
        try:
            self.ensure_ready()
        except Exception as ex:
            logger.error(f"{PROTOCOL} service did not become ready in time: {ex}")
            raise

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def stop(self):
        if self._container:
            logger.debug(f"Stopping container with id {self._container.short_id}")
            self._container.stop()
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
        logger.info(f"{PROTOCOL} service is ready !!")

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
        if PROTOCOL == "RPC":
            pytest.skip("This method doesn't exist for RPC protocol")
        else:
            return self._api.update_filter_subscriptions(subscription)

    def get_filter_messages(self, content_topic):
        return self._api.get_filter_messages(content_topic)

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
