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
RUNNING NODES
MULTIPLE NDES
"""


class TestSharding(StepsSharding):
    def test_sharding_publish_with_valid_payloads(self):
        self.setup_main_relay_nodes()
        self.subscribe_main_relay_nodes()
        self.relay_warm_up()
        payload = "A simple string"
        message = self.create_message(payload=to_base64(payload))
        self.check_published_message_reaches_relay_peer(message)
