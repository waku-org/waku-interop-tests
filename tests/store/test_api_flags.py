import pytest
from src.env_vars import NODE_1
from src.libs.common import to_base64
from src.libs.custom_logger import get_custom_logger
from src.node.waku_message import WakuMessage
from src.steps.store import StepsStore
from src.test_data import SAMPLE_INPUTS

logger = get_custom_logger(__name__)

# TO DO test without pubsubtopic freezes


@pytest.mark.usefixtures("node_setup")
class TestApiFlags(StepsStore):
    def test_store_with_peerAddr(self):
        self.publish_message()
        self.check_published_message_is_stored(store_node=self.store_node1, peer_addr=self.multiaddr_list[0])

    def test_store_with_hashes(self):
        message_hash_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            for message_hash in message_hash_list:
                store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, hashes=message_hash, page_size=50, ascending="true")
                assert len(store_response["messages"]) == 1
                assert store_response["messages"][0]["messageHash"] == message_hash

    def test_store_with_multiple_hashes(self):
        message_hash_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = node.get_store_messages(
                pubsub_topic=self.test_pubsub_topic, hashes=f"{message_hash_list[0]},{message_hash_list[4]}", page_size=50, ascending="true"
            )
            assert len(store_response["messages"]) == 2
            assert store_response["messages"][0]["messageHash"] == message_hash_list[0], "Incorrect messaged filtered based on multiple hashes"
            assert store_response["messages"][1]["messageHash"] == message_hash_list[4], "Incorrect messaged filtered based on multiple hashes"

    def test_store_include_data(self):
        message_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_list.append(message)
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, include_data="true", page_size=50)
            assert len(store_response["messages"]) == len(SAMPLE_INPUTS)
            for index, message in enumerate(store_response["messages"]):
                assert message["message"]["payload"] == message_list[index]["payload"]
                assert message["pubsubTopic"] == self.test_pubsub_topic
                waku_message = WakuMessage([message["message"]])
                waku_message.assert_received_message(message_list[index])
