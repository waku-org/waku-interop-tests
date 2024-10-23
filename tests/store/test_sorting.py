import pytest
from src.libs.common import to_base64
from src.steps.store import StepsStore
from src.libs.custom_logger import get_custom_logger

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("node_setup")
class TestSorting(StepsStore):
    @pytest.mark.parametrize("ascending", ["true", "false"])
    def test_store_sort_ascending(self, ascending):
        expected_message_hash_list = []
        for i in range(10):
            message = self.create_message(payload=to_base64(f"Message_{i}"))
            self.publish_message(message=message)
            expected_message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=5, ascending=ascending)
            response_message_hash_list = []
            for index in range(len(store_response.messages)):
                response_message_hash_list.append(store_response.message_hash(index))
            if ascending == "true":
                assert response_message_hash_list == expected_message_hash_list[:5], "Message hash mismatch for acending order"
            else:
                assert response_message_hash_list == expected_message_hash_list[5:], "Message hash mismatch for descending order"

    def test_store_invalid_ascending(self):
        expected_message_hash_list = []
        ascending = "##"
        for i in range(4):
            message = self.create_message(payload=to_base64(f"Message_{i}"))
            self.publish_message(message=message)
            expected_message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
            logger.debug(f"requesting stored messages with invalid ascending ={ascending}")
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, ascending=ascending, page_size=2)
            response_message_hash_list = []
            for index in range(len(store_response.messages)):
                response_message_hash_list.append(store_response.message_hash(index))
            assert response_message_hash_list == expected_message_hash_list[:2], "pages aren't forward as expected"
