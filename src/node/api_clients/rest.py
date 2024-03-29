from src.libs.custom_logger import get_custom_logger
import json
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

    def get_peers(self):
        info_response = self.rest_call("get", "admin/v1/peers")
        return info_response.json()

    def set_relay_subscriptions(self, pubsub_topics):
        return self.rest_call("post", "relay/v1/subscriptions", json.dumps(pubsub_topics))

    def delete_relay_subscriptions(self, pubsub_topics):
        return self.rest_call("delete", "relay/v1/subscriptions", json.dumps(pubsub_topics))

    def send_relay_message(self, message, pubsub_topic):
        return self.rest_call("post", f"relay/v1/messages/{quote(pubsub_topic, safe='')}", json.dumps(message))

    def get_relay_messages(self, pubsub_topic):
        get_messages_response = self.rest_call("get", f"relay/v1/messages/{quote(pubsub_topic, safe='')}")
        return get_messages_response.json()

    def set_filter_subscriptions(self, subscription):
        set_subscriptions_response = self.rest_call("post", "filter/v2/subscriptions", json.dumps(subscription))
        return set_subscriptions_response.json()

    def update_filter_subscriptions(self, subscription):
        update_subscriptions_response = self.rest_call("put", "filter/v2/subscriptions", json.dumps(subscription))
        return update_subscriptions_response.json()

    def delete_filter_subscriptions(self, subscription):
        delete_subscriptions_response = self.rest_call("delete", "filter/v2/subscriptions", json.dumps(subscription))
        return delete_subscriptions_response.json()

    def delete_all_filter_subscriptions(self, request_id):
        delete_all_subscriptions_response = self.rest_call("delete", "filter/v2/subscriptions/all", json.dumps(request_id))
        return delete_all_subscriptions_response.json()

    def ping_filter_subscriptions(self, request_id):
        ping_subscriptions_response = self.rest_call("get", f"filter/v2/subscriptions/{quote(request_id, safe='')}")
        return ping_subscriptions_response.json()

    def get_filter_messages(self, content_topic, pubsub_topic=None):
        if pubsub_topic is not None:
            endpoint = f"filter/v2/messages/{quote(pubsub_topic, safe='')}/{quote(content_topic, safe='')}"
        else:
            endpoint = f"filter/v2/messages/{quote(content_topic, safe='')}"
        get_messages_response = self.rest_call("get", endpoint)
        return get_messages_response.json()
