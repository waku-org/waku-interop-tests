import pytest
from src.libs.common import to_base64
from src.steps.store import StepsStore


@pytest.mark.usefixtures("node_setup")
class TestPageSize(StepsStore):
    def test_default_page_size(self):
        for i in range(30):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node)
            assert len(store_response.messages) == 20, "Message count mismatch"

    def test_page_size_0_defaults_to_20(self):
        for i in range(30):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=0)
            assert len(store_response.messages) == 20, "Message count mismatch"

    def test_max_page_size(self):
        for i in range(200):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=200)
            assert len(store_response.messages) == 100, "Message count mismatch"

    @pytest.mark.parametrize("page_size", [1, 11, 39, 81, 99])
    def test_different_page_size(self, page_size):
        for i in range(page_size + 1):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=page_size)
            assert len(store_response.messages) == page_size, "Message count mismatch"
