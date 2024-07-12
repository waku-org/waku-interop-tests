import pytest

from src.env_vars import NODE_1, NODE_2
from src.libs.common import delay
from src.libs.custom_logger import get_custom_logger
from src.node.waku_node import peer_info2id, peer_info2multiaddr, multiaddr2id
from src.steps.relay import StepsRelay
from src.steps.store import StepsStore

logger = get_custom_logger(__name__)


class TestPeerStore(StepsRelay, StepsStore):
    def test_get_peers(self):
        self.setup_main_nodes(cluster_id="0")
        self.setup_optional_nodes(cluster_id="0")
        nodes = [self.node1, self.node2]
        nodes.extend(self.optional_nodes)
        delay(1)
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
        self.setup_main_nodes(cluster_id="0")
        self.setup_optional_nodes(cluster_id="0")
        nodes = [self.node1, self.node2]
        nodes.extend(self.optional_nodes)
        delay(1)
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

    @pytest.mark.skip(reason="waiting for https://github.com/waku-org/nwaku/issues/1549 resolution")
    def test_get_peers_two_protocols(self):
        self.setup_first_publishing_node(cluster_id="0", store="true", relay="true")
        self.setup_first_store_node(cluster_id="0", store="true", relay="false")
        delay(1)
        node1_peers = self.publishing_node1.get_peers()
        node2_peers = self.store_node1.get_peers()
        logger.debug(f"Node 1 connected peers {node1_peers}")
        logger.debug(f"Node 2 connected peers {node2_peers}")

        assert len(node1_peers) == 2 and len(node2_peers) == 2, f"Some nodes and/or their services are missing"

    @pytest.mark.skip(reason="pending on https://github.com/waku-org/nwaku/issues/2792")
    @pytest.mark.skipif("go-waku" in (NODE_1 + NODE_2), reason="Test works only with nwaku")
    def test_use_persistent_storage_survive_restart(self):
        self.setup_first_relay_node(cluster_id="0", peer_persistence="true")
        self.setup_second_relay_node(cluster_id="0")
        delay(1)
        node1_peers = self.node1.get_peers()
        node2_peers = self.node2.get_peers()
        node1_id = self.node1.get_id()
        node2_id = self.node2.get_id()
        assert node1_id == peer_info2id(node2_peers[0], self.node2.is_nwaku())
        assert node2_id == peer_info2id(node1_peers[0], self.node1.is_nwaku())

        # Node 3 takes over Node 1
        self.setup_third_relay_node(peer_persistence="true")
        self.node1.kill()
        node2_peers = self.node2.get_peers()
        node3_peers = self.node3.get_peers()
        assert node1_id == peer_info2id(node2_peers[0], self.node2.is_nwaku())
        assert node2_id == peer_info2id(node3_peers[0], self.node3.is_nwaku())

    @pytest.mark.skip(reason="waiting for https://github.com/waku-org/nwaku/issues/2592 resolution")
    @pytest.mark.skipif("go-waku" in (NODE_1 + NODE_2), reason="Test works only with nwaku")
    def test_peer_store_content_after_node2_restarts(self):
        self.setup_first_relay_node(cluster_id="0")
        self.setup_second_relay_node(cluster_id="0")
        delay(1)
        node1_peers = self.node1.get_peers()
        node2_peers = self.node2.get_peers()
        assert len(node1_peers) == len(node2_peers), "Nodes should have each other in the peer store"
        self.node2.restart()
        self.node2.ensure_ready()
        delay(1)
        node1_peers = self.node1.get_peers()
        node2_peers = self.node2.get_peers()
        assert len(node1_peers) == len(node2_peers), "Nodes should have each other in the peer store"
