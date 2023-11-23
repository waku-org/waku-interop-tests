import inspect
from src.libs.custom_logger import get_custom_logger
import math
from time import time
import pytest
import allure
from src.libs.common import to_base64, delay
from src.data_classes import message_rpc_response_schema
from src.env_vars import NODE_1, NODE_2, ADDITIONAL_NODES, NODEKEY, RUNNING_IN_CI
from src.node.waku_node import WakuNode
from tenacity import retry, stop_after_delay, wait_fixed

logger = get_custom_logger(__name__)


class StepsRelay:
    test_pubsub_topic = "/waku/2/rs/18/1"
    test_content_topic = "/test/1/waku-relay/proto"
    test_payload = "Relay works!!"

    @pytest.fixture(scope="function")
    def setup_main_relay_nodes(self, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.node1 = WakuNode(NODE_1, f"node1_{request.cls.test_id}")
        self.node1.start(relay="true", discv5_discovery="true", peer_exchange="true", nodekey=NODEKEY)
        try:
            self.enr_uri = self.node1.info()["enrUri"]
        except Exception as ex:
            raise AttributeError(f"Could not find enrUri in the info call because of error: {str(ex)}")
        self.node2 = WakuNode(NODE_2, f"node2_{request.cls.test_id}")
        self.node2.start(relay="true", discv5_discovery="true", discv5_bootstrap_node=self.enr_uri, peer_exchange="true")
        self.main_nodes = [self.node1, self.node2]
        self.optional_nodes = []

    @pytest.fixture(scope="function")
    def setup_optional_relay_nodes(self, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        if ADDITIONAL_NODES:
            nodes = [node.strip() for node in ADDITIONAL_NODES.split(",")]
        else:
            pytest.skip("ADDITIONAL_NODES is empty, cannot run test")
        for index, node in enumerate(nodes):
            node = WakuNode(node, f"node{index}_{request.cls.test_id}")
            node.start(relay="true", discv5_discovery="true", discv5_bootstrap_node=self.enr_uri, peer_exchange="true")
            self.optional_nodes.append(node)

    @pytest.fixture(scope="function")
    def subscribe_main_relay_nodes(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.ensure_subscriptions_on_nodes(self.main_nodes, [self.test_pubsub_topic])

    @pytest.fixture(scope="function")
    def subscribe_optional_relay_nodes(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.ensure_subscriptions_on_nodes(self.optional_nodes, [self.test_pubsub_topic])

    @pytest.fixture(scope="function")
    def relay_warm_up(self):
        try:
            self.wait_for_published_message_to_reach_peer()
            logger.info("WARM UP successful!!")
        except Exception as ex:
            raise TimeoutError(f"WARM UP FAILED WITH: {ex}")

    # this method should be used only for the tests that use the warm_up fixture
    # otherwise use wait_for_published_message_to_reach_peer
    @allure.step
    def check_published_message_reaches_peer(self, message=None, pubsub_topic=None, message_propagation_delay=0.1, sender=None, peer_list=None):
        if message is None:
            message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.node1
        if not peer_list:
            peer_list = self.main_nodes + self.optional_nodes

        sender.send_message(message, pubsub_topic)
        delay(message_propagation_delay)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 1}:{peer.image} can find the published message")
            get_messages_response = peer.get_messages(pubsub_topic)
            assert get_messages_response, f"Peer NODE_{index}:{peer.image} couldn't find any messages"
            received_message = message_rpc_response_schema.load(get_messages_response[0])
            self.assert_received_message(message, received_message)

    @allure.step
    def check_publish_without_subscription(self, pubsub_topic):
        try:
            self.node1.send_message(self.create_message(), pubsub_topic)
            raise AssertionError("Publish with no subscription worked!!!")
        except Exception as ex:
            assert "Bad Request" in str(ex) or "Internal Server Error" in str(ex)

    # we need much bigger timeout in CI because we run tests in parallel there and the machine itself is slower
    @allure.step
    def wait_for_published_message_to_reach_peer(
        self, timeout_duration=120 if RUNNING_IN_CI else 20, time_between_retries=1, pubsub_topic=None, sender=None, peer_list=None
    ):
        @retry(stop=stop_after_delay(timeout_duration), wait=wait_fixed(time_between_retries), reraise=True)
        def check_peer_connection():
            message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
            self.check_published_message_reaches_peer(message, pubsub_topic=pubsub_topic, sender=sender, peer_list=peer_list)

        check_peer_connection()

    @allure.step
    def assert_received_message(self, sent_message, received_message):
        def assert_fail_message(field_name):
            return f"Incorrect field: {field_name}. Published: {sent_message[field_name]} Received: {getattr(received_message, field_name)}"

        assert received_message.payload == sent_message["payload"], assert_fail_message("payload")
        assert received_message.contentTopic == sent_message["contentTopic"], assert_fail_message("contentTopic")
        if sent_message.get("timestamp") is not None:
            if isinstance(sent_message["timestamp"], float):
                assert math.isclose(float(received_message.timestamp), sent_message["timestamp"], rel_tol=1e-9), assert_fail_message("timestamp")
            else:
                assert str(received_message.timestamp) == str(sent_message["timestamp"]), assert_fail_message("timestamp")
        if "version" in sent_message:
            assert str(received_message.version) == str(sent_message["version"]), assert_fail_message("version")
        if "meta" in sent_message:
            assert str(received_message.meta) == str(sent_message["meta"]), assert_fail_message("meta")
        if "ephemeral" in sent_message:
            assert str(received_message.ephemeral) == str(sent_message["ephemeral"]), assert_fail_message("ephemeral")
        if "rateLimitProof" in sent_message:
            assert str(received_message.rateLimitProof) == str(sent_message["rateLimitProof"]), assert_fail_message("rateLimitProof")

    @allure.step
    def ensure_subscriptions_on_nodes(self, node_list, pubsub_topic_list):
        for node in node_list:
            node.set_subscriptions(pubsub_topic_list)

    @allure.step
    def delete_subscriptions_on_nodes(self, node_list, pubsub_topic_list):
        for node in node_list:
            node.delete_subscriptions(pubsub_topic_list)

    def create_message(self, **kwargs):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        message.update(kwargs)
        return message
