import pytest
from src.env_vars import NODE_2
from src.libs.common import to_base64
from src.libs.custom_logger import get_custom_logger
from src.steps.store import StepsStore
from src.test_data import SAMPLE_INPUTS

logger = get_custom_logger(__name__)


@pytest.mark.xfail("go-waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1109")
@pytest.mark.usefixtures("node_setup")
class TestHashes(StepsStore):
    def test_store_with_hashes(self):
        message_hash_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            for message_hash in message_hash_list:
                store_response = self.get_messages_from_store(node, hashes=message_hash, page_size=50)
                assert len(store_response.messages) == 1
                assert store_response.message_hash(0) == message_hash

    def test_store_with_multiple_hashes(self):
        message_hash_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, hashes=f"{message_hash_list[0]},{message_hash_list[4]}", page_size=50)
            assert len(store_response.messages) == 2
            assert store_response.message_hash(0) == message_hash_list[0], "Incorrect messaged filtered based on multiple hashes"
            assert store_response.message_hash(1) == message_hash_list[4], "Incorrect messaged filtered based on multiple hashes"

    def test_store_with_wrong_hash(self):
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        wrong_hash = self.compute_message_hash(self.test_pubsub_topic, self.create_message(payload=to_base64("test")))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, hashes=wrong_hash, page_size=50)
            assert not store_response.messages, "Messages found"

    def test_store_with_invalid_hash(self):
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        invalid_hash = to_base64("test")
        for node in self.store_nodes:
            try:
                store_response = self.get_messages_from_store(node, hashes=invalid_hash, page_size=50)
                assert not store_response.messages
            except Exception as ex:
                assert "waku message hash parsing error: invalid hash length" in str(ex)

    def test_store_with_non_base64_hash(self):
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        non_base64_hash = "test"
        for node in self.store_nodes:
            try:
                store_response = self.get_messages_from_store(node, hashes=non_base64_hash, page_size=50)
                assert not store_response.messages
            except Exception as ex:
                assert "waku message hash parsing error: invalid hash length" in str(ex)
