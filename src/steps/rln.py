from src.env_vars import DEFAULT_NWAKU, RLN_CREDENTIALS, NODEKEY
from src.libs.common import gen_step_id, to_base64
from src.libs.custom_logger import get_custom_logger
import os
import inspect
import pytest
import allure
from time import time
from src.node.waku_node import WakuNode, rln_credential_store_ready
from src.test_data import PUBSUB_TOPICS_RLN

logger = get_custom_logger(__name__)


class StepsRLN:
    test_pubsub_topic = PUBSUB_TOPICS_RLN[0]
    test_content_topic = "/test/1/waku-rln-relay/proto"
    test_payload = "RLN relay works!!"

    main_nodes = []
    optional_nodes = []

    @pytest.fixture(scope="function")
    def register_main_rln_relay_nodes(self, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.node1 = WakuNode(DEFAULT_NWAKU, f"node1_{request.cls.test_id}")
        self.node1.register_rln(rln_creds_source=RLN_CREDENTIALS, rln_creds_id="1")
        self.node2 = WakuNode(DEFAULT_NWAKU, f"node2_{request.cls.test_id}")
        self.node2.register_rln(rln_creds_source=RLN_CREDENTIALS, rln_creds_id="2")

    @allure.step
    def setup_main_rln_relay_nodes(self, **kwargs):
        self.setup_first_rln_relay_node(**kwargs)
        self.setup_second_rln_relay_node(**kwargs)

    @allure.step
    def setup_first_rln_relay_node(self, **kwargs):
        self.node1 = WakuNode(DEFAULT_NWAKU, f"node1_{self.test_id}")
        self.node1.start(relay="true", nodekey=NODEKEY, rln_creds_source=RLN_CREDENTIALS, rln_creds_id="1", rln_relay_membership_index="1", **kwargs)
        self.enr_uri = self.node1.get_enr_uri()
        self.multiaddr_with_id = self.node1.get_multiaddr_with_id()
        self.main_nodes.extend([self.node1])

    @allure.step
    def setup_second_rln_relay_node(self, **kwargs):
        self.node2 = WakuNode(DEFAULT_NWAKU, f"node2_{self.test_id}")
        self.node2.start(
            relay="true",
            discv5_bootstrap_node=self.enr_uri,
            rln_creds_source=RLN_CREDENTIALS,
            rln_creds_id="2",
            rln_relay_membership_index="1",
            **kwargs,
        )
        if self.node2.is_nwaku():
            self.node2.add_peers([self.multiaddr_with_id])
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
    def create_message(self, **kwargs):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        message.update(kwargs)
        return message

    @allure.step
    def publish_message(self, message=None, pubsub_topic=None, sender=None):
        if message is None:
            message = self.create_message()
        if pubsub_topic is None:
            pubsub_topic = self.test_pubsub_topic
        if not sender:
            sender = self.node1

        sender.send_relay_message(message, pubsub_topic)

    @allure.step
    def ensure_relay_subscriptions_on_nodes(self, node_list, pubsub_topic_list):
        for node in node_list:
            node.set_relay_subscriptions(pubsub_topic_list)

    @allure.step
    def subscribe_main_relay_nodes(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.ensure_relay_subscriptions_on_nodes(self.main_nodes, [self.test_pubsub_topic])
