import pytest
from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("setup_main_relay_nodes", "setup_optional_relay_nodes", "subscribe_main_relay_nodes")
class TestMultipleNodes(StepsRelay):
    def test_first_node_to_start_publishes(self):
        self.ensure_subscriptions_on_nodes(self.optional_nodes, [self.test_pubsub_topic])
        self.wait_for_published_message_to_reach_peer()

    def test_last_node_to_start_publishes(self):
        self.ensure_subscriptions_on_nodes(self.optional_nodes, [self.test_pubsub_topic])
        self.wait_for_published_message_to_reach_peer(sender=self.optional_nodes[-1])
