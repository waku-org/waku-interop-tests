import os
import pytest
from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("register_rln_main_relay_nodes")
class TestRelayRLN(StepsRelay):
    def test_register_rln(self):
        logger.debug(f"Running register RLN test for main relay nodes")
        key_stores_found = 0
        for k in range(1, 3):
            keystore_path = "/keystore_{k}/keystore.json"
            if os.path.exists(keystore_path):
                key_stores_found += 1

        assert key_stores_found == 2, f"Invalid number of RLN keystores found, expected 2 found {key_stores_found}"
