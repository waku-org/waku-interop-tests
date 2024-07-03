from src.env_vars import NODE_2
from src.node.waku_node import WakuNode

import allure

from src.steps.relay import StepsRelay


class StepsPeerExchange(StepsRelay):
    responder_multiaddr = ""

    @allure.step
    def setup_peer_exchange_requester_node(self, **kwargs):
        self.node3 = WakuNode(NODE_2, f"node3_{self.test_id}")
        self.node3.start(
            relay="true",
            peer_exchange_node=self.responder_multiaddr,
            **kwargs,
        )
        self.add_node_peer(self.node3, [self.multiaddr_with_id])
        self.main_nodes.extend([self.node3])
