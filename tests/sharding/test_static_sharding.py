from time import sleep
import pytest
from src.env_vars import NODE_2
from src.libs.common import delay
from src.libs.custom_logger import get_custom_logger
from src.steps.sharding import StepsSharding

logger = get_custom_logger(__name__)

"""
VIA API
VIA FLAGS like pubsub topic and content topic
FILTER
RELAY
RUNNING NODES:
    - running on all kind of cluster
    - nodes on same cluster connect
    - nodes on different clusters do not connect
MULTIPLE NDES
"""

PUBSUB_TOPICS_DIFFERENT_CLUSTERS = [
    "/waku/2/rs/0/0",
    "/waku/2/rs/0/1",
    "/waku/2/rs/2/0",
    "/waku/2/rs/2/1",
    "/waku/2/rs/2/999",
    "/waku/2/rs/8/0",
    "/waku/2/rs/999/999",
]
PUBSUB_TOPICS_SAME_CLUSTER = [
    "/waku/2/rs/2/0",
    "/waku/2/rs/2/1",
    "/waku/2/rs/2/2",
    "/waku/2/rs/2/3",
    "/waku/2/rs/2/4",
    "/waku/2/rs/2/5",
    "/waku/2/rs/2/6",
    "/waku/2/rs/2/7",
]


class TestRunningNodesStaticSharding(StepsSharding):
    @pytest.mark.parametrize("pubsub_topic", PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
    def test_single_pubsub_topic(self, pubsub_topic):
        self.setup_main_relay_nodes(pubsub_topic=pubsub_topic)
        self.subscribe_first_relay_node(pubsub_topics=[pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=[pubsub_topic])
        self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_multiple_pubsub_topics(self):
        self.setup_main_relay_nodes(pubsub_topic=PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
        self.subscribe_first_relay_node(pubsub_topics=PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
        self.subscribe_second_relay_node(pubsub_topics=PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
        for pubsub_topic in PUBSUB_TOPICS_DIFFERENT_CLUSTERS:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_same_cluster_different_shards(self):
        self.setup_first_relay_node(pubsub_topic="/waku/2/rs/2/0")
        self.setup_second_relay_node(pubsub_topic="/waku/2/rs/2/1")
        self.subscribe_first_relay_node(pubsub_topics=["/waku/2/rs/2/0"])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/2/1"])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic="/waku/2/rs/2/0")
            raise AssertionError("Publish on different shard worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_different_cluster_same_shard(self):
        self.setup_first_relay_node(pubsub_topic="/waku/2/rs/2/0")
        self.setup_second_relay_node(pubsub_topic="/waku/2/rs/3/0")
        self.subscribe_first_relay_node(pubsub_topics=["/waku/2/rs/2/0"])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/3/0"])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic="/waku/2/rs/2/0")
            raise AssertionError("Publish on different cluster worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_publish_without_subscribing_works(self):
        self.setup_main_relay_nodes(pubsub_topic="/waku/2/rs/2/0")
        for node in self.main_nodes:
            self.relay_message(node, self.create_message(), self.test_pubsub_topic)

    @pytest.mark.xfail("nwaku" in NODE_2, reason="Bug reported: https://github.com/waku-org/nwaku/issues/2546")
    def test_retrieve_messages_without_subscribing_shouldn_work(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
            raise AssertionError("Retrieving messages without subscribing worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)