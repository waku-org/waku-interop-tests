import logging
import json
from dataclasses import asdict
from src.node.api_clients.base_client import BaseClient

logger = logging.getLogger(__name__)


class RPC(BaseClient):
    def __init__(self, rpc_port, image_name):
        self._image_name = image_name
        self._rpc_port = rpc_port

    def rpc_call(self, endpoint, params=[]):
        url = f"http://127.0.0.1:{self._rpc_port}"
        headers = {"Content-Type": "application/json"}
        payload = {"jsonrpc": "2.0", "method": endpoint, "params": params, "id": 1}
        return self.make_request("post", url, headers=headers, data=json.dumps(payload))

    def info(self):
        info_response = self.rpc_call("get_waku_v2_debug_v1_info", [])
        return info_response.json()["result"]

    def set_subscriptions(self, pubsub_topics):
        if "nwaku" in self._image_name:
            return self.rpc_call("post_waku_v2_relay_v1_subscriptions", [pubsub_topics])
        else:
            return self.rpc_call("post_waku_v2_relay_v1_subscription", [pubsub_topics])

    def send_message(self, message, pubsub_topic):
        return self.rpc_call("post_waku_v2_relay_v1_message", [pubsub_topic, message])

    def get_messages(self, pubsub_topic):
        get_messages_response = self.rpc_call("get_waku_v2_relay_v1_messages", [pubsub_topic])
        return get_messages_response.json()["result"]
