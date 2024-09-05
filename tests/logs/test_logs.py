from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay

logger = get_custom_logger(__name__)


class TestLogs(StepsRelay):
    def test_metadata_protocol_mounted_also_on_non_1_clusters(self, setup_main_relay_nodes):
        for node in self.main_nodes:
            metadata_protocol = "Created WakuMetadata protocol" if node.is_nwaku() else "metadata protocol started"
            assert node.search_waku_log_for_string(metadata_protocol), "Metadata protocol not mounted"
