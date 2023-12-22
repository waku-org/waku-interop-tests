import pytest
from src.libs.common import delay
from src.env_vars import DEFAULT_NWAKU
from src.libs.custom_logger import get_custom_logger
from src.steps.filter import StepsFilter
from src.steps.metrics import StepsMetrics

logger = get_custom_logger(__name__)


@pytest.mark.skip(reason="Skipping until https://github.com/waku-org/nwaku/issues/2293 is fixed")
class TestIdleSubscriptions(StepsFilter, StepsMetrics):
    # tests will probably suffer minor adjustments after https://github.com/waku-org/nwaku/issues/2293 is fixed

    @pytest.mark.timeout(60 * 10)
    def test_idle_filter_subscriptions_for_more_than_5_nodes(self):
        self.relay_node_start(DEFAULT_NWAKU)
        filter_node_list = f"{DEFAULT_NWAKU}," * 6
        self.setup_optional_filter_nodes(filter_node_list)
        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.subscribe_optional_filter_nodes([self.test_content_topic])
        self.check_published_message_reaches_filter_peer(peer_list=self.optional_nodes)
        self.wait_for_metric(self.node1, "waku_filter_subscriptions", 6.0)
        delay(60 * 5)  # not sure how many seconds to put here so hardcoded 5 minutes to be sure
        # after some idle time nodes should disconnect and we should see max 5 connections
        self.wait_for_metric(self.node1, "waku_filter_subscriptions", 5.0)

    @pytest.mark.timeout(60 * 10)
    def test_idle_filter_subscriptions_after_node_disconnection(self):
        self.relay_node_start(DEFAULT_NWAKU)
        self.setup_optional_filter_nodes(DEFAULT_NWAKU)
        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.subscribe_optional_filter_nodes([self.test_content_topic])
        self.check_published_message_reaches_filter_peer(peer_list=self.optional_nodes)
        self.wait_for_metric(self.node1, "waku_filter_subscriptions", 1.0)
        self.optional_nodes[0].stop()
        delay(60 * 5)  # not sure how many seconds to put here so hardcoded 5 minutes to be sure
        # after some idle time the stopped node should disconnect and we should see 0 connections
        self.wait_for_metric(self.node1, "waku_filter_subscriptions", 0.0)
