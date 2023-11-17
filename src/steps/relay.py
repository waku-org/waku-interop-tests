import inspect
from src.libs.custom_logger import get_custom_logger
import math
from time import time
import pytest
import allure
from src.libs.common import to_base64, delay
from src.data_classes import message_rpc_response_schema
from src.env_vars import NODE_LIST, NODEKEY, RUNNING_IN_CI
from src.node.waku_node import WakuNode
from tenacity import retry, stop_after_delay, wait_fixed

logger = get_custom_logger(__name__)


class StepsRelay:
    test_pubsub_topic = "/waku/2/rs/18/1"
    test_content_topic = "/test/1/waku-relay/proto"
    test_payload = "Relay works!!"
    optional_nodes = []

    @pytest.fixture(scope="function")
    def setup_main_relay_nodes(self, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.node1 = WakuNode(NODE_LIST[0], f"node1_{request.cls.test_id}")
        self.node1.start(relay="true", discv5_discovery="true", peer_exchange="true", nodekey=NODEKEY)
        self.enr_uri = self.node1.info()["enrUri"]
        self.node2 = WakuNode(NODE_LIST[1], f"node1_{request.cls.test_id}")
        self.node2.start(relay="true", discv5_discovery="true", discv5_bootstrap_node=self.enr_uri, peer_exchange="true")
        self.main_nodes = [self.node1, self.node2]

    @pytest.fixture(scope="function")
    def setup_optional_relay_nodes(self, setup_main_relay_nodes, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        for index, node in enumerate(NODE_LIST[2:]):
            node = WakuNode(node, f"node{index}_{request.cls.test_id}")
            node.start(relay="true", discv5_discovery="true", discv5_bootstrap_node=self.enr_uri, peer_exchange="true")
            self.optional_nodes.append(node)

    @pytest.fixture(scope="function")
    def subscribe_main_relay_nodes(self, setup_main_relay_nodes):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.ensure_subscriptions_on_nodes(self.main_nodes, [self.test_pubsub_topic])

    @allure.step
    def check_published_message_reaches_peer(self, message, pubsub_topic=None, message_propagation_delay=0.1, sender=None):
        if not sender:
            sender = self.node1
        peer_list = self.main_nodes + self.optional_nodes
        sender.send_message(message, pubsub_topic or self.test_pubsub_topic)
        delay(message_propagation_delay)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 1} {peer.image} can find the published message")
            get_messages_response = peer.get_messages(pubsub_topic or self.test_pubsub_topic)
            assert get_messages_response, f"Peer NODE_{index} {peer.image} couldn't find any messages"
            received_message = message_rpc_response_schema.load(get_messages_response[0])
            self.assert_received_message(message, received_message)

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

    def wait_for_published_message_to_reach_peer(self, timeout_duration=120 if RUNNING_IN_CI else 20, time_between_retries=1, sender=None):
        @retry(stop=stop_after_delay(timeout_duration), wait=wait_fixed(time_between_retries), reraise=True)
        def check_peer_connection():
            message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
            self.check_published_message_reaches_peer(message, sender=sender)

        check_peer_connection()

    def ensure_subscriptions_on_nodes(self, node_list, pubsub_topic_list):
        for node in node_list:
            node.set_subscriptions(pubsub_topic_list)

    def create_message(self, **kwargs):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        message.update(kwargs)
        return message
