import os
import inspect
import pytest
import allure

from src.node.waku_message import WakuMessage
from src.steps.common import StepsCommon
from src.test_data import PUBSUB_TOPICS_RLN, VALID_PUBSUB_TOPICS
from src.env_vars import DEFAULT_NWAKU, RLN_CREDENTIALS, NODEKEY, NODE_1, NODE_2, ADDITIONAL_NODES
from src.libs.common import gen_step_id, delay
from src.libs.custom_logger import get_custom_logger
from src.node.waku_node import WakuNode, rln_credential_store_ready

logger = get_custom_logger(__name__)


class StepsPeerStore(StepsCommon):
    test_pubsub_topic = VALID_PUBSUB_TOPICS[0]
    test_content_topic = "/test/1/waku-relay/proto"
    test_payload = "Relay works!!"

    main_nodes = []
    optional_nodes = []
    multiaddr_list = []

    @allure.step
    def setup_first_relay_node(self, **kwargs):
        self.node1 = WakuNode(NODE_1, f"node1_{self.test_id}")
        self.node1.start(relay="true", nodekey=NODEKEY, **kwargs)
        self.enr_uri = self.node1.get_enr_uri()
        self.multiaddr_with_id = self.node1.get_multiaddr_with_id()
        self.main_nodes.extend([self.node1])

    @allure.step
    def setup_second_relay_node(self, **kwargs):
        self.node2 = WakuNode(NODE_2, f"node2_{self.test_id}")
        self.node2.start(
            relay="true",
            discv5_bootstrap_node=self.enr_uri,
            **kwargs,
        )
        self.add_node_peer(self.node2, [self.multiaddr_with_id])
        self.main_nodes.extend([self.node2])

    @allure.step
    def setup_third_relay_node(self, **kwargs):
        self.node3 = WakuNode(NODE_1, f"node3_{self.test_id}")
        self.node3.start(
            relay="true",
            discv5_bootstrap_node=self.enr_uri,
            **kwargs,
        )
        self.add_node_peer(self.node3, [self.multiaddr_with_id])
        self.main_nodes.extend([self.node3])
