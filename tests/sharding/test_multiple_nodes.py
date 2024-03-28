import pytest
from src.env_vars import NODE_2
from src.libs.custom_logger import get_custom_logger
from src.steps.sharding import StepsSharding

logger = get_custom_logger(__name__)


class TestMultipleNodes(StepsSharding):
    def test_static_shard_relay(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        self.setup_optional_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        self.subscribe_main_relay_nodes(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_optional_relay_nodes(pubsub_topics=[self.test_pubsub_topic])
        self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
