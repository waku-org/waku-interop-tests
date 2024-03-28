import pytest
from src.env_vars import NODE_1, NODE_2
from src.libs.custom_logger import get_custom_logger
from src.steps.sharding import StepsSharding
from src.test_data import CONTENT_TOPICS_DIFFERENT_SHARDS, CONTENT_TOPICS_SHARD_0


logger = get_custom_logger(__name__)

"""
RELAY
- subscribe to shard 1 send a message subscribe to new shard and send new message
- subscribe to shard 1 send a message, unscubscribe from that shard and subscribe to new shard and send new message
- publish on multiple content topics and only after fetch messages. Check that they are retrieved accordingly
"""


@pytest.mark.skipif(
    "go-waku" in NODE_1 or "go-waku" in NODE_2,
    reason="Autosharding tests work only on nwaku because of https://github.com/waku-org/go-waku/issues/1061",
)
class TestRelayAutosharding(StepsSharding):
    auto_cluster = 2

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
