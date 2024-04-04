import inspect
import os
from src.libs.custom_logger import get_custom_logger
from time import time
import pytest
import allure
from src.libs.common import to_base64, delay, gen_step_id
from src.node.waku_message import WakuMessage
from src.env_vars import (
    NODE_1,
    NODE_2,
)
from src.node.waku_node import WakuNode, rln_credential_store_ready
from tenacity import retry, stop_after_delay, wait_fixed
from src.test_data import VALID_PUBSUB_TOPICS

logger = get_custom_logger(__name__)


class StepsLightPush:
    test_content_topic = "/myapp/1/latest/proto"
    test_pubsub_topic = "/waku/2/rs/0/0"
    test_payload = "Light push works!!"

    @pytest.fixture(scope="function", autouse=True)
    def light_push_setup(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.main_receiving_nodes = []
        self.optional_nodes = []
        self.multiaddr_list = []

    @allure.step
    def setup_first_receiving_node(self, lightpush="true", relay="true", **kwargs):
        self.receiving_node1 = WakuNode(NODE_1, f"node1_{self.test_id}")
        self.receiving_node1.start(lightpush=lightpush, relay=relay, **kwargs)
        self.enr_uri = self.receiving_node1.get_enr_uri()
        self.main_receiving_nodes.extend([self.receiving_node1])
        self.multiaddr_list.extend([self.receiving_node1.get_multiaddr_with_id()])
        # self.node22 = WakuNode(NODE_1, f"node11_{self.test_id}")
        # self.node22.start(lightpush="true", relay="true", **kwargs)
        # self.enr_uri = self.node22.get_enr_uri()
        # self.multiaddr_with_id22 = self.node22.get_multiaddr_with_id()
        # self.main_receiving_nodes.extend([self.node22])

    @allure.step
    def setup_lightpush_node(self, lightpush="true", relay="false", **kwargs):
        self.light_push_node = WakuNode(NODE_2, f"node2_{self.test_id}")
        self.light_push_node.start(lightpush=lightpush, relay=relay, discv5_bootstrap_node=self.enr_uri, lightpushnode=self.multiaddr_list, **kwargs)
        if self.light_push_node.is_nwaku():
            for multiaddr in self.multiaddr_list:
                self.light_push_node.add_peers([multiaddr])
        if relay == "true":
            self.main_receiving_nodes.extend([self.light_push_node])

    @allure.step
    def subscribe_to_pubsub_topics_via_relay(self, node=None, pubsub_topics=None):
        if not pubsub_topics:
            pubsub_topics = [self.test_pubsub_topic]
        if not node:
            node = self.main_receiving_nodes
        if isinstance(node, list):
            for node in node:
                node.set_relay_subscriptions(pubsub_topics)
        else:
            node.set_relay_subscriptions(pubsub_topics)

    @allure.step
    def check_light_pushed_message_reaches_receiving_peer(
        self, pubsub_topic=None, message=None, message_propagation_delay=0.1, sender=None, peer_list=None
    ):
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.light_push_node
        if not peer_list:
            peer_list = self.main_receiving_nodes + self.optional_nodes
        payload = self.create_payload(pubsub_topic, message)
        sender.send_light_push_message(payload)
        delay(message_propagation_delay)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 1}:{peer.image} can find the published message")
            get_messages_response = peer.get_relay_messages(pubsub_topic)
            assert get_messages_response, f"Peer NODE_{index + 1}:{peer.image} couldn't find any messages"
            assert len(get_messages_response) == 1, f"Expected 1 message but got {len(get_messages_response)}"
            waku_message = WakuMessage(get_messages_response)
            waku_message.assert_received_message(payload["message"])

    @allure.step
    def create_message(self, **kwargs):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        message.update(kwargs)
        return message

    @allure.step
    def create_payload(self, pubsub_topic=None, message=None, **kwargs):
        if message is None:
            message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        payload = {"pubsubTopic": pubsub_topic, "message": message}
        payload.update(kwargs)
        return payload
