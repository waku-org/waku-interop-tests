import pytest
from src.steps.relay import StepsRelay


@pytest.mark.usefixtures("setup_main_relay_nodes", "setup_optional_relay_nodes", "subscribe_main_relay_nodes")
class TestRelayMultipleNodes(StepsRelay):
    def test_first_node_to_start_publishes(self, subscribe_optional_relay_nodes, relay_warm_up):
        self.check_published_message_reaches_relay_peer()

    def test_last_node_to_start_publishes(self, subscribe_optional_relay_nodes, relay_warm_up):
        self.check_published_message_reaches_relay_peer(sender=self.optional_nodes[-1])

    def test_optional_nodes_not_subscribed_to_same_pubsub_topic(self):
        self.wait_for_published_message_to_reach_relay_peer(peer_list=self.main_nodes)
        try:
            self.check_published_message_reaches_relay_peer(peer_list=self.optional_nodes)
            raise AssertionError("Non subscribed nodes received the message!!")
        except Exception as ex:
            assert "Not Found" in str(ex), "Expected 404 Not Found when the message is not found"

    def test_relay_get_message_while_one_peer_is_paused(self, subscribe_optional_relay_nodes, relay_warm_up):
        self.check_published_message_reaches_relay_peer()
        relay_message1 = self.create_message(contentTopic=self.test_content_topic)
        relay_message2 = self.create_message(contentTopic=self.test_content_topic)
        self.node2.pause()
        self.node1.send_relay_message(relay_message1, self.test_pubsub_topic)
        self.node2.unpause()
        self.node1.send_relay_message(relay_message2, self.test_pubsub_topic)
        messages = self.node2.get_relay_messages(self.test_pubsub_topic)
        assert len(messages) == 2, "Both messages should've been returned"

    def test_relay_get_message_after_one_peer_was_stopped(self, subscribe_optional_relay_nodes, relay_warm_up):
        self.check_published_message_reaches_relay_peer(peer_list=self.main_nodes + self.optional_nodes)
        self.node2.stop()
        self.wait_for_published_message_to_reach_relay_peer(peer_list=self.optional_nodes)
