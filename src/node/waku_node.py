import os
import logging
from tenacity import retry, stop_after_delay, wait_fixed
from src.node.api_clients.rpc import RPC
from src.node.api_clients.rest import REST
from src.node.docker_mananger import DockerManager
from src.env_vars import LOG_DIR, DEFAULT_PUBSUBTOPIC, PROTOCOL
from src.data_storage import DS

logger = logging.getLogger(__name__)


class WakuNode:
    def __init__(self, docker_image, docker_log_prefix=""):
        self._image_name = docker_image
        self._log_path = os.path.join(LOG_DIR, f"{docker_log_prefix}__{self._image_name.replace('/', '_')}.log")
        self._docker_manager = DockerManager(self._image_name)
        self._container = None
        logger.debug("WakuNode instance initialized with log path %s", self._log_path)

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def start(self, **kwargs):
        logger.debug("Starting Node...")
        self._docker_manager.create_network()
        self._ext_ip = self._docker_manager.generate_random_ext_ip()
        self._ports = self._docker_manager.generate_ports()
        self._rest_port = self._ports[0]
        self._rpc_port = self._ports[1]
        self._websocket_port = self._ports[2]

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
            "websocket-port": str(self._ports[3]),
            "rpc-port": self._rpc_port,
            "rest-port": self._rest_port,
            "tcp-port": str(self._ports[2]),
            "discv5-udp-port": str(self._ports[4]),
            "rpc-address": "0.0.0.0",
            "rest-address": "0.0.0.0",
            "nat": f"extip:{self._ext_ip}",
            "pubsub-topic": DEFAULT_PUBSUBTOPIC,
        }

        if "go-waku" in self._docker_manager.image:
            go_waku_args = {
                "min-relay-peers-to-publish": "0",
                "legacy-filter": "false",
                "log-level": "DEBUG",
            }
            default_args.update(go_waku_args)

        for key, value in kwargs.items():
            key = key.replace("_", "-")
            default_args[key] = value

        self._container = self._docker_manager.start_container(self._docker_manager.image, self._ports, default_args, self._log_path, self._ext_ip)
        logger.debug(
            "Started container from image %s. RPC: %s REST: %s WebSocket: %s", self._image_name, self._rpc_port, self._rest_port, self._websocket_port
        )
        DS.waku_nodes.append(self)
        try:
            self.ensure_ready()
        except Exception as e:
            logger.error("%s service did not become ready in time: %s", PROTOCOL, e)
            raise

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def stop(self):
        if self._container:
            logger.debug("Stopping container with id %s", self._container.short_id)
            self._container.stop()
            logger.debug("Container stopped.")

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.05), reraise=True)
    def ensure_ready(self):
        self.info()
        logger.debug("RPC service is ready.")

    def info(self):
        return self._api.info()

    def set_subscriptions(self, pubsub_topics=[DEFAULT_PUBSUBTOPIC]):
        return self._api.set_subscriptions(pubsub_topics)

    def send_message(self, message, pubsub_topic=DEFAULT_PUBSUBTOPIC):
        return self._api.send_message(message, pubsub_topic)

    def get_messages(self, pubsub_topic=DEFAULT_PUBSUBTOPIC):
        return self._api.get_messages(pubsub_topic)
