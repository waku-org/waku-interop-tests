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
    RUNNING_IN_CI,
    ETH_CLIENT_ADDRESS,
    ETH_TESTNET_KEY,
    KEYSTORE_PASSWORD,
    ETH_CONTRACT_ADDRESS,
)
from src.node.waku_node import WakuNode
from tenacity import retry, stop_after_delay, wait_fixed
from src.test_data import VALID_PUBSUB_TOPICS

logger = get_custom_logger(__name__)


class StepsRelay:
    test_pubsub_topic = VALID_PUBSUB_TOPICS[1]
    test_content_topic = "/test/1/waku-relay/proto"
    test_payload = "Relay works!!"

    @pytest.fixture(scope="function", autouse=True)
    def relay_setup(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.main_nodes = []
        self.optional_nodes = []

    @pytest.fixture(scope="function")
    def setup_main_relay_nodes(self, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.node1 = WakuNode(NODE_1, f"node1_{request.cls.test_id}")
        self.node1.start(relay="true", nodekey=NODEKEY)
        self.enr_uri = self.node1.get_enr_uri()
        self.node2 = WakuNode(NODE_2, f"node2_{request.cls.test_id}")
        self.node2.start(relay="true", discv5_bootstrap_node=self.enr_uri)
        self.main_nodes.extend([self.node1, self.node2])

    @pytest.fixture(scope="function")
    def setup_main_rln_relay_nodes(self, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.node1 = WakuNode(NODE_1, f"node1_{request.cls.test_id}")
        rln_creds = {
            "eth_client_address": ETH_CLIENT_ADDRESS,
            "eth_client_private_key": ETH_TESTNET_KEY,
            "keystore_password": KEYSTORE_PASSWORD,
            "eth_contract_address": ETH_CONTRACT_ADDRESS,
        }
        self.node1.start(relay="true", nodekey=NODEKEY, rln_creds=rln_creds, rln_register_only=True)
        self.enr_uri = self.node1.get_enr_uri()
        self.node2 = WakuNode(NODE_2, f"node2_{request.cls.test_id}")
        self.node2.start(relay="true", discv5_bootstrap_node=self.enr_uri, rln_creds=rln_creds, rln_register_only=True)
        self.main_nodes.extend([self.node1, self.node2])

    @pytest.fixture(scope="function")
    def setup_optional_relay_nodes(self, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        if ADDITIONAL_NODES:
            nodes = [node.strip() for node in ADDITIONAL_NODES.split(",")]
        else:
            pytest.skip("ADDITIONAL_NODES is empty, cannot run test")
        for index, node in enumerate(nodes):
            node = WakuNode(node, f"additional_node{index}_{request.cls.test_id}")
            node.start(relay="true", discv5_bootstrap_node=self.enr_uri)
            self.optional_nodes.append(node)

    @pytest.fixture(scope="function")
    def subscribe_main_relay_nodes(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.ensure_relay_subscriptions_on_nodes(self.main_nodes, [self.test_pubsub_topic])

    @pytest.fixture(scope="function")
    def subscribe_optional_relay_nodes(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.ensure_relay_subscriptions_on_nodes(self.optional_nodes, [self.test_pubsub_topic])

    @pytest.fixture(scope="function")
    def relay_warm_up(self):
        try:
            self.wait_for_published_message_to_reach_relay_peer()
            logger.info("WARM UP successful!!")
        except Exception as ex:
            raise TimeoutError(f"WARM UP FAILED WITH: {ex}")

    # this method should be used only for the tests that use the relay_warm_up fixture
    # otherwise use wait_for_published_message_to_reach_relay_peer
    @allure.step
    def check_published_message_reaches_relay_peer(self, message=None, pubsub_topic=None, message_propagation_delay=0.1, sender=None, peer_list=None):
        if message is None:
            message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.node1
        if not peer_list:
            peer_list = self.main_nodes + self.optional_nodes

        sender.send_relay_message(message, pubsub_topic)
        delay(message_propagation_delay)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 1}:{peer.image} can find the published message")
            get_messages_response = peer.get_relay_messages(pubsub_topic)
            assert get_messages_response, f"Peer NODE_{index}:{peer.image} couldn't find any messages"
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
    def wait_for_published_message_to_reach_relay_peer(
        self, timeout_duration=120 if RUNNING_IN_CI else 20, time_between_retries=1, pubsub_topic=None, sender=None, peer_list=None
    ):
        @retry(stop=stop_after_delay(timeout_duration), wait=wait_fixed(time_between_retries), reraise=True)
        def check_peer_connection():
            message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
            self.check_published_message_reaches_relay_peer(message, pubsub_topic=pubsub_topic, sender=sender, peer_list=peer_list)

        check_peer_connection()

    @allure.step
    def ensure_relay_subscriptions_on_nodes(self, node_list, pubsub_topic_list):
        for node in node_list:
            node.set_relay_subscriptions(pubsub_topic_list)

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
    @retry(stop=stop_after_delay(30), wait=wait_fixed(1), reraise=True)
    def subscribe_and_publish_with_retry(self, node_list, pubsub_topic_list):
        self.ensure_relay_subscriptions_on_nodes(node_list, pubsub_topic_list)
        self.check_published_message_reaches_relay_peer()
