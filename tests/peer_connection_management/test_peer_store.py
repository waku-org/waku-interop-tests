import pytest

from src.libs.common import parse_id
from src.libs.custom_logger import get_custom_logger
from src.steps.relay import StepsRelay

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("setup_main_relay_nodes", "setup_optional_relay_nodes")
class TestPeerStore(StepsRelay):
    def test_get_peers(self):
        nodes = [self.node1, self.node2]
        nodes.extend(self.optional_nodes)
        ids = []
        for node in nodes:
            node_id = node.get_id()
            ids.append(node_id)

        for i in range(5):
            others = []
            for peer_info in nodes[i].get_peers():
                others.append(parse_id(peer_info))

            assert (i == 0 and len(others) == 4) or (i > 0 and len(others) == 1), f"Some nodes missing in the peer store of node {ids[i]}"
