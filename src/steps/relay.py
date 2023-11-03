import logging
from time import sleep, time
import pytest
import allure
from src.data_classes import message_rpc_response_schema
from src.env_vars import NODE_1, NODE_2
from src.node.waku_node import WakuNode
from tenacity import retry, stop_after_delay, wait_fixed

logger = logging.getLogger(__name__)


class StepsRelay:
    @pytest.fixture(scope="function", autouse=True)
    def setup_nodes(self, request):
        self.node1 = WakuNode(NODE_1, request.cls.test_id)
        self.node1.start(relay="true", discv5_discovery="true", peer_exchange="true")
        enr_uri = self.node1.info()["enrUri"]
        self.node2 = WakuNode(NODE_2, request.cls.test_id)
        self.node2.start(relay="true", discv5_discovery="true", discv5_bootstrap_node=enr_uri, peer_exchange="true")
        self.test_pubsub_topic = "test"
        self.test_content_topic = "/test/1/waku-relay"
        self.test_payload = "Relay works!!"
        self.node1.set_subscriptions([self.test_pubsub_topic])
        self.node2.set_subscriptions([self.test_pubsub_topic])

    @allure.step
    @retry(stop=stop_after_delay(20), wait=wait_fixed(0.5), reraise=True)
    def check_published_message_reaches_peer(self, message):
        message.timestamp = int(time() * 1e9)
        self.node1.send_message(message, self.test_pubsub_topic)
        sleep(0.1)
        get_messages_response = self.node2.get_messages(self.test_pubsub_topic)
        logger.debug("Got reponse from remote peer %s", get_messages_response)
        received_message = message_rpc_response_schema.load(get_messages_response[0])
        assert received_message.payload == message.payload
        assert received_message.contentTopic == message.contentTopic
        assert received_message.timestamp == message.timestamp
