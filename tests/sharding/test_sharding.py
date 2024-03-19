import pytest
from src.env_vars import NODE_1, NODE_2
from src.libs.custom_logger import get_custom_logger
from time import time
from src.libs.common import delay, to_base64
from src.steps.sharding import StepsSharding
from src.test_data import INVALID_CONTENT_TOPICS, INVALID_PAYLOADS, SAMPLE_INPUTS, SAMPLE_TIMESTAMPS, VALID_PUBSUB_TOPICS
from src.node.waku_message import WakuMessage

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


class TestSharding(StepsSharding):
    def test_same_cluster_same_content_topic(self):
        self.setup_main_relay_nodes(cluster_id=2)
        self.subscribe_first_relay_node([self.test_content_topic])
        self.subscribe_second_relay_node([self.test_content_topic])
        self.check_published_message_reaches_relay_peer(self.create_message(payload=to_base64(self.test_payload)))

    def test_same_cluster_different_content_topic(self):
        self.setup_main_relay_nodes(cluster_id=2)
        self.subscribe_first_relay_node([self.test_content_topic])
        self.subscribe_second_relay_node(["/myapp/1/latest/proto"])
        try:
            self.check_published_message_reaches_relay_peer(self.create_message(payload=to_base64(self.test_payload)))
            raise AssertionError("Publish on different content topic worked!!!")
        except Exception as ex:
            assert "Not Found" in str(ex)
