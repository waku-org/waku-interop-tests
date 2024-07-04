from uuid import uuid4

from src.env_vars import NODE_2
from src.node.waku_node import WakuNode

import allure

from src.steps.relay import StepsRelay


class StepsPeerExchange(StepsRelay):
    responder_multiaddr = ""

    @allure.step
    def setup_third_node_as_peer_exchange_requester(self, **kwargs):
        self.node3 = WakuNode(NODE_2, f"node3_{self.test_id}")
        self.node3.start(
            relay="true",
            peer_exchange_node=self.responder_multiaddr,
            **kwargs,
        )
        self.add_node_peer(self.node3, [self.multiaddr_with_id])
        self.main_nodes.extend([self.node3])

    @allure.step
    def setup_fourth_node_as_filter(self, **kwargs):
        self.node4 = WakuNode(NODE_2, f"node4_{self.test_id}")
        self.node4.start(relay="false", **kwargs)
        self.add_node_peer(self.node4, [self.multiaddr_with_id])
        self.main_nodes.extend([self.node4])
