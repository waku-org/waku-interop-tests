import allure
from tenacity import retry, stop_after_delay, wait_fixed


class StepsCommon:
    @allure.step
    @retry(stop=stop_after_delay(6), wait=wait_fixed(0.5), reraise=True)
    def add_node_peer(self, node, multiaddr_list, shards=[0, 1, 2, 3, 4, 5, 6, 7, 8]):
        if node.is_nwaku():
            for multiaddr in multiaddr_list:
                node.add_peers([multiaddr])
        elif node.is_gowaku():
            for multiaddr in multiaddr_list:
                peer_info = {"multiaddr": multiaddr, "protocols": ["/vac/waku/relay/2.0.0"], "shards": shards}
                node.add_peers(peer_info)
