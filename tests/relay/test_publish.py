import logging
from time import time
from src.libs.common import to_base64
from src.steps.relay import StepsRelay
from src.test_data import INVALID_CONTENT_TOPICS, INVALID_PAYLOADS, SAMPLE_INPUTS, SAMPLE_TIMESTAMPS

logger = logging.getLogger(__name__)


class TestRelayPublish(StepsRelay):
    def test_publish_with_valid_payloads(self):
        failed_payloads = []
        for payload in SAMPLE_INPUTS:
            logger.debug("Running test with payload %s", payload["description"])
            message = {"payload": to_base64(payload["value"]), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
            try:
                self.check_published_message_reaches_peer(message)
            except Exception as e:
                logger.error("Payload %s failed: %s", payload["description"], str(e))
                failed_payloads.append(payload["description"])
        assert not failed_payloads, f"Payloads failed: {failed_payloads}"

    def test_publish_with_invalid_payloads(self):
        success_payloads = []
        for payload in INVALID_PAYLOADS:
            logger.debug("Running test with payload %s", payload["description"])
            message = {"payload": payload["value"], "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
            try:
                self.node1.send_message(message, self.test_pubsub_topic)
                success_payloads.append(payload)
            except Exception as ex:
                assert "Bad Request" in str(ex)
        assert not success_payloads, f"Invalid Payloads that didn't failed: {success_payloads}"

    def test_publish_with_missing_payload(self):
        message = {"contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        try:
            self.node1.send_message(message, self.test_pubsub_topic)
            raise AssertionError("Publish with missing payload worked!!!")
        except Exception as ex:
            if self.node1.is_nwaku():
                assert "Bad Request" in str(ex)
            elif self.node1.is_gowaku():
                assert "Internal Server Error" in str(ex)
            else:
                raise Exception("Not implemented")

    def test_publish_with_various_content_topics(self):
        failed_content_topics = []
        for content_topic in SAMPLE_INPUTS:
            logger.debug("Running test with content topic %s", content_topic["description"])
            message = {"payload": to_base64(self.test_payload), "contentTopic": content_topic["value"], "timestamp": int(time() * 1e9)}
            try:
                self.check_published_message_reaches_peer(message)
            except Exception as e:
                logger.error("ContentTopic %s failed: %s", content_topic["description"], str(e))
                failed_content_topics.append(content_topic)
        assert not failed_content_topics, f"ContentTopics failed: {failed_content_topics}"

    def test_publish_with_invalid_content_topics(self):
        success_content_topics = []
        for content_topic in INVALID_CONTENT_TOPICS:
            logger.debug("Running test with contetn topic %s", content_topic["description"])
            message = {"payload": to_base64(self.test_payload), "contentTopic": content_topic["value"], "timestamp": int(time() * 1e9)}
            try:
                self.node1.send_message(message, self.test_pubsub_topic)
                success_content_topics.append(content_topic)
            except Exception as ex:
                assert "Bad Request" in str(ex)
        assert not success_content_topics, f"Invalid Content topics that didn't failed: {success_content_topics}"

    def test_publish_with_missing_content_topic(self):
        message = {"payload": to_base64(self.test_payload), "timestamp": int(time() * 1e9)}
        try:
            self.node1.send_message(message, self.test_pubsub_topic)
            raise AssertionError("Publish with missing content_topic worked!!!")
        except Exception as ex:
            if self.node1.is_nwaku():
                assert "Bad Request" in str(ex)
            elif self.node1.is_gowaku():
                assert "Internal Server Error" in str(ex)
            else:
                raise Exception("Not implemented")

    def test_publish_with_valid_timestamps(self):
        failed_timestamps = []
        for timestamp in SAMPLE_TIMESTAMPS:
            if self.node1.type() in timestamp["valid_for"]:
                logger.debug("Running test with timestamp %s", timestamp["description"])
                message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": timestamp["value"]}
                try:
                    self.check_published_message_reaches_peer(message)
                except Exception as ex:
                    logger.error("Timestamp %s failed: %s", timestamp["description"], str(ex))
                    failed_timestamps.append(timestamp)
        assert not failed_timestamps, f"Timestamps failed: {failed_timestamps}"

    def test_publish_with_invalid_timestamps(self):
        success_timestamps = []
        for timestamp in SAMPLE_TIMESTAMPS:
            if self.node1.type() not in timestamp["valid_for"]:
                logger.debug("Running test with timestamp %s", timestamp["description"])
                message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": timestamp["value"]}
                try:
                    self.check_published_message_reaches_peer(message)
                    success_timestamps.append(timestamp)
                except Exception as e:
                    pass
        assert not success_timestamps, f"Invalid Timestamps that didn't failed: {success_timestamps}"

    def test_publish_with_no_timestamp(self):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic}
        self.check_published_message_reaches_peer(message)
