import pytest
from src.env_vars import NODE_2
from src.libs.custom_logger import get_custom_logger
from src.steps.store import StepsStore

logger = get_custom_logger(__name__)

# test without pubsubtopic freezes


class TestRunningNodes(StepsStore):
    def test_main_node_relay_and_store__peer_relay_and_store(self):
        self.setup_first_publishing_node(store="true", relay="true")
        self.setup_first_store_node(store="true", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        self.check_published_message_is_stored(
            contentTopics=self.test_content_topic, pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true", store_v="v1"
        )

    @pytest.mark.xfail("nwaku" in NODE_2, reason="Bug reported: https://github.com/waku-org/nwaku/issues/2586")
    def test_main_node_relay_and_store__peer_only_store(self):
        self.setup_first_publishing_node(store="true", relay="true")
        self.setup_first_store_node(store="true", relay="false")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        self.check_published_message_is_stored(
            contentTopics=self.test_content_topic, pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true", store_v="v1"
        )

    @pytest.mark.xfail("go-waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1087")
    def test_main_node_only_relay__peer_relay_and_store(self):
        self.setup_first_publishing_node(store="false", relay="true")
        self.setup_first_store_node(store="true", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        self.store_node1.get_relay_messages(self.test_pubsub_topic)
        self.check_published_message_is_stored(
            contentTopics=self.test_content_topic, pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true", store_v="v1"
        )
