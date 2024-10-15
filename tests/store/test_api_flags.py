import pytest
from src.libs.custom_logger import get_custom_logger
from src.libs.common import to_base64
from src.node.waku_message import WakuMessage
from src.steps.store import StepsStore
from src.test_data import SAMPLE_INPUTS

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("node_setup")
class TestApiFlags(StepsStore):
    def test_store_with_peerAddr(self):
        self.publish_message()
        self.check_published_message_is_stored(store_node=self.store_node1, peer_addr=self.multiaddr_list[0])

    def test_store_with_wrongPeerAddr(self):
        self.publish_message()
        wrong_peer_addr = self.multiaddr_list[0][1:]
        logger.debug(f"logger is {wrong_peer_addr}")
        try:
            self.check_published_message_is_stored(store_node=self.store_node1, peer_addr=wrong_peer_addr)
            raise Exception("message restored with wrong peer address")
        except Exception as ex:
            logger.debug(f" response with wrong peer address is { ex.args[0]}")
            assert ex.args[0].find("Invalid MultiAddress") != -1

    def test_store_include_data(self):
        message_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_list.append(message)
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, include_data="true", page_size=50)
            assert len(store_response.messages) == len(SAMPLE_INPUTS)
            for index in range(len(store_response.messages)):
                assert store_response.message_payload(index) == message_list[index]["payload"]
                assert store_response.message_pubsub_topic(index) == self.test_pubsub_topic
                waku_message = WakuMessage([store_response.message_at(index)])
                waku_message.assert_received_message(message_list[index])

    def test_store_not_include_data(self):
        message = self.create_message()
        self.publish_message(message=message)
        store_response = self.get_messages_from_store(self.store_node1, include_data="false")
        logger.debug(f" message restored with hash only is {store_response.messages} ")
        assert "message" not in store_response.messages
