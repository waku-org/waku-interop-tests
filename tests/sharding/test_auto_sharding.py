import pytest
from src.env_vars import NODE_1, NODE_2
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
- publish on multiple content topics and only after fetch messages. Check that they are retrieved accordingly
RUNNING NODES:
    - nodes on same cluster connect
    - nodes on different clusters do not connect
    - combination of satic with auto
    - start nodes with and without pubsubtopic
MULTIPLE NDES
"""

CONTENT_TOPICS_DIFFERENT_SHARDS = [
    "/myapp/1/latest/proto",  # resolves to shard 0
    "/waku/2/content/test.js",  # resolves to shard 1
    "/app/22/sometopic/someencoding",  # resolves to shard 2
    "/toychat/2/huilong/proto",  # resolves to shard 3
    "/statusim/1/community/cbor",  # resolves to shard 4
    "/app/27/sometopic/someencoding",  # resolves to shard 5
    "/app/29/sometopic/someencoding",  # resolves to shard 6
    "/app/20/sometopic/someencoding",  # resolves to shard 7
]

CONTENT_TOPICS_SHARD_0 = [
    "/newsService/1.0/weekly/protobuf",
    "/newsService/1.0/alerts/xml",
    "/newsService/1.0/updates/json",
    "/newsService/2.0/alerts/json",
    "/newsService/2.0/summaries/xml",
    "/newsService/2.0/highlights/yaml",
    "/newsService/3.0/weekly/json",
    "/newsService/3.0/summaries/xml",
]

CONTENT_TOPICS_SHARD_7 = [
    "/newsService/2.0/alerts/yaml",
    "/newsService/2.0/highlights/xml",
    "/newsService/3.0/daily/protobuf",
    "/newsService/3.0/alerts/xml",
    "/newsService/3.0/updates/protobuf",
    "/newsService/3.0/reviews/xml",
    "/newsService/4.0/alerts/yaml",
    "/newsService/4.0/updates/yaml",
]


@pytest.mark.skipif(
    "go-waku" in NODE_1 or "go-waku" in NODE_2,
    reason="Autosharding tests work only on nwaku because of https://github.com/waku-org/go-waku/issues/1061",
)
class TestRunningNodesAutosharding(StepsSharding):
    auto_cluster = 2

    @pytest.mark.parametrize("content_topic", CONTENT_TOPICS_DIFFERENT_SHARDS)
    def test_single_content_topic(self, content_topic):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=content_topic)
        self.subscribe_first_relay_node(content_topics=[content_topic])
        self.subscribe_second_relay_node(content_topics=[content_topic])
        self.check_published_message_reaches_relay_peer(content_topic=content_topic)

    @pytest.mark.parametrize("content_topic_list", [CONTENT_TOPICS_SHARD_0, CONTENT_TOPICS_SHARD_7])
    def test_multiple_content_topics_same_shard(self, content_topic_list):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=content_topic_list)
        self.subscribe_first_relay_node(content_topics=content_topic_list)
        self.subscribe_second_relay_node(content_topics=content_topic_list)
        for content_topic in content_topic_list:
            self.check_published_message_reaches_relay_peer(content_topic=content_topic)

    def test_multiple_content_topics_different_shard(self):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=CONTENT_TOPICS_DIFFERENT_SHARDS)
        self.subscribe_first_relay_node(content_topics=CONTENT_TOPICS_DIFFERENT_SHARDS)
        self.subscribe_second_relay_node(content_topics=CONTENT_TOPICS_DIFFERENT_SHARDS)
        for content_topic in CONTENT_TOPICS_DIFFERENT_SHARDS:
            self.check_published_message_reaches_relay_peer(content_topic=content_topic)

    def test_2_nodes_different_content_topic_same_shard(self):
        self.setup_first_relay_node(cluster_id=self.auto_cluster, content_topic="/newsService/1.0/weekly/protobuf")
        self.setup_second_relay_node(cluster_id=self.auto_cluster, content_topic="/newsService/1.0/alerts/xml")
        self.subscribe_first_relay_node(content_topics=["/newsService/1.0/weekly/protobuf"])
        self.subscribe_second_relay_node(content_topics=["/newsService/1.0/alerts/xml"])
        try:
            self.check_published_message_reaches_relay_peer(content_topic="/newsService/1.0/weekly/protobuf")
            raise AssertionError("Publish on different content topic worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_2_nodes_different_content_topic_different_shard(self):
        self.setup_first_relay_node(cluster_id=self.auto_cluster, content_topic="/myapp/1/latest/proto")
        self.setup_second_relay_node(cluster_id=self.auto_cluster, content_topic="/waku/2/content/test.js")
        self.subscribe_first_relay_node(content_topics=["/myapp/1/latest/proto"])
        self.subscribe_second_relay_node(content_topics=["/waku/2/content/test.js"])
        try:
            self.check_published_message_reaches_relay_peer(content_topic="/myapp/1/latest/proto")
            raise AssertionError("Publish on different content topic worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    @pytest.mark.parametrize("pubsub_topic", ["/waku/2/rs/2/0", "/waku/2/rs/2/1"])
    def test_pubsub_topic_also_in_docker_flags(self, pubsub_topic):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, pubsub_topic=pubsub_topic, content_topic=self.test_content_topic)
        self.subscribe_main_relay_nodes(content_topics=[self.test_content_topic])
        self.check_published_message_reaches_relay_peer(content_topic=self.test_content_topic)

    def test_content_topic_not_in_docker_flags(self):
        self.setup_main_relay_nodes(cluster_id=2, pubsub_topic=self.test_pubsub_topic)
        self.subscribe_main_relay_nodes(content_topics=[self.test_content_topic])
        self.check_published_message_reaches_relay_peer(content_topic=self.test_content_topic)

    def test_content_topic_and_pubsub_topic_not_in_docker_flags(self):
        self.setup_main_relay_nodes(cluster_id=2)
        self.subscribe_main_relay_nodes(content_topics=[self.test_content_topic])
        self.check_published_message_reaches_relay_peer(content_topic=self.test_content_topic)

    # start node with multiple pubsub topics and multiple content topics
    # use both autosharding and static sharding

    ## RELAY

    def test_publish_without_subscribing_works(self):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=self.test_content_topic)
        for node in self.main_nodes:
            self.relay_message(node, self.create_message(contentTopic=self.test_content_topic))

    def test_retrieve_messages_without_subscribing(self):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=self.test_content_topic)
        self.check_published_message_reaches_relay_peer(content_topic=self.test_content_topic)

    def test_subscribe_and_publish_on_another_content_topic_from_same_shard(self):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=self.test_content_topic)
        self.subscribe_main_relay_nodes(content_topics=["/newsService/1.0/weekly/protobuf"])
        self.check_published_message_reaches_relay_peer(content_topic="/newsService/1.0/weekly/protobuf")
        self.check_published_message_reaches_relay_peer(content_topic=self.test_content_topic)

    def test_subscribe_and_publish_on_another_content_topic_from_another_shard(self):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=self.test_content_topic)
        self.subscribe_main_relay_nodes(content_topics=["/toychat/2/huilong/proto"])
        self.check_published_message_reaches_relay_peer(content_topic="/toychat/2/huilong/proto")
        self.check_published_message_reaches_relay_peer(content_topic=self.test_content_topic)

    def test_publish_on_unsubscribed_content_topic_works(self):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=self.test_content_topic)
        self.subscribe_main_relay_nodes(content_topics=[self.test_content_topic])
        for node in self.main_nodes:
            self.relay_message(node, self.create_message(contentTopic="/toychat/2/huilong/proto"))

    def test_cant_retrieve_messages_on_unsubscribed_content_topic(self):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=self.test_content_topic)
        self.subscribe_main_relay_nodes(content_topics=[self.test_content_topic])
        try:
            self.check_published_message_reaches_relay_peer(content_topic="/toychat/2/huilong/proto")
            raise AssertionError("Retrieving messages on unsubscribed content topic worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    @pytest.mark.parametrize("content_topic_list", [CONTENT_TOPICS_SHARD_0, CONTENT_TOPICS_DIFFERENT_SHARDS])
    def test_subscribe_via_api_to_new_content_topics(self, content_topic_list):
        self.setup_main_relay_nodes(cluster_id=self.auto_cluster, content_topic=content_topic_list[:1])
        self.subscribe_main_relay_nodes(content_topics=content_topic_list[1:])
        for content_topic in content_topic_list[1:]:
            self.check_published_message_reaches_relay_peer(content_topic=content_topic)
