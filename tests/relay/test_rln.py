import pytest
from src.env_vars import NODE_1, NODE_2
from src.libs.custom_logger import get_custom_logger
from time import time
from src.libs.common import delay, to_base64
from src.steps.relay import StepsRelay
from src.test_data import INVALID_CONTENT_TOPICS, INVALID_PAYLOADS, SAMPLE_INPUTS, SAMPLE_TIMESTAMPS, VALID_PUBSUB_TOPICS
from src.node.waku_message import WakuMessage

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("setup_main_rln_relay_nodes")
class TestRelayRLN(StepsRelay):
    def test_rln_registration(self):
        logger.debug(f"Running test to register and start relay node with RLN")
