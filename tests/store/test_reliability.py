import pytest
from src.libs.custom_logger import get_custom_logger
from src.libs.common import delay
from src.steps.store import StepsStore

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("node_setup")
class TestReliability(StepsStore):
    def test_publishing_node_is_stopped(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        self.publishing_node1.stop()
        store_response = self.store_node1.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending="true", store_v="v3")
        assert len(store_response["messages"]) == 1

    def test_publishing_node_restarts(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        self.publishing_node1.restart()
        self.publishing_node1.ensure_ready()
        self.add_node_peer(self.store_node1, self.multiaddr_list)
        self.subscribe_to_pubsub_topics_via_relay(node=self.publishing_node1)
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending="true", store_v="v3")
            assert len(store_response["messages"]) == 2

    def test_store_node_restarts(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        self.store_node1.restart()
        self.store_node1.ensure_ready()
        self.subscribe_to_pubsub_topics_via_relay(node=self.store_node1)
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending="true", store_v="v3")
            assert len(store_response["messages"]) == 2

    def test_publishing_node_paused_and_unpaused(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        self.publishing_node1.pause()
        delay(1)
        self.publishing_node1.unpause()
        self.publishing_node1.ensure_ready()
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending="true", store_v="v3")
            assert len(store_response["messages"]) == 2

    def test_store_node_paused_and_unpaused(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        self.store_node1.pause()
        delay(1)
        self.store_node1.unpause()
        self.store_node1.ensure_ready()
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending="true", store_v="v3")
            assert len(store_response["messages"]) == 2

    def test_message_relayed_while_store_node_is_paused(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        self.store_node1.pause()
        self.publish_message()
        self.store_node1.unpause()
        self.store_node1.ensure_ready()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending="true", store_v="v3")
            assert len(store_response["messages"]) == 2

    def test_message_relayed_while_store_node_is_stopped(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        self.store_node1.stop()
        self.publish_message()
        self.store_node1.start()
        self.store_node1.ensure_ready()
        self.add_node_peer(self.store_node1, self.multiaddr_list)
        self.subscribe_to_pubsub_topics_via_relay(node=self.store_node1)
        delay(1)
        for node in self.store_nodes:
            store_response = node.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending="true", store_v="v3")
            assert len(store_response["messages"]) == 2

    def test_message_relayed_before_store_node_is_started(self):
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
        self.setup_second_store_node(store="true", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        store_response = self.store_node2.get_store_messages(pubsub_topic=self.test_pubsub_topic, page_size=5, ascending="true", store_v="v3")
        assert len(store_response["messages"]) == 0
        self.publish_message()
        self.check_published_message_is_stored(page_size=5, ascending="true")
