import os
import pytest

from src.env_vars import RLN_CREDENTIALS
from src.libs.common import delay, to_base64
from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay
from src.test_data import SAMPLE_INPUTS, PUBSUB_TOPICS_RLN

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("register_main_rln_relay_nodes", "setup_main_rln_relay_nodes", "subscribe_main_relay_nodes")
class TestRelayRLN(StepsRelay):
    test_pubsub_topic = PUBSUB_TOPICS_RLN[0]

    def test_publish_valid_payloads_at_slow_pace(self):
        failed_payloads = []
        for payload in SAMPLE_INPUTS:
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                self.check_published_message_reaches_relay_peer(message)
            except Exception as e:
                logger.error(f'Payload {payload["description"]} failed: {str(e)}')
                failed_payloads.append(payload["description"])
            delay(1)
            assert not failed_payloads, f"Payloads failed: {failed_payloads}"
