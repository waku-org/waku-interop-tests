from src.libs.custom_logger import get_custom_logger
from src.steps.sharding import StepsSharding
from src.test_data import PUBSUB_TOPICS_SAME_CLUSTER

logger = get_custom_logger(__name__)

"""

- subscribe to shard 1 send a message subscribe to new shard and send new message
- subscribe to shard 1 send a message, unscubscribe from that shard and subscribe to new shard and send new message
- publish on multiple pubsub topics and only after fetch messages. Check that they are retrieved accordingly

"""


class TestRelayStaticSharding(StepsSharding):
    def test_publish_without_subscribing_works(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        for node in self.main_nodes:
            self.relay_message(node, self.create_message(), self.test_pubsub_topic)

    def test_retrieve_messages_without_subscribing(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)
            if self.node2.is_nwaku():
                pass
            else:
                raise AssertionError("Retrieving messages without subscribing worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)

    def test_subscribe_and_publish_on_another_shard(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        self.subscribe_main_relay_nodes(pubsub_topics=["/waku/2/rs/2/1"])
        self.check_published_message_reaches_relay_peer(pubsub_topic="/waku/2/rs/2/1")
        self.check_published_message_reaches_relay_peer(pubsub_topic=self.test_pubsub_topic)

    def test_cant_publish_on_unsubscribed_shard(self):
        self.setup_main_relay_nodes(pubsub_topic=self.test_pubsub_topic)
        self.subscribe_main_relay_nodes(pubsub_topics=[self.test_pubsub_topic])
        try:
            self.check_published_message_reaches_relay_peer(pubsub_topic="/waku/2/rs/2/1")
            raise AssertionError("Publishing messages on unsubscribed shard worked!!!")
        except Exception as ex:
            assert "Failed to publish: Node not subscribed to topic: /waku/2/rs/2/1" in str(ex)

    def test_subscribe_via_api_to_new_pubsub_topics(self):
        self.setup_main_relay_nodes(pubsub_topic=PUBSUB_TOPICS_SAME_CLUSTER[:1])
        self.subscribe_main_relay_nodes(pubsub_topics=PUBSUB_TOPICS_SAME_CLUSTER[1:])
        for pubsub_topic in PUBSUB_TOPICS_SAME_CLUSTER[1:]:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)

    def test_subscribe_via_api_to_new_pubsub_topics_other_cluster(self):
        topics = ["/waku/2/rs/2/0", "/waku/2/rs/3/0"]
        self.setup_main_relay_nodes(cluster_id=2, pubsub_topic=topics[0])
        self.subscribe_first_relay_node(pubsub_topics=topics)
        self.subscribe_second_relay_node(pubsub_topics=topics)
        for pubsub_topic in topics:
            self.check_published_message_reaches_relay_peer(pubsub_topic=pubsub_topic)
