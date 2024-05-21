import pytest
from src.libs.common import to_base64
from src.steps.store import StepsStore


@pytest.mark.usefixtures("node_setup")
class TestSorting(StepsStore):
    @pytest.mark.parametrize("ascending", ["true", "false"])
    def test_store_sort_ascending(self, ascending):
        expected_message_hash_list = []
        for i in range(10):
            message = self.create_message(payload=to_base64(f"Message_{i}"))
            self.publish_message(message=message, message_propagation_delay=0.01)
            expected_message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending=ascending)
            response_message_hash_list = []
            for message in store_response["messages"]:
                response_message_hash_list.append(message["messageHash"]["data"])
            if ascending == "true":
                assert response_message_hash_list == expected_message_hash_list[:5], "Message hash mismatch for acending order"
            else:
                assert response_message_hash_list == expected_message_hash_list[5:], "Message hash mismatch for descending order"
