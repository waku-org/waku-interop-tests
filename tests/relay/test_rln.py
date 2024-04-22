import math
import random
from time import time

import pytest

from src.libs.common import delay, to_base64
from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay
from src.steps.rln import StepsRLN
from src.test_data import SAMPLE_INPUTS

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("register_main_rln_relay_nodes")
class TestRelayRLN(StepsRLN, StepsRelay):
    def test_publish_with_valid_payloads_at_slow_rate(self):
        self.setup_first_rln_relay_node()
        self.setup_second_rln_relay_node()
        self.subscribe_main_relay_nodes()
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
        self.setup_first_rln_relay_node()
        self.setup_second_rln_relay_node()
        self.subscribe_main_relay_nodes()
        previous = math.trunc(time())
        for i, payload in enumerate(SAMPLE_INPUTS[:4]):
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                now = math.trunc(time())
                self.publish_message(message)
                if i > 0 and (now - previous) == 0:
                    raise AssertionError("Publish with RLN enabled at spam rate worked!!!")
                else:
                    previous = now
            except Exception as e:
                assert "RLN validation failed" in str(e)

    @pytest.mark.skip(reason="flaky because of problems with time measurement")
    def test_publish_with_valid_payloads_at_variable_rate(self):
        self.setup_first_rln_relay_node()
        self.setup_second_rln_relay_node()
        self.subscribe_main_relay_nodes()
        previous = math.trunc(time())
        for i, payload in enumerate(SAMPLE_INPUTS):
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                if i % 2 == 1:  # every sample with odd index is sent slowly
                    delay(1 + 1)
                now = math.trunc(time())
                logger.debug(f"Message sent at timestamp {now}")
                self.publish_message(message)
                if i > 0 and (now - previous) == 0:
                    raise AssertionError("Publish with RLN enabled at spam rate worked!!!")
                else:
                    previous = now
            except Exception as e:
                assert "RLN validation failed" in str(e)

    def test_publish_with_valid_payloads_random_epoch_at_slow_rate(self):
        epoch_sec = random.randint(2, 5)
        self.setup_first_rln_relay_node(rln_relay_epoch_sec=epoch_sec)
        self.setup_second_rln_relay_node(rln_relay_epoch_sec=epoch_sec)
        self.subscribe_main_relay_nodes()
        failed_payloads = []
        for payload in SAMPLE_INPUTS[:5]:
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                self.publish_message(message)
            except Exception as e:
                logger.error(f'Payload {payload["description"]} failed: {str(e)}')
                failed_payloads.append(payload["description"])
            delay(epoch_sec)
            assert not failed_payloads, f"Payloads failed: {failed_payloads}"

    @pytest.mark.skip(reason="waiting for RLN v2 implementation")
    def test_publish_with_valid_payloads_random_user_message_limit(self):
        user_message_limit = random.randint(2, 4)
        self.setup_first_rln_relay_node(rln_relay_user_message_limit=user_message_limit)
        self.setup_second_rln_relay_node(rln_relay_user_message_limit=user_message_limit)
        self.subscribe_main_relay_nodes()
        failed_payloads = []
        for payload in SAMPLE_INPUTS[:user_message_limit]:
            logger.debug(f'Running test with payload {payload["description"]}')
            message = self.create_message(payload=to_base64(payload["value"]))
            try:
                self.publish_message(message)
            except Exception as e:
                logger.error(f'Payload {payload["description"]} failed: {str(e)}')
                failed_payloads.append(payload["description"])
            assert not failed_payloads, f"Payloads failed: {failed_payloads}"

    @pytest.mark.skip(reason="pending on https://github.com/waku-org/nwaku/issues/2606")
    def test_publish_with_valid_payloads_dynamic_at_slow_rate(self):
        self.setup_first_rln_relay_node(rln_relay_dynamic="true")
        self.setup_second_rln_relay_node(rln_relay_dynamic="true")
        self.subscribe_main_relay_nodes()
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
