import pytest
from src.libs.custom_logger import get_custom_logger
from src.libs.common import to_base64
from src.steps.store import StepsStore
from src.test_data import SAMPLE_INPUTS

logger = get_custom_logger(__name__)

#  TO DO test without pubsubtopic freezes


class TestGetMessages(StepsStore):
    @pytest.fixture(scope="function", autouse=True)
    def store_functional_setup(self, store_setup):
        self.setup_first_publishing_node(store="true", relay="true")
        self.setup_first_store_node(store="true", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()

    def test_store_messages_with_valid_payloads(self):
        failed_payloads = []
        for payload in SAMPLE_INPUTS:
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                self.publish_message_via("relay", message=message)
                self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=50, ascending="true")
            except Exception as e:
                logger.error(f'Payload {payload["description"]} failed: {str(e)}')
                failed_payloads.append(payload["description"])
        assert not failed_payloads, f"Payloads failed: {failed_payloads}"
