import pytest
from src.env_vars import NODE_2
from src.libs.custom_logger import get_custom_logger
from src.steps.sharding import StepsSharding

logger = get_custom_logger(__name__)

"""
VIA API
VIA FLAGS like pubsub topic and content topic
FILTER
RELAY
- subscribe to shard 1 send a message subscribe to new shard and send new message
- subscribe to shard 1 send a message, unscubscribe from that shard and subscribe to new shard and send new message
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


class TestRunningNodes(StepsSharding):
    @pytest.mark.parametrize("pubsub_topic", PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
    def test_single_pubsub_topic(self, pubsub_topic):
        self.setup_main_relay_nodes(pubsub_topic=pubsub_topic)
        self.subscribe_first_relay_node(pubsub_topics=[pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=[pubsub_topic])
        self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_multiple_pubsub_topics_same_cluster(self):
        self.setup_main_relay_nodes(pubsub_topic=PUBSUB_TOPICS_SAME_CLUSTER)
        self.subscribe_first_relay_node(pubsub_topics=PUBSUB_TOPICS_SAME_CLUSTER)
        self.subscribe_second_relay_node(pubsub_topics=PUBSUB_TOPICS_SAME_CLUSTER)
        for pubsub_topic in PUBSUB_TOPICS_SAME_CLUSTER:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_multiple_pubsub_topics_different_clusters(self):
        self.setup_main_relay_nodes(pubsub_topic=PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
        self.subscribe_first_relay_node(pubsub_topics=PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
        self.subscribe_second_relay_node(pubsub_topics=PUBSUB_TOPICS_DIFFERENT_CLUSTERS)
        for pubsub_topic in PUBSUB_TOPICS_DIFFERENT_CLUSTERS:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_same_cluster_different_shards(self):
        self.setup_first_relay_node(pubsub_topic=self.test_pubsub_topic)
        self.setup_second_relay_node(pubsub_topic="/waku/2/rs/2/1")
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/2/1"])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
            raise AssertionError("Publish on different shard worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_different_cluster_same_shard(self):
        self.setup_first_relay_node(pubsub_topic=self.test_pubsub_topic)
        self.setup_second_relay_node(pubsub_topic="/waku/2/rs/3/0")
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/3/0"])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
            raise AssertionError("Publish on different cluster worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_different_cluster_different_shard(self):
        self.setup_first_relay_node(pubsub_topic=self.test_pubsub_topic)
        self.setup_second_relay_node(pubsub_topic="/waku/2/rs/3/1")
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/3/1"])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
            raise AssertionError("Publish on different cluster worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_publish_without_subscribing_works(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        self.setup_second_relay_node(pubsub_topic=self.test_pubsub_topic)
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
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

    def test_subscribe_and_publish_on_another_shard(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        self.subscribe_first_relay_node(pubsub_topics=["/waku/2/rs/2/1"])
        self.subscribe_second_relay_node(pubsub_topics=["/waku/2/rs/2/1"])
        self.check_published_message_reaches_relay_peer(pubsub_topic="/waku/2/rs/2/1")

    def test_cant_publish_on_unsubscribed_shard(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=[self.test_pubsub_topic])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic="/waku/2/rs/2/1")
            raise AssertionError("Publishing messages on unsubscribed shard worked!!!")
        except Exception as ex:
            assert "Failed to publish: Node not subscribed to topic: /waku/2/rs/2/1" in str(ex)

    @pytest.mark.parametrize("content_topic", ["/toychat/2/huilong/proto", "/aaaaa/3/bbbbb/proto"])
    @pytest.mark.skipif("go-waku" in NODE_2, reason="Test doesn't work on go-waku")
    def test_content_topic_also_in_docker_flags(self, content_topic):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic, content_topic=content_topic)
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)

    @pytest.mark.xfail("go-waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1034#issuecomment-2011350765")
    def test_pubsub_topic_not_in_docker_flags(self):
        self.setup_main_relay_nodes(cluster_id=2)
        self.subscribe_first_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.subscribe_second_relay_node(pubsub_topics=[self.test_pubsub_topic])
        self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)

    def test_subscribe_via_api_to_new_pubsub_topics(self):
        self.setup_main_relay_nodes(pubsub_topic=PUBSUB_TOPICS_SAME_CLUSTER[:1])
        self.subscribe_first_relay_node(pubsub_topics=PUBSUB_TOPICS_SAME_CLUSTER[1:])
        self.subscribe_second_relay_node(pubsub_topics=PUBSUB_TOPICS_SAME_CLUSTER[1:])
        for pubsub_topic in PUBSUB_TOPICS_SAME_CLUSTER[1:]:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_subscribe_via_api_to_new_pubsub_topics_other_cluster(self):
        topics = ["/waku/2/rs/2/0", "/waku/2/rs/3/0"]
        self.setup_main_relay_nodes(cluster_id=2, pubsub_topic=topics[0])
        self.subscribe_first_relay_node(pubsub_topics=topics)
        self.subscribe_second_relay_node(pubsub_topics=topics)
        for pubsub_topic in topics:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_start_node_with_50_pubsub_topics(self):
        topics = ["/waku/2/rs/2/" + str(i) for i in range(50)]
        self.setup_main_relay_nodes(pubsub_topic=topics)
        self.subscribe_first_relay_node(pubsub_topics=topics)
        self.subscribe_second_relay_node(pubsub_topics=topics)
        for pubsub_topic in topics:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)
