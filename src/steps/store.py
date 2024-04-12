import inspect
import os
from src.libs.custom_logger import get_custom_logger
from time import time
import pytest
import allure
from src.libs.common import to_base64, delay, gen_step_id
from src.node.waku_message import MessageRpcResponseStore, WakuMessage, MessageRpcResponse
from src.env_vars import (
    ADDITIONAL_NODES,
    NODE_1,
    NODE_2,
)
from src.node.waku_node import WakuNode, rln_credential_store_ready
from tenacity import retry, stop_after_delay, wait_fixed
from src.test_data import VALID_PUBSUB_TOPICS

logger = get_custom_logger(__name__)


class StepsStore:
    test_content_topic = "/myapp/1/latest/proto"
    test_pubsub_topic = "/waku/2/rs/0/0"
    test_payload = "Store works!!"

    @pytest.fixture(scope="function", autouse=True)
    def store_setup(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.main_publishing_nodes = []
        self.store_nodes = []
        self.optional_nodes = []
        self.multiaddr_list = []

    @allure.step
    def add_node_peer(self, node):
        if node.is_nwaku():
            for multiaddr in self.multiaddr_list:
                node.add_peers([multiaddr])

    @allure.step
    def start_publishing_node(self, image, node_index, **kwargs):
        node = WakuNode(image, f"publishing_node{node_index}_{self.test_id}")
        node.start(**kwargs)
        if kwargs["relay"] == "true":
            self.main_publishing_nodes.extend([node])
        if kwargs["store"] == "true":
            self.store_nodes.extend([node])
        self.add_node_peer(node)
        self.multiaddr_list.extend([node.get_multiaddr_with_id()])
        return node

    @allure.step
    def setup_store_node(self, image, node_index, **kwargs):
        node = WakuNode(image, f"store_node{node_index}_{self.test_id}")
        node.start(discv5_bootstrap_node=self.enr_uri, storenode=self.multiaddr_list[0], **kwargs)
        if kwargs["relay"] == "true":
            self.main_publishing_nodes.extend([node])
        self.store_nodes.extend([node])
        self.add_node_peer(node)
        return node

    @allure.step
    def setup_first_publishing_node(self, store="true", relay="true", **kwargs):
        self.publishing_node1 = self.start_publishing_node(NODE_1, node_index=1, store=store, relay=relay, **kwargs)
        self.enr_uri = self.publishing_node1.get_enr_uri()

    @allure.step
    def setup_second_publishing_node(self, store, relay, **kwargs):
        self.publishing_node2 = self.start_publishing_node(NODE_1, node_index=2, store=store, relay=relay, **kwargs)

    @allure.step
    def setup_additional_publishing_nodes(self, node_list=ADDITIONAL_NODES, **kwargs):
        if node_list:
            nodes = [node.strip() for node in node_list.split(",") if node]
        else:
            pytest.skip("ADDITIONAL_NODES/node_list is empty, cannot run test")
        for index, node in enumerate(nodes):
            self.start_publishing_node(node, node_index=index + 2, store="true", relay="true", **kwargs)

    @allure.step
    def setup_first_store_node(self, store="true", relay="true", **kwargs):
        self.store_node1 = self.setup_store_node(NODE_2, node_index=1, store=store, relay=relay, **kwargs)

    @allure.step
    def setup_second_store_node(self, store="true", relay="false", **kwargs):
        self.store_node2 = self.setup_store_node(NODE_2, node_index=2, store=store, relay=relay, **kwargs)

    @allure.step
    def setup_additional_store_nodes(self, node_list=ADDITIONAL_NODES, **kwargs):
        if node_list:
            nodes = [node.strip() for node in node_list.split(",") if node]
        else:
            pytest.skip("ADDITIONAL_NODES/node_list is empty, cannot run test")
        self.additional_store_nodes = []
        for index, node in enumerate(nodes):
            node = self.setup_store_node(node, node_index=index + 2, store="true", relay="false", **kwargs)
            self.additional_store_nodes.append(node)

    @allure.step
    def subscribe_to_pubsub_topics_via_relay(self, node=None, pubsub_topics=None):
        if pubsub_topics is None:
            pubsub_topics = [self.test_pubsub_topic]
        if not node:
            node = self.main_publishing_nodes
        if isinstance(node, list):
            for node in node:
                node.set_relay_subscriptions(pubsub_topics)
        else:
            node.set_relay_subscriptions(pubsub_topics)

    @allure.step
    def subscribe_to_pubsub_topics_via_filter(self, node, pubsub_topic=None, content_topic=None):
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if content_topic is None:
            content_topic = [self.test_content_topic]
        subscription = {"requestId": "1", "contentFilters": content_topic, "pubsubTopic": pubsub_topic}
        node.set_filter_subscriptions(subscription)

    @allure.step
    def publish_message_via(self, type, pubsub_topic=None, message=None, message_propagation_delay=0.1, sender=None):
        if message is None:
            self.message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.publishing_node1
        if type == "relay":
            logger.debug("Relaying message")
            sender.send_relay_message(self.message, pubsub_topic)
        elif type == "lightpush":
            payload = self.create_payload(pubsub_topic, self.message)
            sender.send_light_push_message(payload)
        delay(message_propagation_delay)

    @allure.step
    def check_published_message_is_stored(
        self,
        store_node=None,
        peerAddr=None,
        includeData=None,
        pubsubTopic=None,
        contentTopics=None,
        startTime=None,
        endTime=None,
        hashes=None,
        cursor=None,
        pageSize=None,
        ascending=None,
        store_v="v3",
        **kwargs,
    ):
        if store_node is None:
            store_node = self.store_nodes
        elif not isinstance(store_node, list):
            store_node = [store_node]
        else:
            store_node = store_node
        for node in store_node:
            logger.debug(f"Checking that peer {node.image} can find the stored message")
            get_messages_response = node.get_store_messages(
                peerAddr=peerAddr,
                includeData=includeData,
                pubsubTopic=pubsubTopic,
                contentTopics=contentTopics,
                startTime=startTime,
                endTime=endTime,
                hashes=hashes,
                cursor=cursor,
                pageSize=pageSize,
                ascending=ascending,
                store_v=store_v,
                **kwargs,
            )

            assert "messages" in get_messages_response, f"Peer {node.image} has no messages key in the reponse"
            assert get_messages_response["messages"], f"Peer {node.image} couldn't find any messages"
            assert len(get_messages_response["messages"]) == 1, f"Expected 1 message but got {len(get_messages_response)}"
            waku_message = WakuMessage(get_messages_response["messages"], schema=MessageRpcResponseStore if node.is_nwaku() else MessageRpcResponse)
            waku_message.assert_received_message(self.message)

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
