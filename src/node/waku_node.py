import os
import logging
from time import time
import requests
import json
from tenacity import retry, stop_after_delay, wait_fixed
from dataclasses import asdict
from src.node.docker_mananger import DockerManager
from src.env_vars import LOG_DIR, DEFAULT_PUBSUBTOPIC
from src.data_storage import DS
from src.libs.common import bytes_to_hex


logger = logging.getLogger(__name__)


class WakuNode:
    def __init__(self, docker_image, docker_log_prefix=""):
        self._image_name = docker_image
        self._log_path = os.path.join(LOG_DIR, f"{docker_log_prefix}__{self._image_name.replace('/', '_')}.log")
        self._docker_manager = DockerManager(self._image_name)
        self._container = None
        self._ext_ip = self._docker_manager.generate_random_ext_ip()
        logger.debug(f"WakuNode instance initialized with log path: {self._log_path}")

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def start(self, **kwargs):
        logger.debug("Starting Node...")
        self._docker_manager.create_network()
        ports = self._docker_manager.generate_ports()
        self._rpc_port = ports[0]
        self._websocket_port = ports[2]

        default_args = {
            "listen-address": "0.0.0.0",
            "rpc": "true",
            "rpc-admin": "true",
            "websocket-support": "true",
            "log-level": "TRACE",
            "websocket-port": str(ports[2]),
            "rpc-port": str(ports[0]),
            "tcp-port": str(ports[1]),
            "discv5-udp-port": str(ports[3]),
            "rpc-address": "0.0.0.0",
            "topic": DEFAULT_PUBSUBTOPIC,
            "nat": f"extip:{self._ext_ip}",
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

        logger.debug(f"Starting container with args: {default_args}")
        self._container = self._docker_manager.start_container(self._docker_manager.image, ports, default_args, self._log_path, self._ext_ip)
        logger.debug(f"Started container from image {self._image_name}. RPC port: {self._rpc_port} and WebSocket port: {self._websocket_port}")
        DS.waku_nodes.append(self)
        try:
            self.ensure_rpc_ready()
        except Exception as e:
            logger.error(f"RPC service did not become ready in time: {e}")
            raise

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def stop(self):
        if self._container:
            logger.debug("Stopping container with id %s", self._container.short_id)
            self._container.stop()
            logger.debug("Container stopped.")

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def rpc_call(self, method, params=[]):
        url = f"http://127.0.0.1:{self._rpc_port}"
        headers = {"Content-Type": "application/json"}
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        logger.debug("RPC call payload %s", payload)
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        return response.json()

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.05), reraise=True)
    def ensure_rpc_ready(self):
        self.info()
        logger.debug("RPC service is ready.")

    def info(self):
        return self.rpc_call("get_waku_v2_debug_v1_info", [])

    def set_subscriptions(self, pubsub_topics=[DEFAULT_PUBSUBTOPIC]):
        return self.rpc_call("post_waku_v2_relay_v1_subscriptions", [pubsub_topics])

    def send_message(self, message, pubsub_topic=DEFAULT_PUBSUBTOPIC):
        if message.timestamp is None:
            message.timestamp = int(time() * 1e9)
        return self.rpc_call("post_waku_v2_relay_v1_message", [pubsub_topic, asdict(message)])

    def get_messages(self, pubsub_topic=DEFAULT_PUBSUBTOPIC):
        return self.rpc_call("get_waku_v2_relay_v1_messages", [pubsub_topic])

    def get_asymmetric_key_pair(self):
        response = self.rpc_call("get_waku_v2_private_v1_asymmetric_keypair", [])
        seckey = response.get("seckey")
        pubkey = response.get("pubkey")
        private_key = response.get("privateKey")
        public_key = response.get("publicKey")
        if seckey:
            return {"privateKey": seckey, "publicKey": pubkey}
        else:
            return {"privateKey": private_key, "publicKey": public_key}

    def post_asymmetric_message(self, message, public_key, pubsub_topic=None):
        if not message.payload:
            raise Exception("Attempting to send an empty message")
        return self.rpc_call(
            "post_waku_v2_private_v1_asymmetric_message",
            [pubsub_topic or DEFAULT_PUBSUBTOPIC, message, "0x" + bytes_to_hex(public_key)],
        )

    def get_asymmetric_messages(self, private_key, pubsub_topic=None):
        return self.rpc_call(
            "get_waku_v2_private_v1_asymmetric_messages",
            [pubsub_topic or DEFAULT_PUBSUBTOPIC, "0x" + bytes_to_hex(private_key)],
        )

    def get_symmetric_key(self):
        return bytes.fromhex(self.rpc_call("get_waku_v2_private_v1_symmetric_key", []))

    def post_symmetric_message(self, message, sym_key, pubsub_topic=None):
        if not message.payload:
            raise Exception("Attempting to send an empty message")
        return self.rpc_call(
            "post_waku_v2_private_v1_symmetric_message",
            [pubsub_topic or DEFAULT_PUBSUBTOPIC, message, "0x" + bytes_to_hex(sym_key)],
        )

    def get_symmetric_messages(self, sym_key, pubsub_topic=None):
        return self.rpc_call(
            "get_waku_v2_private_v1_symmetric_messages",
            [pubsub_topic or DEFAULT_PUBSUBTOPIC, "0x" + bytes_to_hex(sym_key)],
        )

    def get_peer_id(self):
        # not implemented
        peer_id = ""
        return peer_id

    def get_multiaddr_with_id(self):
        peer_id = self.get_peer_id()
        multiaddr_with_id = f"/ip4/127.0.0.1/tcp/{self._websocket_port}/ws/p2p/{peer_id}"
        return multiaddr_with_id
