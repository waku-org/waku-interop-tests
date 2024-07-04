from src.libs.common import delay, logger
from src.node.waku_node import peer_info2multiaddr
from src.steps.peer_exchange import StepsPeerExchange


class TestPeerExchange(StepsPeerExchange):
    def test_get_peers(self):
        self.setup_first_relay_node(relay_peer_exchange="true")
        self.setup_second_relay_node(peer_exchange="true")
        delay(1)
        node1_peers = self.node1.get_peers()
        assert len(node1_peers) == 1
        logger.debug(f"Node 1 connected peers {node1_peers}")
        self.responder_multiaddr = peer_info2multiaddr(node1_peers[0], self.node1.is_nwaku())
        logger.debug(f"Node 2 multiaddr {self.responder_multiaddr}")
        self.setup_peer_exchange_requester_node()
