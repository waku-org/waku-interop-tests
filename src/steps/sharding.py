import inspect
import os
from uuid import uuid4
from src.libs.custom_logger import get_custom_logger
from time import time
import pytest
import allure
from src.libs.common import to_base64, delay, gen_step_id
from src.node.waku_message import WakuMessage
from src.env_vars import (
    NODE_1,
    NODE_2,
    ADDITIONAL_NODES,
    NODEKEY,
    DEFAULT_NWAKU,
    RLN_CREDENTIALS,
)
from src.node.waku_node import WakuNode, rln_credential_store_ready
from tenacity import retry, stop_after_delay, wait_fixed
from src.test_data import VALID_PUBSUB_TOPICS

logger = get_custom_logger(__name__)


class StepsSharding:
    test_content_topic = "/toychat/2/huilong/proto"
    test_payload = "Sharding works!!"

    @pytest.fixture(scope="function", autouse=True)
    def relay_setup(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.main_nodes = []
        self.optional_nodes = []

    def setup_first_relay_node(self, cluster_id, **kwargs):
        self.node1 = WakuNode(NODE_1, f"node1_{self.test_id}")
        self.node1.start(relay="true", nodekey=NODEKEY, cluster_id=cluster_id, **kwargs)
        self.enr_uri = self.node1.get_enr_uri()
        self.multiaddr_with_id = self.node1.get_multiaddr_with_id()
        self.main_nodes.extend([self.node1])

    def setup_second_relay_node(self, cluster_id, **kwargs):
        self.node2 = WakuNode(NODE_2, f"node2_{self.test_id}")
        self.node2.start(relay="true", discv5_bootstrap_node=self.enr_uri, cluster_id=cluster_id, **kwargs)
        self.node2.add_peers([self.multiaddr_with_id])
        self.main_nodes.extend([self.node2])

    def setup_main_relay_nodes(self, cluster_id):
        self.setup_first_relay_node(cluster_id)
        self.setup_second_relay_node(cluster_id)

    def setup_optional_relay_nodes(self):
        if ADDITIONAL_NODES:
            nodes = [node.strip() for node in ADDITIONAL_NODES.split(",")]
        else:
            pytest.skip("ADDITIONAL_NODES is empty, cannot run test")
        for index, node in enumerate(nodes):
            node = WakuNode(node, f"node{index + 3}_{self.test_id}")
            node.start(relay="true", discv5_bootstrap_node=self.enr_uri)
            self.optional_nodes.append(node)

    def subscribe_first_relay_node(self, content_topics):
        self.node1.set_relay_auto_subscriptions(content_topics)

    def subscribe_second_relay_node(self, content_topics):
        self.node2.set_relay_auto_subscriptions(content_topics)

    def subscribe_main_relay_nodes(self, content_topics):
        self.ensure_relay_auto_subscriptions_on_nodes(self.main_nodes, content_topics)

    def subscribe_optional_relay_nodes(self, content_topics):
        self.ensure_relay_auto_subscriptions_on_nodes(self.optional_nodes, content_topics)

    def relay_warm_up(self):
        try:
            self.wait_for_published_message_to_reach_relay_peer()
            logger.info("WARM UP successful!!")
        except Exception as ex:
            raise TimeoutError(f"WARM UP FAILED WITH: {ex}")

    # this method should be used only for the tests that use the relay_warm_up fixture
    # otherwise use wait_for_published_message_to_reach_relay_peer
    @allure.step
    def check_published_message_reaches_relay_peer(
        self, message=None, content_topic=None, message_propagation_delay=0.1, sender=None, peer_list=None
    ):
        if message is None:
            message = self.create_message()
        if content_topic is None:
            content_topic = self.test_content_topic
        if not sender:
            sender = self.node1
        if not peer_list:
            peer_list = self.main_nodes + self.optional_nodes

        sender.send_relay_auto_message(message)
        delay(message_propagation_delay)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 1}:{peer.image} can find the published message")
            get_messages_response = peer.get_relay_auto_messages(content_topic)
            assert get_messages_response, f"Peer NODE_{index + 1}:{peer.image} couldn't find any messages"
            assert len(get_messages_response) == 1, f"Expected 1 message but got {len(get_messages_response)}"
            waku_message = WakuMessage(get_messages_response)
            waku_message.assert_received_message(message)

    @allure.step
    def check_publish_without_relay_subscription(self, pubsub_topic):
        try:
            self.node1.send_relay_message(self.create_message(), pubsub_topic)
            raise AssertionError("Publish with no subscription worked!!!")
        except Exception as ex:
            assert "Bad Request" in str(ex) or "Internal Server Error" in str(ex)

    # we need much bigger timeout in CI because we run tests in parallel there and the machine itself is slower
    @allure.step
    def wait_for_published_message_to_reach_relay_peer(self, timeout_duration=120, time_between_retries=1, sender=None, peer_list=None):
        @retry(stop=stop_after_delay(timeout_duration), wait=wait_fixed(time_between_retries), reraise=True)
        def publish_and_check_relay_peer():
            message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
            self.check_published_message_reaches_relay_peer(message, content_topic=self.test_content_topic, sender=sender, peer_list=peer_list)

        publish_and_check_relay_peer()

    @allure.step
    def ensure_relay_auto_subscriptions_on_nodes(self, node_list, content_topic_list):
        for node in node_list:
            node.set_relay_auto_subscriptions(content_topic_list)

    @allure.step
    def delete_relay_subscriptions_on_nodes(self, node_list, pubsub_topic_list):
        for node in node_list:
            node.delete_relay_subscriptions(pubsub_topic_list)

    @allure.step
    def create_message(self, **kwargs):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        message.update(kwargs)
        return message

    @allure.step
    @retry(stop=stop_after_delay(120), wait=wait_fixed(1), reraise=True)
    def subscribe_and_publish_with_retry(self, node_list, pubsub_topic_list):
        self.ensure_relay_subscriptions_on_nodes(node_list, pubsub_topic_list)
        self.check_published_message_reaches_relay_peer()

    @allure.step
    def register_rln_single_node(self, **kwargs):
        logger.debug("Registering RLN credentials for single node")
        self.node1 = WakuNode(DEFAULT_NWAKU, f"node1_{gen_step_id()}")
        self.node1.register_rln(rln_creds_source=kwargs["rln_creds_source"], rln_creds_id=kwargs["rln_creds_id"])

    @allure.step
    def check_rln_registration(self, key_id):
        current_working_directory = os.getcwd()
        creds_file_path = f"{current_working_directory}/keystore_{key_id}/keystore.json"
        try:
            rln_credential_store_ready(creds_file_path)
        except Exception as ex:
            logger.error(f"Credentials at {creds_file_path} not available: {ex}")
            raise
