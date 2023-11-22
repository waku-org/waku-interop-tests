from src.libs.custom_logger import get_custom_logger
import json
from dataclasses import asdict
from urllib.parse import quote
from src.node.api_clients.base_client import BaseClient

logger = get_custom_logger(__name__)


class REST(BaseClient):
    def __init__(self, rest_port):
        self._rest_port = rest_port

    def rest_call(self, method, endpoint, payload=None):
        url = f"http://127.0.0.1:{self._rest_port}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        return self.make_request(method, url, headers=headers, data=payload)

    def info(self):
        info_response = self.rest_call("get", "debug/v1/info")
        return info_response.json()

    def set_subscriptions(self, pubsub_topics):
        return self.rest_call("post", "relay/v1/subscriptions", json.dumps(pubsub_topics))

    def delete_subscriptions(self, pubsub_topics):
        return self.rest_call("delete", "relay/v1/subscriptions", json.dumps(pubsub_topics))

    def send_message(self, message, pubsub_topic):
        return self.rest_call("post", f"relay/v1/messages/{quote(pubsub_topic, safe='')}", json.dumps(message))

    def get_messages(self, pubsub_topic):
        get_messages_response = self.rest_call("get", f"relay/v1/messages/{quote(pubsub_topic, safe='')}")
        return get_messages_response.json()
