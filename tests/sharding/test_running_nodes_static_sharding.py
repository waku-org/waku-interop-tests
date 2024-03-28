import pytest
from src.env_vars import NODE_2
from src.libs.custom_logger import get_custom_logger
from src.steps.sharding import StepsSharding
from src.test_data import PUBSUB_TOPICS_DIFFERENT_CLUSTERS, PUBSUB_TOPICS_SAME_CLUSTER

logger = get_custom_logger(__name__)

"""
VIA API
VIA FLAGS like pubsub topic and content topic
FILTER
RUNNING NODES:
    - running on all kind of cluster
    - nodes on same cluster connect
    - nodes on different clusters do not connect
MULTIPLE NDES
"""


class TestRunningNodesStaticSharding(StepsSharding):
    @pytest.mark.parametrize("pubsub_topic", PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
    def test_single_pubsub_topic(self, pubsub_topic):
        self.setup_main_relay_nodes(pubsub_topic=pubsub_topic)
        self.subscribe_main_relay_nodes(pubsub_topics=[pubsub_topic])
        self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_multiple_pubsub_topics_same_cluster(self):
        self.setup_main_relay_nodes(pubsub_topic=PUBSUB_TOPICS_SAME_CLUSTER)
        self.subscribe_main_relay_nodes(pubsub_topics=PUBSUB_TOPICS_SAME_CLUSTER)
        for pubsub_topic in PUBSUB_TOPICS_SAME_CLUSTER:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_multiple_pubsub_topics_different_clusters(self):
        self.setup_main_relay_nodes(pubsub_topic=PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
        self.subscribe_main_relay_nodes(pubsub_topics=PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
        for pubsub_topic in PUBSUB_TOPICS_DIFFERENT_CLUSTERS:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_2_nodes_same_cluster_different_shards(self):
        self.setup_first_relay_node(pubsub_topic=self.test_pubsub_topic)
        self.setup_second_relay_node(pubsub_topic="/waku/2/rs/2/1")
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/2/1"])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
            raise AssertionError("Publish on different shard worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_2_nodes_different_cluster_same_shard(self):
        self.setup_first_relay_node(pubsub_topic=self.test_pubsub_topic)
        self.setup_second_relay_node(pubsub_topic="/waku/2/rs/3/0")
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/3/0"])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
            raise AssertionError("Publish on different cluster worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_2_nodes_different_cluster_different_shard(self):
        self.setup_first_relay_node(pubsub_topic=self.test_pubsub_topic)
        self.setup_second_relay_node(pubsub_topic="/waku/2/rs/3/1")
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/3/1"])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
            raise AssertionError("Publish on different cluster worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    @pytest.mark.parametrize("content_topic", ["/toychat/2/huilong/proto", "/aaaaa/3/bbbbb/proto"])
    @pytest.mark.skipif("go-waku" in NODE_2, reason="Test doesn't work on go-waku")
    def test_content_topic_also_in_docker_flags(self, content_topic):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic, content_topic=content_topic)
        self.subscribe_main_relay_nodes(pubsub_topics=[self.test_pubsub_topic])
        self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)

    # Bug reported: https://github.com/waku-org/go-waku/issues/1034#issuecomment-2011350765
    def test_pubsub_topic_not_in_docker_flags(self):
        self.setup_main_relay_nodes(cluster_id=2)
        self.subscribe_main_relay_nodes(pubsub_topics=[self.test_pubsub_topic])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
        except Exception as ex:
            assert f"Peer NODE_2:{NODE_2} couldn't find any messages" in str(ex)

    def test_start_node_with_50_pubsub_topics(self):
        topics = ["/waku/2/rs/2/" + str(i) for i in range(50)]
        self.setup_main_relay_nodes(pubsub_topic=topics)
        self.subscribe_main_relay_nodes(pubsub_topics=topics)
        for pubsub_topic in topics:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)
