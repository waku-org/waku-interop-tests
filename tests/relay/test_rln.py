import pytest
from src.env_vars import NODE_1, NODE_2
from src.libs.custom_logger import get_custom_logger
from time import time
from src.libs.common import delay, to_base64
from src.steps.relay import StepsRelay
from src.test_data import INVALID_CONTENT_TOPICS, INVALID_PAYLOADS, SAMPLE_INPUTS, SAMPLE_TIMESTAMPS, VALID_PUBSUB_TOPICS
from src.node.waku_message import WakuMessage

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("setup_main_rln_relay_nodes", "subscribe_main_relay_nodes")
class TestRelayRLN(StepsRelay):
    def test_publish_with_valid_payloads(self):
        failed_payloads = []
        for payload in SAMPLE_INPUTS:
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                self.check_published_message_reaches_relay_peer(message)
            except Exception as e:
                logger.error(f'Payload {payload["description"]} failed: {str(e)}')
                failed_payloads.append(payload["description"])
        assert not failed_payloads, f"Payloads failed: {failed_payloads}"
