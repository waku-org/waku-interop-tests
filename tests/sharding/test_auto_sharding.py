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
RUNNING NODES:
    - running on all kind of cluster
    - nodes on same cluster connect
    - nodes on different clusters do not connect
MULTIPLE NDES
"""


@pytest.mark.skipif(
    "go-waku" in NODE_1 or "go-waku" in NODE_2,
    reason="Autosharding tests work only on nwaku because of https://github.com/waku-org/go-waku/issues/1061",
)
class TestRunningNodesAutosharding(StepsSharding):
    def test_same_cluster_same_content_topic(self):
        self.setup_main_relay_nodes(cluster_id=2)
        self.subscribe_first_relay_node(content_topics=[self.test_content_topic])
        self.subscribe_second_relay_node(content_topics=[self.test_content_topic])
        self.check_published_message_reaches_relay_peer(content_topic=self.test_content_topic)

    def test_same_cluster_different_content_topic(self):
        self.setup_main_relay_nodes(cluster_id=2)
        self.subscribe_first_relay_node([self.test_content_topic])
        self.subscribe_second_relay_node(["/myapp/1/latest/proto"])
        try:
            self.check_published_message_reaches_relay_peer(content_topic=self.test_content_topic)
            raise AssertionError("Publish on different content topic worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)
