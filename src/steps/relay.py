import logging
from time import sleep
import pytest
from src.env_vars import NODE_1, NODE_2
from src.node.waku_node import WakuNode
from tenacity import retry, stop_after_delay, wait_fixed

logger = logging.getLogger(__name__)


class StepsRelay:
    @pytest.fixture(scope="function", autouse=True)
    def setup_nodes(self):
        self.node1 = WakuNode(NODE_1)
        self.node1.start(relay="true", discv5_discovery="true", peer_exchange="true")
        enr_uri = self.node1.info()["result"]["enrUri"]
        self.node2 = WakuNode(NODE_2)
        self.node2.start(relay="true", discv5_discovery="true", discv5_bootstrap_node=enr_uri, peer_exchange="true")
        self.node1.set_subscriptions()
        self.node2.set_subscriptions()
        self.default_content_topic = "/test/1/waku-relay"
        self.default_payload = "Relay works!!"

    @retry(stop=stop_after_delay(5), wait=wait_fixed(0.1), reraise=True)
    def check_published_message_reaches_peer(self, message):
        self.node1.send_message(message)
        sleep(0.1)
        get_messages_response = self.node2.get_messages()
        logger.debug("Got reponse from remote peer %s", get_messages_response)
        assert get_messages_response["result"][0]["payload"] == message.payload
        assert get_messages_response["result"][0]["contentTopic"] == message.contentTopic
        assert get_messages_response["result"][0]["timestamp"] == message.timestamp
