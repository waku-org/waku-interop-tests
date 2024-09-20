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
            store_response = self.get_messages_from_store(node, hashes=f"{message_hash_list[0]},{message_hash_list[4]}",
                                                          page_size=50)
            assert len(store_response.messages) == 2
            assert store_response.message_hash(0) == message_hash_list[
                0], "Incorrect messaged filtered based on multiple hashes"
            assert store_response.message_hash(1) == message_hash_list[
                4], "Incorrect messaged filtered based on multiple hashes"

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

    # Addon on Test

    # Test when the hashes parameter is an empty string.
    def test_store_with_empty_hashes(self):
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))

        # Test with an empty string for the hashes parameter
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, hashes="", page_size=50)
            assert len(store_response.messages) == 4, "Messages found"

    # Test when the hash is longer than the valid length (e.g., 45 characters or more).
    def test_store_with_excessive_length_hash(self):
        excessive_length_hash = 'A' * 50  # Exceeds valid length of 44 characters for a Base64-encoded hash
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))

        for node in self.store_nodes:
            store_response = self.get_store_messages_with_errors(node, hashes=excessive_length_hash, page_size=50)
            print("store_response:", store_response)

            # Check if the response has a "messages" key and if it's empty
            assert "messages" not in store_response or not store_response.get("messages",
                                                                              []), "Messages found for an excessive length hash"

    # Test the behavior when you supply an empty hash alongside valid hashes.
    def test_store_with_empty_and_valid_hash(self):
        message_hash_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))

        empty_hash = ""
        for node in self.store_nodes:
            try:
                # Combining valid hash with an empty hash
                store_response = self.get_messages_from_store(node, hashes=f"{message_hash_list[0]},{empty_hash}", page_size=50)
                assert len(store_response.messages) == 1, "Message count mismatch with empty and valid hashes"
            except Exception as ex:
                assert "waku message hash parsing error" in str(ex), "Unexpected error for combined empty and valid hash"

    # Test for hashes that include non-Base64 characters.
    def test_store_with_non_base64_characters_in_hash(self):
        non_base64_hash = "###INVALID###"  # Invalid hash with non-Base64 characters
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))

        for node in self.store_nodes:
            store_response = self.get_store_messages_with_errors(node, hashes=non_base64_hash, page_size=50)

            assert "waku message hash parsing error: Incorrect base64 string" in store_response["error_message"], \
                f"Expected 'Incorrect base64 string' error, got {store_response['error_message']}"

    # Test when duplicate valid hashes are provided.
    def test_store_with_duplicate_hashes(self):
        message_hash_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))

        # Use the same hash twice
        duplicate_hash = f"{message_hash_list[0]},{message_hash_list[0]}"
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, hashes=duplicate_hash, page_size=50)
            assert len(store_response.messages) == 1, "Expected only one message for duplicate hashes"
            assert store_response.message_hash(0) == message_hash_list[0], "Incorrect message returned for duplicate hashes"
