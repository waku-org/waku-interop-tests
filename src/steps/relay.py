import logging
import math
from time import sleep, time
import pytest
import allure
from src.libs.common import to_base64
from src.data_classes import message_rpc_response_schema
from src.env_vars import NODE_1, NODE_2
from src.node.waku_node import WakuNode
from tenacity import retry, stop_after_delay, wait_fixed

logger = logging.getLogger(__name__)


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
        self.node1.set_subscriptions([self.test_pubsub_topic])
        self.node2.set_subscriptions([self.test_pubsub_topic])

    @pytest.fixture(scope="function", autouse=True)
    @retry(stop=stop_after_delay(40), wait=wait_fixed(1), reraise=True)
    def wait_for_network_to_warm_up(self):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        try:
            self.check_published_message_reaches_peer(message)
        except Exception as ex:
            raise Exception(f"WARM UP FAILED WITH: {ex}")

    @allure.step
    def check_published_message_reaches_peer(self, message):
        self.node1.send_message(message, self.test_pubsub_topic)
        sleep(0.1)
        get_messages_response = self.node2.get_messages(self.test_pubsub_topic)
        logger.debug("Got reponse from remote peer %s", get_messages_response)
        assert get_messages_response, "Peer node couldn't find any messages"
        received_message = message_rpc_response_schema.load(get_messages_response[0])
        assert (
            received_message.payload == message["payload"]
        ), f'Incorrect payload. Published {message["payload"]} Received {received_message.payload}'
        assert (
            received_message.contentTopic == message["contentTopic"]
        ), f'Incorrect contentTopic. Published {message["contentTopic"]} Received {received_message.contentTopic}'
        if "timestamp" in message and message["timestamp"]:
            assert_fail_message = f'Incorrect timestamp. Published {message["timestamp"]} Received {received_message.timestamp}'
            if isinstance(message["timestamp"], float):
                assert math.isclose(float(received_message.timestamp), message["timestamp"], rel_tol=1e-9), assert_fail_message
            else:
                assert str(received_message.timestamp) == str(message["timestamp"]), assert_fail_message
