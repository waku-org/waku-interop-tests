from src.libs.custom_logger import get_custom_logger
from time import time
from src.libs.common import to_base64
from src.steps.relay import StepsRelay
from src.test_data import INVALID_CONTENT_TOPICS, INVALID_PAYLOADS, SAMPLE_INPUTS, SAMPLE_TIMESTAMPS

logger = get_custom_logger(__name__)


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
                assert "Bad Request" in str(ex) or "Internal Server Error" in str(ex)
        assert not success_payloads, f"Invalid Payloads that didn't failed: {success_payloads}"

    def test_publish_with_missing_payload(self):
        message = {"contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        try:
            self.node1.send_message(message, self.test_pubsub_topic)
            raise AssertionError("Publish with missing payload worked!!!")
        except Exception as ex:
            assert "Bad Request" in str(ex) or "Internal Server Error" in str(ex)

    def test_publish_with_payload_less_than_one_mb(self):
        payload_length = 1024 * 1023
        logger.debug("Running test with payload length of %s bytes", payload_length)
        message = {"payload": to_base64("a" * (payload_length)), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        self.check_published_message_reaches_peer(message, message_propagation_delay=2)

    def test_publish_with_payload_equal_or_more_than_one_mb(self):
        payload_length = 1024 * 1023
        for payload_length in [1024 * 1024, 1024 * 1024 * 10]:
            logger.debug("Running test with payload length of %s bytes", payload_length)
            message = {"payload": to_base64("a" * (payload_length)), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
            try:
                self.check_published_message_reaches_peer(message, message_propagation_delay=2)
                raise AssertionError("Duplicate message was retrieved twice")
            except Exception as ex:
                assert "Peer node couldn't find any messages" in str(ex)

    def test_publish_with_valid_content_topics(self):
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
                assert "Bad Request" in str(ex) or "Internal Server Error" in str(ex)
        assert not success_content_topics, f"Invalid Content topics that didn't failed: {success_content_topics}"

    def test_publish_with_missing_content_topic(self):
        message = {"payload": to_base64(self.test_payload), "timestamp": int(time() * 1e9)}
        try:
            self.node1.send_message(message, self.test_pubsub_topic)
            raise AssertionError("Publish with missing content_topic worked!!!")
        except Exception as ex:
            assert "Bad Request" in str(ex) or "Internal Server Error" in str(ex)

    def test_publish_on_unsubscribed_pubsub_topic(self):
        try:
            self.check_published_message_reaches_peer(self.test_message, pubsub_topic="/waku/2/rs/19/1")
            raise AssertionError("Publish on unsubscribed pubsub_topic worked!!!")
        except Exception as ex:
            assert "Bad Request" in str(ex) or "Internal Server Error" in str(ex)

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

    def test_publish_with_valid_version(self):
        self.test_message["version"] = 10
        self.check_published_message_reaches_peer(self.test_message)

    def test_publish_with_invalid_version(self):
        self.test_message["version"] = 2.1
        try:
            self.check_published_message_reaches_peer(self.test_message)
            raise AssertionError("Publish with invalid version worked!!!")
        except Exception as ex:
            assert "Bad Request" in str(ex)

    def test_publish_with_valid_meta(self):
        self.test_message["meta"] = to_base64(self.test_payload)
        self.check_published_message_reaches_peer(self.test_message)

    def test_publish_with_invalid_meta(self):
        self.test_message["meta"] = self.test_payload
        try:
            self.check_published_message_reaches_peer(self.test_message)
            raise AssertionError("Publish with invalid meta worked!!!")
        except Exception as ex:
            assert "Bad Request" in str(ex)

    def test_publish_with_rate_limit_proof(self):
        self.test_message["rateLimitProof"] = {
            "proof": to_base64("proofData"),
            "epoch": to_base64("epochData"),
            "nullifier": to_base64("nullifierData"),
        }
        self.check_published_message_reaches_peer(self.test_message)

    def test_publish_with_ephemeral(self):
        failed_ephemeral = []
        for ephemeral in [True, False]:
            logger.debug("Running test with Ephemeral %s", ephemeral)
            self.test_message["ephemeral"] = ephemeral
            try:
                self.check_published_message_reaches_peer(self.test_message)
            except Exception as e:
                logger.error("Massage with Ephemeral %s failed: %s", ephemeral, str(e))
                failed_ephemeral.append(ephemeral)
        assert not failed_ephemeral, f"Ephemeral that failed: {failed_ephemeral}"

    def test_publish_and_retrieve_duplicate_message(self):
        self.check_published_message_reaches_peer(self.test_message)
        try:
            self.check_published_message_reaches_peer(self.test_message)
            raise AssertionError("Duplicate message was retrieved twice")
        except Exception as ex:
            assert "Peer node couldn't find any messages" in str(ex)
