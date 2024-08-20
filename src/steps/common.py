import base64
import hashlib
import inspect
from time import time
import allure
import pytest
from tenacity import retry, stop_after_delay, wait_fixed
from src.libs.common import delay, to_base64
from src.libs.custom_logger import get_custom_logger

logger = get_custom_logger(__name__)


class StepsCommon:
    @pytest.fixture(scope="function", autouse=True)
    def common_setup(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        if not hasattr(self, "test_payload"):
            self.test_payload = "Default Payload"
        if not hasattr(self, "test_content_topic"):
            self.test_content_topic = "/test/1/default/proto"

    @allure.step
    @retry(stop=stop_after_delay(20), wait=wait_fixed(0.5), reraise=True)
    def add_node_peer(self, node, multiaddr_list, shards=[0, 1, 2, 3, 4, 5, 6, 7, 8]):
        if node.is_nwaku():
            for multiaddr in multiaddr_list:
                node.add_peers([multiaddr])
        elif node.is_gowaku():
            for multiaddr in multiaddr_list:
                peer_info = {"multiaddr": multiaddr, "protocols": ["/vac/waku/relay/2.0.0"], "shards": shards}
                node.add_peers(peer_info)

    @allure.step
    @retry(stop=stop_after_delay(70), wait=wait_fixed(1), reraise=True)
    def wait_for_autoconnection(self, node_list, hard_wait=None):
        for node in node_list:
            get_peers = node.get_peers()
            assert len(get_peers) >= 1
        if hard_wait:
            delay(hard_wait)

    @allure.step
    def create_message(self, **kwargs):
        message = {"payload": to_base64(self.test_payload), "contentTopic": self.test_content_topic, "timestamp": int(time() * 1e9)}
        message.update(kwargs)
        return message

    @allure.step
    def compute_message_hash(self, pubsub_topic, msg):
        ctx = hashlib.sha256()
        ctx.update(pubsub_topic.encode("utf-8"))
        ctx.update(base64.b64decode(msg["payload"]))
        ctx.update(msg["contentTopic"].encode("utf-8"))
        if "meta" in msg:
            ctx.update(base64.b64decode(msg["meta"]))
        ctx.update(int(msg["timestamp"]).to_bytes(8, byteorder="big"))
        hash_bytes = ctx.digest()
        return base64.b64encode(hash_bytes).decode("utf-8")
