import pytest
from src.libs.custom_logger import get_custom_logger
from src.steps.filter import StepsFilter

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("setup_main_relay_node", "setup_main_filter_node")
class TestFilterMultipleNodes(StepsFilter):
    def test_all_nodes_subscribed_to_the_topic(self):
        self.setup_optional_filter_nodes()
        self.wait_for_subscriptions_on_main_nodes([self.test_content_topic])
        self.subscribe_optional_filter_nodes([self.test_content_topic])
        self.check_published_message_reaches_filter_peer()

    def test_optional_nodes_not_subscribed_to_same_topic(self):
        self.setup_optional_filter_nodes()
        self.wait_for_subscriptions_on_main_nodes([self.test_content_topic])
        self.subscribe_optional_filter_nodes([self.second_content_topic])
        self.check_published_message_reaches_filter_peer(peer_list=self.main_nodes)
        self.check_publish_without_filter_subscription(peer_list=self.optional_nodes)
