import pytest
from src.steps.store import StepsStore
from src.test_data import CONTENT_TOPICS_DIFFERENT_SHARDS


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
                    store_response["messages"][0]["messageHash"]["data"] == self.message_hash_list[index]
                ), "Incorrect messaged filtered based on content topic"

    def test_store_with_multiple_content_topics(self):
        for node in self.store_nodes:
            store_response = node.get_store_messages(
                content_topics=f"{CONTENT_TOPICS_DIFFERENT_SHARDS[0]},{CONTENT_TOPICS_DIFFERENT_SHARDS[4]}", page_size=20, ascending="true"
            )
            assert len(store_response["messages"]) == 2, "Message count mismatch"
            assert (
                store_response["messages"][0]["messageHash"]["data"] == self.message_hash_list[0]
            ), "Incorrect messaged filtered based on multiple content topics"
            assert (
                store_response["messages"][1]["messageHash"]["data"] == self.message_hash_list[4]
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
                    store_response["messages"][0]["messageHash"]["data"] == self.message_hash_list[index]
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
                    store_response["messages"][0]["messageHash"]["data"] == self.message_hash_list[index]
                ), "Incorrect messaged filtered based on content topic"

    def test_store_without_pubsub_topic_and_content_topic(self):
        for node in self.store_nodes:
            store_response = node.get_store_messages(page_size=20, ascending="true")
            assert len(store_response["messages"]) == len(CONTENT_TOPICS_DIFFERENT_SHARDS), "Message count mismatch"
