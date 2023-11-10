from src.libs.custom_logger import get_custom_logger
import math
from time import time
import pytest
import allure
from src.libs.common import to_base64, delay
from src.data_classes import message_rpc_response_schema
from src.env_vars import NODE_1, NODE_2
from src.node.waku_node import WakuNode
from tenacity import retry, stop_after_delay, wait_fixed

logger = get_custom_logger(__name__)


class StepsRelay:
    @pytest.fixture(scope="function", autouse=True)
    def setup_nodes(self, request):
        self.node1 = WakuNode(NODE_1, "node1_" + request.cls.test_id)
        self.node1.start(relay="true", discv5_discovery="true", peer_exchange="true")
        enr_uri = self.node1.info()["enrUri"]
        self.node2 = WakuNode(NODE_2, "node2_" + request.cls.test_id)
        self.node2.start(relay="true", discv5_discovery="true", discv5_bootstrap_node=enr_uri, peer_exchange="true")
        self.test_pubsub_topic = "/waku/2/rs/18/1"
        self.test_content_topic = "/test/1/waku-relay/proto"
        self.test_payload = "Relay works!!"
        self.test_message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        self.node1.set_subscriptions([self.test_pubsub_topic])
        self.node2.set_subscriptions([self.test_pubsub_topic])

    @pytest.fixture(scope="function", autouse=True)
    @retry(stop=stop_after_delay(120), wait=wait_fixed(1), reraise=True)
    def wait_for_network_to_warm_up(self):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        try:
            self.check_published_message_reaches_peer(message)
        except Exception as ex:
            raise Exception(f"WARM UP FAILED WITH: {ex}")

    @allure.step
    def check_published_message_reaches_peer(self, message, pubsub_topic=None, message_propagation_delay=0.1):
        if not pubsub_topic:
            pubsub_topic = self.test_pubsub_topic
        self.node1.send_message(message, pubsub_topic)

        delay(message_propagation_delay)
        get_messages_response = self.node2.get_messages(pubsub_topic)
        logger.debug("Got reponse from remote peer %s", get_messages_response)
        assert get_messages_response, "Peer node couldn't find any messages"
        received_message = message_rpc_response_schema.load(get_messages_response[0])
        self.assert_received_message(message, received_message)

    def assert_received_message(self, sent_message, received_message):
        def assert_fail_message(field_name):
            return f"Incorrect {field_name}. Published {sent_message[field_name]} Received {getattr(received_message, field_name)}"

        assert (
            received_message.payload == sent_message["payload"]
        ), f'Incorrect payload. Published {sent_message["payload"]} Received {received_message.payload}'
        assert (
            received_message.contentTopic == sent_message["contentTopic"]
        ), f'Incorrect contentTopic. Published {sent_message["contentTopic"]} Received {received_message.contentTopic}'
        if "timestamp" in sent_message and sent_message["timestamp"]:
            if isinstance(sent_message["timestamp"], float):
                assert math.isclose(float(received_message.timestamp), sent_message["timestamp"], rel_tol=1e-9), assert_fail_message("timestamp")
            else:
                assert str(received_message.timestamp) == str(sent_message["timestamp"]), assert_fail_message("timestamp")
        if "version" in sent_message and sent_message["version"]:
            assert str(received_message.version) == str(sent_message["version"]), assert_fail_message("version")
        if "meta" in sent_message and sent_message["meta"]:
            assert str(received_message.meta) == str(sent_message["meta"]), assert_fail_message("meta")
