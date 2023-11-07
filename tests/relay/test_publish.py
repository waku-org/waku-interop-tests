import logging

from src.libs.common import to_base64
from src.data_classes import MessageRpcQuery
from src.steps.relay import StepsRelay
from src.test_data import SAMPLE_INPUTS

logger = logging.getLogger(__name__)


class TestRelayPublish(StepsRelay):
    def test_publish_with_various_payloads(self):
        failed_payloads = []
        for index, payload in enumerate(SAMPLE_INPUTS):
            logger.debug("Running test with payload %s", payload["description"])
            message = MessageRpcQuery(payload=to_base64(payload["value"]), contentTopic=self.test_content_topic)
            try:
                # The node may require a warmup period for message processing to stabilize.
                # Therefore, we use the retry function for the first payload to account for this warmup.
                if index == 0:
                    self.check_published_message_reaches_peer_with_retry(message)
                else:
                    self.check_published_message_reaches_peer(message)
            except Exception as e:
                logger.error("Payload %s failed: %s", payload["description"], str(e))
                failed_payloads.append(payload["description"])

        assert not failed_payloads, f"Payloads failed: {failed_payloads}"

    def test_publish_with_various_content_topics(self):
        failed_content_topics = []
        for index, content_topic in enumerate(SAMPLE_INPUTS):
            logger.debug("Running test with content topic %s", content_topic["description"])
            message = MessageRpcQuery(payload=to_base64(self.test_payload), contentTopic=content_topic["value"])
            try:
                # The node may require a warmup period for message processing to stabilize.
                # Therefore, we use the retry function for the first payload to account for this warmup.
                if index == 0:
                    self.check_published_message_reaches_peer_with_retry(message)
                else:
                    self.check_published_message_reaches_peer(message)
            except Exception as e:
                logger.error("ContentTopic %s failed: %s", {content_topic["description"]}, {str(e)})
                failed_content_topics.append(content_topic)
        assert not failed_content_topics, f"ContentTopics failed: {failed_content_topics}"
