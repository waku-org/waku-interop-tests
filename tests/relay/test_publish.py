import logging
from time import sleep

from src.libs.common import to_base64
from src.data_classes import MessageRpcQuery
from src.steps.relay import StepsRelay
from src.test_data import SAMPLE_INPUTS

logger = logging.getLogger(__name__)


class TestRelayPublish(StepsRelay):
    def test_publish_with_various_payloads(self):
        failed_payloads = []
        for payload in SAMPLE_INPUTS:
            logger.debug("Running test with payload %s", payload["description"])
            message = MessageRpcQuery(payload=to_base64(payload["value"]), contentTopic=self.default_content_topic)
            try:
                self.check_published_message_reaches_peer(message)
            except Exception as e:
                logger.error(f"Payload '{payload['description']}' failed: {str(e)}")
                failed_payloads.append(payload)
        assert not failed_payloads, f"Payloads failed: {failed_payloads}"

    def test_publish_with_various_content_topics(self):
        failed_content_topics = []
        for content_topic in SAMPLE_INPUTS:
            logger.debug("Running test with content topic %s", content_topic["description"])
            message = MessageRpcQuery(payload=to_base64(self.default_payload), contentTopic=content_topic["value"])
            try:
                self.check_published_message_reaches_peer(message)
            except Exception as e:
                logger.error(f"ContentTopic '{content_topic['description']}' failed: {str(e)}")
                failed_content_topics.append(content_topic)
        assert not failed_content_topics, f"ContentTopics failed: {failed_content_topics}"

    # while True:
    #     message = MessageRpcQuery(
    #         payload="TTE=",
    #         contentTopic="/test/1/waku-filter",
    #         timestamp=int(time() * 1e9)
    #     )
    #     node1.send_message(message)
    #     sleep(1)
    #     # print(node1.get_messages())
    #     print(node2.get_messages())

    # node1.stop()
    # node2.stop()

    # info = node1.info()
    # enr_uri = node1.info()["result"]
