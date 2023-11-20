from time import sleep
import pytest
from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("setup_main_relay_nodes", "setup_optional_relay_nodes", "subscribe_main_relay_nodes")
class TestMultipleNodes(StepsRelay):
    def test_first_node_to_start_publishes(self, subscribe_optional_relay_nodes, relay_warm_up):
        self.check_published_message_reaches_peer(self.create_message())

    def test_last_node_to_start_publishes(self, subscribe_optional_relay_nodes, relay_warm_up):
        self.check_published_message_reaches_peer(self.create_message(), sender=self.optional_nodes[-1])

    def test_optional_nodes_not_subscribed_to_same_pubsub_topic(self):
        self.wait_for_published_message_to_reach_peer(peer_list=self.main_nodes)
        try:
            self.check_published_message_reaches_peer(self.create_message(), peer_list=self.optional_nodes)
            raise AssertionError("Non subscribed nodes received the message!!")
        except Exception as ex:
            assert "Not Found" in str(ex), "Expected 404 Not Found when the message is not found"
