import pytest
from src.env_vars import NODE_2
from src.libs.custom_logger import get_custom_logger
from time import time
from src.libs.common import delay, to_base64

from src.steps.store import StepsStore
from src.test_data import INVALID_CONTENT_TOPICS, INVALID_PAYLOADS, PUBSUB_TOPICS_WRONG_FORMAT, SAMPLE_INPUTS, SAMPLE_TIMESTAMPS, VALID_PUBSUB_TOPICS

logger = get_custom_logger(__name__)


class TestStore(StepsStore):
    @pytest.fixture(scope="function", autouse=True)
    def store_functional_setup(self, store_setup):
        self.setup_first_publishing_node()
        self.setup_first_store_node()
        self.subscribe_to_pubsub_topics_via_relay()

    def test_aaaaaa(self):
        self.publish_message_via("relay")
        self.check_published_message_is_stored(
            contentTopics=self.test_content_topic, pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true", store_v="v1"
        )
        self.check_published_message_is_stored(peerAddr=self.multiaddr_list[0], pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")
        self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")

    # def test_light_push_with_valid_payloads(self):
    #     failed_payloads = []
    #     for payload in SAMPLE_INPUTS:
    #         logger.debug(f'Running test with payload {payload["description"]}')
    #         message = self.create_message(payload=to_base64(payload["value"]))
    #         try:
    #             self.check_published_message_is_stored_by_store_peer(message=message)
    #         except Exception as e:
    #             logger.error(f'Payload {payload["description"]} failed: {str(e)}')
    #             failed_payloads.append(payload["description"])
    #     assert not failed_payloads, f"Payloads failed: {failed_payloads}"
