import inspect
from src.libs.custom_logger import get_custom_logger
from time import time
import pytest
import allure
from src.libs.common import to_base64, delay
from src.node.waku_message import WakuMessage
from src.env_vars import (
    NODE_1,
    NODE_2,
    ADDITIONAL_NODES,
    NODEKEY,
)
from src.node.waku_node import WakuNode

logger = get_custom_logger(__name__)


class StepsSharding:
    test_content_topic = "/toychat/2/huilong/proto"
    test_pubsub_topic = "/waku/2/rs/2/0"
    test_payload = "Sharding works!!"

    @pytest.fixture(scope="function", autouse=True)
    def relay_setup(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.main_nodes = []
        self.optional_nodes = []

    @allure.step
    def setup_first_relay_node(self, cluster_id=None, pubsub_topic=None, content_topic=None, **kwargs):
        self.node1 = WakuNode(NODE_1, f"node1_{self.test_id}")
        kwargs = self._resolve_sharding_flags(cluster_id, pubsub_topic, content_topic, **kwargs)
        self.node1.start(relay="true", nodekey=NODEKEY, **kwargs)
        self.enr_uri = self.node1.get_enr_uri()
        self.multiaddr_with_id = self.node1.get_multiaddr_with_id()
        self.main_nodes.extend([self.node1])

    @allure.step
    def setup_second_relay_node(self, cluster_id=None, pubsub_topic=None, content_topic=None, **kwargs):
        self.node2 = WakuNode(NODE_2, f"node2_{self.test_id}")
        kwargs = self._resolve_sharding_flags(cluster_id, pubsub_topic, content_topic, **kwargs)
        self.node2.start(relay="true", discv5_bootstrap_node=self.enr_uri, **kwargs)
        if self.node2.is_nwaku():
            self.node2.add_peers([self.multiaddr_with_id])
        self.main_nodes.extend([self.node2])

    @allure.step
    def setup_main_relay_nodes(self, cluster_id=None, pubsub_topic=None, content_topic=None, **kwargs):
        self.setup_first_relay_node(cluster_id, pubsub_topic, content_topic, **kwargs)
        self.setup_second_relay_node(cluster_id, pubsub_topic, content_topic, **kwargs)

    @allure.step
    def setup_optional_relay_nodes(self):
        if ADDITIONAL_NODES:
            nodes = [node.strip() for node in ADDITIONAL_NODES.split(",")]
        else:
            pytest.skip("ADDITIONAL_NODES is empty, cannot run test")
        for index, node in enumerate(nodes):
            node = WakuNode(node, f"node{index + 3}_{self.test_id}")
            node.start(relay="true", discv5_bootstrap_node=self.enr_uri)
            self.optional_nodes.append(node)

    @allure.step
    def subscribe_relay_node(self, node, content_topics, pubsub_topics):
        if content_topics:
            node.set_relay_auto_subscriptions(content_topics)
        elif pubsub_topics:
            node.set_relay_subscriptions(pubsub_topics)
        else:
            raise AttributeError("content_topics or pubsub_topics need to be passed")

    @allure.step
    def subscribe_first_relay_node(self, content_topics=None, pubsub_topics=None):
        self.subscribe_relay_node(self.node1, content_topics, pubsub_topics)

    @allure.step
    def subscribe_second_relay_node(self, content_topics=None, pubsub_topics=None):
        self.subscribe_relay_node(self.node2, content_topics, pubsub_topics)

    @allure.step
    def subscribe_main_relay_nodes(self, content_topics=None, pubsub_topics=None):
        for node in self.main_nodes:
            self.subscribe_relay_node(node, content_topics, pubsub_topics)

    @allure.step
    def subscribe_optional_relay_nodes(self, content_topics, pubsub_topics=None):
        for node in self.optional_nodes:
            self.subscribe_relay_node(node, content_topics, pubsub_topics)

    @allure.step
    def relay_message(self, node, message, pubsub_topic=None):
        if pubsub_topic:
            node.send_relay_message(message, pubsub_topic)
        else:
            node.send_relay_auto_message(message)

    @allure.step
    def retrieve_relay_message(self, node, content_topic=None, pubsub_topic=None):
        if content_topic:
            return node.get_relay_auto_messages(content_topic)
        elif pubsub_topic:
            return node.get_relay_messages(pubsub_topic)
        else:
            raise AttributeError("content_topic or pubsub_topic needs to be passed")

    @allure.step
    def check_published_message_reaches_relay_peer(
        self, message=None, content_topic=None, pubsub_topic=None, message_propagation_delay=0.1, sender=None, peer_list=None
    ):
        if message is None:
            message = self.create_message()
        if not sender:
            sender = self.node1
        if not peer_list:
            peer_list = self.main_nodes + self.optional_nodes

        self.relay_message(sender, message, pubsub_topic)
        delay(message_propagation_delay)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 1}:{peer.image} can find the published message")
            get_messages_response = self.retrieve_relay_message(peer, content_topic, pubsub_topic)
            assert get_messages_response, f"Peer NODE_{index + 1}:{peer.image} couldn't find any messages"
            assert len(get_messages_response) == 1, f"Expected 1 message but got {len(get_messages_response)}"
            waku_message = WakuMessage(get_messages_response)
            waku_message.assert_received_message(message)

    @allure.step
    def create_message(self, **kwargs):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        message.update(kwargs)
        return message

    def _resolve_sharding_flags(self, cluster_id=None, pubsub_topic=None, content_topic=None, **kwargs):
        if pubsub_topic:
            kwargs["pubsub_topic"] = pubsub_topic
            if not cluster_id:
                try:
                    if isinstance(pubsub_topic, list):
                        pubsub_topic = pubsub_topic[0]
                    cluster_id = pubsub_topic.split("/")[4]
                    logger.debug(f"Cluster id was resolved to: {cluster_id}")
                except Exception as ex:
                    raise Exception("Could not resolve cluster_id from pubsub_topic")
        kwargs["cluster_id"] = cluster_id
        if content_topic:
            kwargs["content_topic"] = content_topic
        return kwargs
