import pytest
from src.libs.common import to_base64
from src.steps.store import StepsStore


@pytest.mark.usefixtures("node_setup")
class TestCursor(StepsStore):
    def test_get_multiple_2000_store_messages(self):
        for i in range(110):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")), message_propagation_delay=0.001)
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsubTopic=self.test_pubsub_topic, page_size=50, ascending="true", store_v="v3")
            print(len(store_response["messages"]))
