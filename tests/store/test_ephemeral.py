import pytest
from src.libs.custom_logger import get_custom_logger
from src.libs.common import to_base64
from src.steps.store import StepsStore
from src.test_data import SAMPLE_INPUTS, VALID_PUBSUB_TOPICS

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("node_setup")
class TestEphemeral(StepsStore):
    def test_message_with_ephemeral_true(self):
        self.publish_message(message=self.create_message(ephemeral=True))
        self.check_store_returns_empty_response()

    def test_message_with_ephemeral_false(self):
        self.publish_message(message=self.create_message(ephemeral=False))
        self.check_published_message_is_stored(page_size=5, ascending="true")

    def test_message_with_both_ephemeral_true_and_false(self):
        self.publish_message(message=self.create_message(ephemeral=True))
        stored = self.publish_message(message=self.create_message(ephemeral=False))
        self.check_published_message_is_stored(page_size=5, ascending="true", message_to_check=stored)
        assert len(self.store_response["messages"]) == 1
        stored = self.publish_message(message=self.create_message(ephemeral=False))
        self.publish_message(message=self.create_message(ephemeral=True))
        self.check_published_message_is_stored(page_size=5, ascending="true", message_to_check=stored)
        assert len(self.store_response["messages"]) == 2
