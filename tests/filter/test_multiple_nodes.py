import pytest
from src.env_vars import NODE_1
from src.libs.common import delay
from src.libs.custom_logger import get_custom_logger
from src.steps.filter import StepsFilter

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("setup_main_relay_node", "setup_main_filter_node")
class TestFilterMultipleNodes(StepsFilter):
    def test_all_nodes_subscribed_to_the_topic(self):
        self.setup_optional_filter_nodes()
        self.wait_for_subscriptions_on_main_nodes([self.test_content_topic])
        self.subscribe_optional_filter_nodes([self.test_content_topic])
        self.wait_for_published_message_to_reach_filter_peer()

    def test_optional_nodes_not_subscribed_to_same_topic(self):
        self.setup_optional_filter_nodes()
        self.wait_for_subscriptions_on_main_nodes([self.test_content_topic])
        self.subscribe_optional_filter_nodes([self.second_content_topic])
        self.check_published_message_reaches_filter_peer(peer_list=self.main_nodes)
        self.check_publish_without_filter_subscription(peer_list=self.optional_nodes)

    @pytest.mark.xfail("nwaku" in NODE_1, reason="Bug reported: https://github.com/waku-org/nwaku/issues/2319")
    def test_filter_get_message_while_one_peer_is_paused(self):
        self.setup_optional_filter_nodes()
        self.wait_for_subscriptions_on_main_nodes([self.test_content_topic])
        self.subscribe_optional_filter_nodes([self.test_content_topic])
        self.check_published_message_reaches_filter_peer()
        relay_message1 = self.create_message(contentTopic=self.test_content_topic)
        relay_message2 = self.create_message(contentTopic=self.test_content_topic)
        self.node2.pause()
        self.node1.send_relay_message(relay_message1, self.test_pubsub_topic)
        self.node2.unpause()
        self.node1.send_relay_message(relay_message2, self.test_pubsub_topic)
        delay(0.5)
        filter_messages = self.get_filter_messages(content_topic=self.test_content_topic, pubsub_topic=self.test_pubsub_topic, node=self.node2)
        assert len(filter_messages) == 2, "Both messages should've been returned"

    @pytest.mark.xfail("nwaku" in NODE_1, reason="Bug reported: https://github.com/waku-org/nwaku/issues/2319")
    def test_filter_get_message_after_one_peer_was_stopped(self):
        self.setup_optional_filter_nodes()
        self.wait_for_subscriptions_on_main_nodes([self.test_content_topic])
        self.subscribe_optional_filter_nodes([self.test_content_topic])
        self.check_published_message_reaches_filter_peer(peer_list=self.main_nodes + self.optional_nodes)
        self.node2.stop()
        self.check_published_message_reaches_filter_peer(peer_list=self.optional_nodes)

    def test_ping_only_some_nodes_have_subscriptions(self):
        self.wait_for_subscriptions_on_main_nodes([self.test_content_topic])
        self.setup_optional_filter_nodes()
        self.ping_filter_subscriptions("1", node=self.node2)
        for node in self.optional_nodes:
            self.ping_without_filter_subscription(node=node)
