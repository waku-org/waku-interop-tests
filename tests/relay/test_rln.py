import math
from time import time

import pytest

from src.libs.common import delay, to_base64
from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay
from src.steps.rln import StepsRLN
from src.test_data import SAMPLE_INPUTS

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("register_main_rln_relay_nodes", "setup_main_rln_relay_nodes", "subscribe_main_relay_nodes")
class TestRelayRLN(StepsRLN, StepsRelay):
    def test_publish_with_valid_payloads_at_slow_rate(self):
        failed_payloads = []
        for payload in SAMPLE_INPUTS[:5]:
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                self.publish_message(message)
            except Exception as e:
                logger.error(f'Payload {payload["description"]} failed: {str(e)}')
                failed_payloads.append(payload["description"])
            delay(1)
            assert not failed_payloads, f"Payloads failed: {failed_payloads}"

    def test_publish_with_valid_payloads_at_spam_rate(self):
        previous = int(time())
        for i, payload in enumerate(SAMPLE_INPUTS[:4]):
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                now = int(time())
                self.publish_message(message)
                if i > 0 and (now - previous) == 0:
                    raise AssertionError("Publish with RLN enabled at spam rate worked!!!")
                else:
                    previous = now
            except Exception as e:
                assert "RLN validation failed" in str(e)

    def test_publish_with_valid_payloads_at_alternate_rate(self):
        previous = math.trunc(time())
        for i, payload in enumerate(SAMPLE_INPUTS):
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                if (i + 1) % 2 == 1:  # every odd sample should be sent slowly
                    delay(1)
                now = math.trunc(time())
                logger.debug(f"Message sent at timestamp {now}")
                self.publish_message(message)
                if i > 0 and (now - previous) == 0:
                    raise AssertionError("Publish with RLN enabled at spam rate worked!!!")
                else:
                    previous = now
            except Exception as e:
                assert "RLN validation failed" in str(e)
