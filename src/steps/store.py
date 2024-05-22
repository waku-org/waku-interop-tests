import inspect
from src.libs.custom_logger import get_custom_logger
import pytest
import allure
from src.libs.common import delay
from src.node.waku_message import WakuMessage
from src.env_vars import (
    ADDITIONAL_NODES,
    NODE_1,
    NODE_2,
    NODEKEY,
)
from src.node.waku_node import WakuNode
from src.steps.common import StepsCommon

logger = get_custom_logger(__name__)


class StepsStore(StepsCommon):
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

    @pytest.fixture(scope="function", autouse=False)
    def node_setup(self, store_setup):
        self.setup_first_publishing_node(store="true", relay="true")
        self.setup_first_store_node(store="true", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()

    @allure.step
    def start_publishing_node(self, image, node_index, **kwargs):
        node = WakuNode(image, f"publishing_node{node_index}_{self.test_id}")
        node.start(**kwargs)
        if kwargs["relay"] == "true":
            self.main_publishing_nodes.extend([node])
        if kwargs["store"] == "true":
            self.store_nodes.extend([node])
        self.add_node_peer(node, self.multiaddr_list)
        self.multiaddr_list.extend([node.get_multiaddr_with_id()])
        return node

    @allure.step
    def setup_store_node(self, image, node_index, **kwargs):
        node = WakuNode(image, f"store_node{node_index}_{self.test_id}")
        node.start(discv5_bootstrap_node=self.enr_uri, storenode=self.multiaddr_list[0], **kwargs)
        if kwargs["relay"] == "true":
            self.main_publishing_nodes.extend([node])
        self.store_nodes.extend([node])
        self.add_node_peer(node, self.multiaddr_list)
        return node

    @allure.step
    def setup_first_publishing_node(self, store="true", relay="true", **kwargs):
        self.publishing_node1 = self.start_publishing_node(NODE_1, node_index=1, store=store, relay=relay, nodekey=NODEKEY, **kwargs)
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
    def publish_message(self, via="relay", pubsub_topic=None, message=None, message_propagation_delay=0.01, sender=None):
        self.message = self.create_message() if message is None else message
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.publishing_node1
        if via == "relay":
            logger.debug("Relaying message")
            sender.send_relay_message(self.message, pubsub_topic)
        elif via == "lightpush":
            payload = self.create_payload(pubsub_topic, self.message)
            sender.send_light_push_message(payload)
        delay(message_propagation_delay)
        return self.message

    def get_messages_from_store(
        self,
        node=None,
        peer_addr=None,
        include_data=None,
        pubsub_topic=None,
        content_topics=None,
        start_time=None,
        end_time=None,
        hashes=None,
        cursor=None,
        page_size=None,
        ascending="true",
        store_v="v3",
        **kwargs,
    ):
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if node.is_gowaku() and content_topics is None:
            content_topics = self.test_content_topic
        return node.get_store_messages(
            peer_addr=peer_addr,
            include_data=include_data,
            pubsub_topic=pubsub_topic,
            content_topics=content_topics,
            start_time=start_time,
            end_time=end_time,
            hashes=hashes,
            cursor=cursor,
            page_size=page_size,
            ascending=ascending,
            store_v=store_v,
            **kwargs,
        )

    @allure.step
    def check_published_message_is_stored(
        self,
        store_node=None,
        peer_addr=None,
        include_data=None,
        pubsub_topic=None,
        content_topics=None,
        start_time=None,
        end_time=None,
        hashes=None,
        cursor=None,
        page_size=None,
        ascending=None,
        store_v="v3",
        message_to_check=None,
        **kwargs,
    ):
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if message_to_check is None:
            message_to_check = self.message
        if store_node is None:
            store_node = self.store_nodes
        elif not isinstance(store_node, list):
            store_node = [store_node]
        else:
            store_node = store_node
        for node in store_node:
            logger.debug(f"Checking that peer {node.image} can find the stored message")
            self.store_response = self.get_messages_from_store(
                node=node,
                peer_addr=peer_addr,
                include_data=include_data,
                pubsub_topic=pubsub_topic,
                content_topics=content_topics,
                start_time=start_time,
                end_time=end_time,
                hashes=hashes,
                cursor=cursor,
                page_size=page_size,
                ascending=ascending,
                store_v=store_v,
                **kwargs,
            )

            assert "messages" in self.store_response, f"Peer {node.image} has no messages key in the reponse"
            assert self.store_response["messages"], f"Peer {node.image} couldn't find any messages. Actual response: {self.store_response}"
            assert len(self.store_response["messages"]) >= 1, "Expected at least 1 message but got none"
            store_message_index = -1  # we are looking for the last and most recent message in the store
            waku_message = WakuMessage(self.store_response["messages"][store_message_index:])
            if store_v == "v1":
                waku_message.assert_received_message(message_to_check)
            else:
                expected_hash = self.compute_message_hash(pubsub_topic, message_to_check)
                if node.is_nwaku():
                    actual = self.store_response["messages"][store_message_index]["messageHash"]
                else:
                    actual = self.store_response["messages"][store_message_index]["message_hash"]
                assert expected_hash == actual, f"Message hash returned by store doesn't match the computed message hash {expected_hash}"

    @allure.step
    def check_store_returns_empty_response(self, pubsub_topic=None):
        if not pubsub_topic:
            pubsub_topic = self.test_pubsub_topic
        try:
            self.check_published_message_is_stored(pubsubTopic=pubsub_topic, page_size=5, ascending="true")
        except Exception as ex:
            assert "couldn't find any messages" in str(ex)

    @allure.step
    def create_payload(self, pubsub_topic=None, message=None, **kwargs):
        if message is None:
            message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        payload = {"pubsubTopic": pubsub_topic, "message": message}
        payload.update(kwargs)
        return payload
