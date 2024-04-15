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
        self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")

    def test_main_node_relay_and_store__peer_only_store(self):
        self.setup_first_publishing_node(store="true", relay="true")
        self.setup_first_store_node(store="true", relay="false")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        if self.store_node1.is_gowaku():
            self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")
        elif self.store_node1.is_nwaku():
            self.check_store_returns_empty_response()

    def test_main_node_relay_and_store__peer_only_relay(self):
        self.setup_first_publishing_node(store="true", relay="true")
        self.setup_first_store_node(store="false", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")

    def test_main_node_relay_and_store__peer_neither_relay_nor_store(self):
        self.setup_first_publishing_node(store="true", relay="true")
        self.setup_first_store_node(store="false", relay="false")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")

    @pytest.mark.xfail("go-waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1087")
    def test_main_node_only_relay__peer_relay_and_store(self):
        self.setup_first_publishing_node(store="false", relay="true")
        self.setup_first_store_node(store="true", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")

    def test_main_node_only_relay__peer_only_store(self):
        self.setup_first_publishing_node(store="false", relay="true")
        self.setup_first_store_node(store="true", relay="false")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        if self.store_node1.is_gowaku():
            try:
                self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")
            except Exception as ex:
                assert "failed to negotiate protocol: protocols not supported" in str(ex)
        elif self.store_node1.is_nwaku():
            self.check_store_returns_empty_response()

    def test_main_node_only_relay__peer_only_relay(self):
        self.setup_first_publishing_node(store="false", relay="true")
        self.setup_first_store_node(store="false", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("relay")
        try:
            self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")
        except Exception as ex:
            assert "failed to negotiate protocol: protocols not supported" in str(ex) or "PEER_DIAL_FAILURE" in str(ex)

    def test_main_node_lightpush_and_store__peer_relay_and_store(self):
        self.setup_first_publishing_node(store="true", relay="false", lightpush="true")
        self.setup_first_store_node(store="true", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.publish_message_via("lightpush")
        self.check_published_message_is_stored(pubsubTopic=self.test_pubsub_topic, pageSize=5, ascending="true")
