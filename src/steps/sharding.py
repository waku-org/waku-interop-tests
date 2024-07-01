import inspect
from uuid import uuid4
from src.libs.custom_logger import get_custom_logger
from time import time
import pytest
import allure
from src.libs.common import to_base64, delay
from src.node.waku_message import WakuMessage
from src.env_vars import (
    DEFAULT_NWAKU,
    NODE_1,
    NODE_2,
    ADDITIONAL_NODES,
    NODEKEY,
)
from src.node.waku_node import WakuNode
from src.steps.common import StepsCommon
from src.steps.relay import StepsRelay

logger = get_custom_logger(__name__)


class StepsSharding(StepsRelay):
    test_content_topic = "/myapp/1/latest/proto"
    test_pubsub_topic = "/waku/2/rs/2/0"
    test_payload = "Sharding works!!"
    auto_cluster = 2

    @pytest.fixture(scope="function", autouse=True)
    def sharding_setup(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.main_nodes = []
        self.optional_nodes = []
        self.main_filter_nodes = []
        self.optional_filter_nodes = []

    @allure.step
    def setup_second_node_as_filter(self, cluster_id=None, pubsub_topic=None, content_topic=None, **kwargs):
        self.node2 = WakuNode(NODE_2, f"node2_{self.test_id}")
        kwargs = self._resolve_sharding_flags(cluster_id, pubsub_topic, content_topic, **kwargs)
        self.node2.start(relay="false", discv5_bootstrap_node=self.enr_uri, filternode=self.multiaddr_with_id, **kwargs)
        self.add_node_peer(self.node2, [self.multiaddr_with_id])
        self.main_filter_nodes.extend([self.node2])

    @allure.step
    def setup_main_relay_nodes(self, **kwargs):
        self.setup_first_relay_node(**kwargs)
        self.setup_second_relay_node(**kwargs)

    @allure.step
    def setup_optional_relay_nodes(self, **kwargs):
        if ADDITIONAL_NODES:
            nodes = [node.strip() for node in ADDITIONAL_NODES.split(",")]
        else:
            pytest.skip("ADDITIONAL_NODES is empty, cannot run test")
        for index, node in enumerate(nodes):
            node = WakuNode(node, f"node{index + 3}_{self.test_id}")
            node.start(relay="true", discv5_bootstrap_node=self.enr_uri, **kwargs)
            self.add_node_peer(node, [self.multiaddr_with_id])
            self.optional_nodes.append(node)

    @allure.step
    def setup_nwaku_relay_nodes(self, num_nodes, **kwargs):
        for index in range(num_nodes):
            node = WakuNode(DEFAULT_NWAKU, f"node{index + 3}_{self.test_id}")
            node.start(relay="true", discv5_bootstrap_node=self.enr_uri, **kwargs)
            self.add_node_peer(node, [self.multiaddr_with_id])
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
    def subscribe_main_nodes(self, content_topics=None, pubsub_topics=None):
        for node in self.main_nodes:
            self.subscribe_relay_node(node, content_topics, pubsub_topics)

    @allure.step
    def subscribe_optional_relay_nodes(self, content_topics=None, pubsub_topics=None):
        for node in self.optional_nodes:
            self.subscribe_relay_node(node, content_topics, pubsub_topics)

    @allure.step
    def unsubscribe_relay_node(self, node, content_topics, pubsub_topics):
        if content_topics:
            node.delete_relay_auto_subscriptions(content_topics)
        elif pubsub_topics:
            node.delete_relay_subscriptions(pubsub_topics)
        else:
            raise AttributeError("content_topics or pubsub_topics need to be passed")

    @allure.step
    def unsubscribe_first_relay_node(self, content_topics=None, pubsub_topics=None):
        self.unsubscribe_relay_node(self.node1, content_topics, pubsub_topics)

    @allure.step
    def unsubscribe_second_relay_node(self, content_topics=None, pubsub_topics=None):
        self.unsubscribe_relay_node(self.node2, content_topics, pubsub_topics)

    @allure.step
    def unsubscribe_main_relay_nodes(self, content_topics=None, pubsub_topics=None):
        for node in self.main_nodes:
            self.unsubscribe_relay_node(node, content_topics, pubsub_topics)

    @allure.step
    def unsubscribe_optional_relay_nodes(self, content_topics=None, pubsub_topics=None):
        for node in self.optional_nodes:
            self.unsubscribe_relay_node(node, content_topics, pubsub_topics)

    @allure.step
    def subscribe_filter_node(self, node, content_topics=None, pubsub_topic=None):
        subscription = {"requestId": str(uuid4()), "contentFilters": content_topics, "pubsubTopic": pubsub_topic}
        node.set_filter_subscriptions(subscription)

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
    def check_published_message_reaches_relay_peer(self, content_topic=None, pubsub_topic=None, sender=None, peer_list=None):
        message = self.create_message(contentTopic=content_topic) if content_topic else self.create_message()
        if not sender:
            sender = self.node1
        if not peer_list:
            peer_list = self.main_nodes + self.optional_nodes

        self.relay_message(sender, message, pubsub_topic)
        delay(0.1)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 1}:{peer.image} can find the published message")
            get_messages_response = self.retrieve_relay_message(peer, content_topic, pubsub_topic)
            assert get_messages_response, f"Peer NODE_{index + 1}:{peer.image} couldn't find any messages"
            assert len(get_messages_response) == 1, f"Expected 1 message but got {len(get_messages_response)}"
            waku_message = WakuMessage(get_messages_response)
            waku_message.assert_received_message(message)

    @allure.step
    def get_filter_messages(self, content_topic, pubsub_topic=None, node=None):
        if node is None:
            node = self.node2
        if node.is_gowaku():
            return node.get_filter_messages(content_topic, pubsub_topic)
        elif node.is_nwaku():
            return node.get_filter_messages(content_topic)
        else:
            raise NotImplementedError("Not implemented for this node type")

    @allure.step
    def check_published_message_reaches_filter_peer(self, content_topic=None, pubsub_topic=None, sender=None, peer_list=None):
        message = self.create_message(contentTopic=content_topic) if content_topic else self.create_message()
        if not sender:
            sender = self.node1
        if not peer_list:
            peer_list = self.main_filter_nodes + self.optional_filter_nodes

        self.relay_message(sender, message, pubsub_topic)
        delay(0.1)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 2}:{peer.image} can find the published message")
            get_messages_response = self.get_filter_messages(message["contentTopic"], pubsub_topic=pubsub_topic, node=peer)
            assert get_messages_response, f"Peer NODE_{index + 2}:{peer.image} couldn't find any messages"
            assert len(get_messages_response) == 1, f"Expected 1 message but got {len(get_messages_response)}"
            waku_message = WakuMessage(get_messages_response)
            waku_message.assert_received_message(message)

    @allure.step
    def check_published_message_doesnt_reach_relay_peer(self, pubsub_topic=None, content_topic=None):
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic, content_topic=content_topic)
            raise AssertionError("Retrieving messages on not subscribed content topic worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    @allure.step
    def check_publish_fails_on_not_subscribed_pubsub_topic(self, pubsub_topic):
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)
            raise AssertionError("Publishing messages on unsubscribed shard worked!!!")
        except Exception as ex:
            assert f"Failed to publish: Node not subscribed to topic: {pubsub_topic}" in str(ex)

    @allure.step
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
