import pytest
from src.libs.custom_logger import get_custom_logger
from src.libs.common import to_base64
from src.steps.store import StepsStore
from src.test_data import SAMPLE_INPUTS, VALID_PUBSUB_TOPICS

logger = get_custom_logger(__name__)

# TO DO test without pubsubtopic freezes


@pytest.mark.usefixtures("node_setup")
class TestGetMessages(StepsStore):
    # only one test for store v1, all other tests are using the new store v3
    def test_legacy_store_v1(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true", store_v="v1")

    def test_get_store_messages_with_different_payloads(self):
        failed_payloads = []
        for payload in SAMPLE_INPUTS:
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                self.publish_message(message=message)
                self.check_published_message_is_stored(page_size=50, ascending="true")
            except Exception as e:
                logger.error(f'Payload {payload["description"]} failed: {str(e)}')
                failed_payloads.append(payload["description"])
        assert not failed_payloads, f"Payloads failed: {failed_payloads}"
        assert len(self.store_response["messages"]) == len(SAMPLE_INPUTS)

    def test_get_store_messages_with_different_content_topics(self):
        failed_content_topics = []
        for content_topic in SAMPLE_INPUTS:
            logger.debug(f'Running test with content topic {content_topic["description"]}')
            message = self.create_message(contentTopic=content_topic["value"])
            try:
                self.publish_message(message=message)
                self.check_published_message_is_stored(page_size=50, ascending="true")
            except Exception as e:
                logger.error(f'ContentTopic {content_topic["description"]} failed: {str(e)}')
                failed_content_topics.append(content_topic)
        assert not failed_content_topics, f"ContentTopics failed: {failed_content_topics}"
        assert len(self.store_response["messages"]) == len(SAMPLE_INPUTS)

    def test_get_store_messages_with_different_pubsub_topics(self):
        self.subscribe_to_pubsub_topics_via_relay(pubsub_topics=VALID_PUBSUB_TOPICS)
        failed_pubsub_topics = []
        for pubsub_topic in VALID_PUBSUB_TOPICS:
            logger.debug(f"Running test with pubsub topic {pubsub_topic}")
            try:
                self.publish_message(pubsub_topic=pubsub_topic)
                self.check_published_message_is_stored(pubsub_topic=pubsub_topic, page_size=50, ascending="true")
            except Exception as e:
                logger.error(f"PubsubTopic pubsub_topic failed: {str(e)}")
                failed_pubsub_topics.append(pubsub_topic)
        assert not failed_pubsub_topics, f"PubsubTopics failed: {failed_pubsub_topics}"

    def test_get_store_message_with_meta(self):
        message = self.create_message(meta=to_base64(self.test_payload))
        self.publish_message(message=message)
        self.check_published_message_is_stored(page_size=5, ascending="true")

    def test_get_store_message_with_version(self):
        message = self.create_message(version=10)
        self.publish_message(message=message)
        self.check_published_message_is_stored(page_size=5, ascending="true")

    def test_get_store_duplicate_messages(self):
        message = self.create_message()
        self.publish_message(message=message)
        self.publish_message(message=message)
        self.check_published_message_is_stored(page_size=5, ascending="true")
        # only one message is stored
        assert len(self.store_response["messages"]) == 1

    def test_get_multiple_store_messages(self):
        message_hash_list = []
        for payload in SAMPLE_INPUTS:
            message = self.create_message(payload=to_base64(payload["value"]))
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=50, ascending="true")
            assert len(store_response["messages"]) == len(SAMPLE_INPUTS)
            for index, message_hash in enumerate(store_response["messages"]):
                assert message_hash["messageHash"]["data"] == message_hash_list[index], f"Message hash at index {index} doesn't match"
