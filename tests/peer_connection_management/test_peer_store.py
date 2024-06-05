import pytest

from src.libs.common import peer_info2id, peer_info2multiaddr, multiaddr2id
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
                others.append(peer_info2id(peer_info))

            assert (i == 0 and len(others) == 4) or (i > 0 and len(others) == 1), f"Some nodes missing in the peer store of Node ID {ids[i]}"

    def test_add_peers(self):
        nodes = [self.node1, self.node2]
        nodes.extend(self.optional_nodes)

        # Get peers 1-4
        peers_info = nodes[0].get_peers()
        assert len(peers_info) == 4, f"Some nodes missing in the peer store of Node 1"

        # Get peer 0
        peers_info.extend(nodes[1].get_peers())
        assert len(peers_info) == 5, f"Node 1 missing in the peer store of Node 2"

        # Convert to multi addresses
        peers_multiaddr = []
        for peer in peers_info:
            multiaddr = peer_info2multiaddr(peer)
            logger.debug(f"Peer info {peer}")
            logger.debug(f"Peer multi address {multiaddr}")
            peers_multiaddr.append(multiaddr)

        # Add peers one by one excluding self for Nodes 2-5
        for i in range(1, 5):
            for peer in peers_multiaddr:
                if nodes[i].get_id() != multiaddr2id(peer):
                    try:
                        nodes[i].add_peers([peer])
                    except Exception as ex:
                        logger.error(f"Failed to add peer to Node {i} peer store: {ex}")
                        raise
