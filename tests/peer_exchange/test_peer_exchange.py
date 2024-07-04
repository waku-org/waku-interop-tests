from src.libs.common import delay, logger
from src.node.waku_node import peer_info2multiaddr, peer_info2id, multiaddr2id
from src.steps.peer_exchange import StepsPeerExchange


class TestPeerExchange(StepsPeerExchange):
    def test_get_peers(self):
        self.setup_first_relay_node(relay_peer_exchange="true")
        self.setup_second_relay_node(peer_exchange="true")
        delay(1)
        node1_peers = self.node1.get_peers()
        assert len(node1_peers) == 1
        self.responder_multiaddr = peer_info2multiaddr(node1_peers[0], self.node1.is_nwaku())
        self.setup_peer_exchange_requester_node(discv5_discovery="false")

        node1_id = self.node1.get_id()
        node2_id = self.node2.get_id()
        others = {node1_id, node2_id}

        own = set()
        for peer_info in self.node3.get_peers():
            peer_id = multiaddr2id(peer_info2multiaddr(peer_info, self.node3.is_nwaku()))
            own.add(peer_id)

        assert own == others, f"Not all nodes found as expected in peer store of Node3"
