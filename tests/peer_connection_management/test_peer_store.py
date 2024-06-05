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
                peer_id = peer_info2id(peer_info, nodes[i].is_nwaku())
                others.append(peer_id)

            assert (i == 0 and len(others) == 4) or (i > 0 and len(others) >= 1), f"Some nodes missing in the peer store of Node ID {ids[i]}"

    def test_add_peers(self):
        nodes = [self.node1, self.node2]
        nodes.extend(self.optional_nodes)

        peers_multiaddr = set()
        for i in range(2):
            for peer_info in nodes[i].get_peers():
                multiaddr = peer_info2multiaddr(peer_info, nodes[i].is_nwaku())
                peers_multiaddr.add(multiaddr)

        assert len(peers_multiaddr) == 5, f"Exactly 5 multi addresses are expected"

        # Add peers one by one excluding self for Nodes 2-5
        for i in range(1, 5):
            for peer in list(peers_multiaddr):
                if nodes[i].get_id() != multiaddr2id(peer):
                    try:
                        if nodes[i].is_nwaku():
                            nodes[i].add_peers([peer])
                        else:
                            peer_info = {"multiaddr": peer, "shards": [0], "protocols": ["/vac/waku/relay/2.0.0"]}
                            nodes[i].add_peers(peer_info)
                    except Exception as ex:
                        logger.error(f"Failed to add peer to Node {i} peer store: {ex}")
                        raise
