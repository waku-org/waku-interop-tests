import os
import inspect
import pytest
import allure

from src.node.waku_message import WakuMessage
from src.steps.common import StepsCommon
from src.test_data import PUBSUB_TOPICS_RLN
from src.env_vars import DEFAULT_NWAKU, RLN_CREDENTIALS, NODEKEY, NODE_1, NODE_2
from src.libs.common import gen_step_id, delay
from src.libs.custom_logger import get_custom_logger
from src.node.waku_node import WakuNode, rln_credential_store_ready

logger = get_custom_logger(__name__)


class StepsRLN(StepsCommon):
    test_pubsub_topic = PUBSUB_TOPICS_RLN[0]
    test_content_topic = "/test/1/waku-rln-relay/proto"
    test_payload = "RLN relay works!!"

    main_nodes = []
    optional_nodes = []
    multiaddr_list = []
    lightpush_nodes = []

    @pytest.fixture(scope="function")
    def register_main_rln_relay_nodes(self, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.register_rln_single_node(rln_creds_source=RLN_CREDENTIALS, rln_creds_id="1")
        self.register_rln_single_node(rln_creds_source=RLN_CREDENTIALS, rln_creds_id="2")

    @allure.step
    def setup_main_rln_relay_nodes(self, **kwargs):
        self.setup_first_rln_relay_node(**kwargs)
        self.setup_second_rln_relay_node(**kwargs)

    @allure.step
    def setup_first_rln_relay_node(self, **kwargs):
        self.node1 = WakuNode(NODE_1, f"node1_{self.test_id}")
        self.node1.start(
            relay="true",
            nodekey=NODEKEY,
            rln_creds_source=RLN_CREDENTIALS,
            rln_creds_id="1",
            rln_relay_membership_index="1",
            **kwargs,
        )
        self.enr_uri = self.node1.get_enr_uri()
        self.multiaddr_with_id = self.node1.get_multiaddr_with_id()
        self.main_nodes.extend([self.node1])

        self.multiaddr_list.extend([self.node1.get_multiaddr_with_id()])

    @allure.step
    def setup_second_rln_relay_node(self, **kwargs):
        self.node2 = WakuNode(NODE_2, f"node2_{self.test_id}")
        self.node2.start(
            relay="true",
            discv5_bootstrap_node=self.enr_uri,
            rln_creds_source=RLN_CREDENTIALS,
            rln_creds_id="2",
            rln_relay_membership_index="1",
            **kwargs,
        )
        self.add_node_peer(self.node2, [self.multiaddr_with_id])
        self.main_nodes.extend([self.node2])

    @allure.step
    def setup_second_lightpush_node(self, relay="false", **kwargs):
        self.light_push_node2 = WakuNode(NODE_2, f"lightpush_node2_{self.test_id}")
        self.light_push_node2.start(relay=relay, discv5_bootstrap_node=self.enr_uri, lightpush="true", lightpushnode=self.multiaddr_list[0], **kwargs)
        if relay == "true":
            self.main_nodes.extend([self.light_push_node2])
        self.lightpush_nodes.extend([self.light_push_node2])
        self.add_node_peer(self.light_push_node2, self.multiaddr_list)

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
    def register_rln_single_node(self, **kwargs):
        logger.debug("Registering RLN credentials for single node")
        self.node1 = WakuNode(DEFAULT_NWAKU, f"node1_{gen_step_id()}")
        self.node1.register_rln(rln_creds_source=kwargs["rln_creds_source"], rln_creds_id=kwargs["rln_creds_id"])

    @allure.step
    def check_rln_registration(self, key_id):
        current_working_directory = os.getcwd()
        creds_file_path = f"{current_working_directory}/keystore_{key_id}/keystore.json"
        try:
            rln_credential_store_ready(creds_file_path)
        except Exception as ex:
            logger.error(f"Credentials at {creds_file_path} not available: {ex}")
            raise

    @allure.step
    def publish_message(self, message=None, pubsub_topic=None, sender=None):
        if message is None:
            message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.node1

        sender.send_relay_message(message, pubsub_topic)

    def publish_light_push_message(self, message=None, pubsub_topic=None, sender=None):
        if message is None:
            message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.node1

        payload = self.create_payload(pubsub_topic, message)
        sender.send_light_push_message(payload)

    @allure.step
    def ensure_relay_subscriptions_on_nodes(self, node_list, pubsub_topic_list):
        for node in node_list:
            node.set_relay_subscriptions(pubsub_topic_list)

    @allure.step
    def subscribe_main_relay_nodes(self):
        self.ensure_relay_subscriptions_on_nodes(self.main_nodes, [self.test_pubsub_topic])

    @allure.step
    def create_payload(self, pubsub_topic=None, message=None, **kwargs):
        if message is None:
            message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        payload = {"pubsubTopic": pubsub_topic, "message": message}
        payload.update(kwargs)
        return payload

    @allure.step
    def check_light_pushed_message_reaches_receiving_peer(
        self, pubsub_topic=None, message=None, message_propagation_delay=0.1, sender=None, peer_list=None
    ):
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.node1
        if not peer_list:
            peer_list = self.main_nodes + self.optional_nodes

        payload = self.create_payload(pubsub_topic, message)
        logger.debug("Lightpushing message")
        sender.send_light_push_message(payload)
        delay(message_propagation_delay)
        for index, peer in enumerate(peer_list):
            logger.debug(f"Checking that peer NODE_{index + 1}:{peer.image} can find the lightpushed message")
            get_messages_response = peer.get_relay_messages(pubsub_topic)
            assert get_messages_response, f"Peer NODE_{index + 1}:{peer.image} couldn't find any messages"
            assert len(get_messages_response) == 1, f"Expected 1 message but got {len(get_messages_response)}"
            waku_message = WakuMessage(get_messages_response)
            waku_message.assert_received_message(payload["message"])
