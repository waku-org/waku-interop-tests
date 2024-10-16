import pytest
from src.env_vars import NODE_2
from src.steps.store import StepsStore
from src.test_data import CONTENT_TOPICS_DIFFERENT_SHARDS
from src.libs.custom_logger import get_custom_logger

logger = get_custom_logger(__name__)


@pytest.mark.xfail("go-waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1108")
class TestTopics(StepsStore):
    @pytest.fixture(scope="function", autouse=True)
    def topics_setup(self, node_setup):
        self.message_hash_list = []
        for content_topic in CONTENT_TOPICS_DIFFERENT_SHARDS:
            message = self.create_message(contentTopic=content_topic)
            self.publish_message(message=message)
            self.message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))

    def test_store_with_one_content_topic(self):
        for node in self.store_nodes:
            for index, content_topic in enumerate(CONTENT_TOPICS_DIFFERENT_SHARDS):
                store_response = node.get_store_messages(content_topics=content_topic, page_size=20, ascending="true")
                assert len(store_response["messages"]) == 1, "Message count mismatch"
                assert (
                    store_response["messages"][0]["messageHash"] == self.message_hash_list[index]
                ), "Incorrect messaged filtered based on content topic"

    def test_store_with_multiple_content_topics(self):
        for node in self.store_nodes:
            store_response = node.get_store_messages(
                content_topics=f"{CONTENT_TOPICS_DIFFERENT_SHARDS[0]},{CONTENT_TOPICS_DIFFERENT_SHARDS[4]}", page_size=20, ascending="true"
            )
            assert len(store_response["messages"]) == 2, "Message count mismatch"
            assert (
                store_response["messages"][0]["messageHash"] == self.message_hash_list[0]
            ), "Incorrect messaged filtered based on multiple content topics"
            assert (
                store_response["messages"][1]["messageHash"] == self.message_hash_list[4]
            ), "Incorrect messaged filtered based on multiple content topics"

    def test_store_with_unknown_content_topic(self):
        for node in self.store_nodes:
            store_response = node.get_store_messages(content_topics="test", page_size=20, ascending="true")
            assert len(store_response["messages"]) == 0, "Message count mismatch"

    def test_store_with_unknown_pubsub_topic(self):
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic="test", page_size=20, ascending="true")
            assert len(store_response["messages"]) == 0, "Message count mismatch"

    def test_store_with_both_pubsub_topic_and_content_topic(self):
        for node in self.store_nodes:
            for index, content_topic in enumerate(CONTENT_TOPICS_DIFFERENT_SHARDS):
                store_response = node.get_store_messages(
                    pubsub_topic=self.test_pubsub_topic, content_topics=content_topic, page_size=20, ascending="true"
                )
                assert len(store_response["messages"]) == 1, "Message count mismatch"
                assert (
                    store_response["messages"][0]["messageHash"] == self.message_hash_list[index]
                ), "Incorrect messaged filtered based on content topic"

    def test_store_with_unknown_pubsub_topic_but_known_content_topic(self):
        for node in self.store_nodes:
            store_response = node.get_store_messages(
                pubsub_topic="test", content_topics=CONTENT_TOPICS_DIFFERENT_SHARDS[0], page_size=20, ascending="true"
            )
            assert len(store_response["messages"]) == 0, "Message count mismatch"

    def test_store_with_both_pubsub_topic_and_content_topic(self):
        for node in self.store_nodes:
            for index, content_topic in enumerate(CONTENT_TOPICS_DIFFERENT_SHARDS):
                store_response = node.get_store_messages(
                    pubsub_topic=self.test_pubsub_topic, content_topics=content_topic, page_size=20, ascending="true"
                )
                assert len(store_response["messages"]) == 1, "Message count mismatch"
                assert (
                    store_response["messages"][0]["messageHash"] == self.message_hash_list[index]
                ), "Incorrect messaged filtered based on content topic"

    def test_store_without_pubsub_topic_and_content_topic(self):
        for node in self.store_nodes:
            store_response = node.get_store_messages(page_size=20, ascending="true")
            assert len(store_response["messages"]) == len(CONTENT_TOPICS_DIFFERENT_SHARDS), "Message count mismatch"

    def test_store_with_not_valid_content_topic(self):
        empty_content_topic = ""
        for node in self.store_nodes:
            store_response = node.get_store_messages(page_size=20, include_data="true", ascending="true", content_topics=empty_content_topic)
            assert len(store_response["messages"]) == len(CONTENT_TOPICS_DIFFERENT_SHARDS), "Message count mismatch"
        # test with space string content topic
        space_content_topic = " "
        try:
            store_response = self.store_nodes[0].get_store_messages(
                page_size=20, include_data="true", ascending="true", content_topics=space_content_topic
            )
            logger.debug(f" response for empty content_topic {store_response}")
            assert store_response["messages"] == [], "message stored with wrong topic "
        except Exception as e:
            raise Exception("couldn't get stored message")
        # test with wrong url
        wrong_content_topic = "myapp/1/latest/proto"
        try:
            store_response = self.store_nodes[0].get_store_messages(
                page_size=20, include_data="true", ascending="true", content_topics=wrong_content_topic
            )
            logger.debug(f" response for wrong url content topic is {store_response}")
            assert store_response["messages"] == [], "message stored with wrong topic "
        except Exception as e:
            raise Exception("couldn't get stored message")
