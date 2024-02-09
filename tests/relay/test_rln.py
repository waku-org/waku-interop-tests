import os
import pytest

from src.env_vars import RLN_CREDENTIALS
from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures()
class TestRelayRLN(StepsRelay):
    def test_register_rln(self):
        logger.debug(f"Running register RLN test for main relay nodes")
        key_stores_found = 0

        if RLN_CREDENTIALS is None:
            pytest.skip("RLN_CREDENTIALS not set, skipping test")

        for k in range(1, 6):
            self.register_rln_single_node(rln_creds_source=RLN_CREDENTIALS, rln_creds_id=f"{k}")
            self.check_rln_registration(k)
            key_stores_found += 1
        assert key_stores_found == 5, f"Invalid number of RLN keystores found, expected 2 found {key_stores_found}"
