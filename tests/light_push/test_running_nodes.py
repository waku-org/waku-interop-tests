import pytest
from src.env_vars import NODE_2
from src.libs.custom_logger import get_custom_logger
from time import sleep, time
from src.libs.common import delay, to_base64
from src.steps.light_push import StepsLightPush
from src.test_data import INVALID_CONTENT_TOPICS, INVALID_PAYLOADS, PUBSUB_TOPICS_WRONG_FORMAT, SAMPLE_INPUTS, SAMPLE_TIMESTAMPS, VALID_PUBSUB_TOPICS

logger = get_custom_logger(__name__)


# node1 only lightpush - node2 only filter
# node1 only lightpush - node2 only relay
# node1 only lightpush - node2 lightpush + filter
# node1 only lightpush - node2 lightpush + relay
# node1 only lightpush - node2 all

# node1 only lightpush + relay - node2 only filter
# node1 only lightpush + relay - node2 only relay
# node1 only lightpush + relay - node2 filter + relay
# node1 only lightpush + relay - node2 lightpush + filter
# node1 only lightpush + relay - node2 lightpush + relay
# node1 only lightpush + relay - node2 all

# node1 only lightpush + filter - node2 only filter
# node1 only lightpush + filter - node2 only relay
# node1 only lightpush + filter - node2 filter + relay
# node1 only lightpush + filter - node2 lightpush + filter
# node1 only lightpush + filter - node2 lightpush + relay
# node1 only lightpush + filter - node2 all

# node1 only all - node2 only filter
# node1 only all - node2 only relay
# node1 only all - node2 filter + relay
# node1 only all - node2 lightpush + filter
# node1 only all - node2 lightpush + relay
# node1 only all - node2 all


class TestRunningNodes(StepsLightPush):
    def test_main_node_only_lightpush__peer_only_lightpush(self):
        self.setup_first_receiving_node(lightpush="true", relay="false")
        self.setup_lightpush_node(lightpush="true", relay="false")
        try:
            self.light_push_node.send_light_push_message(self.create_payload())
            raise AssertionError("Light push with non lightpush peer worked!!!")
        except Exception as ex:
            assert "Failed to request a message push: no waku relay found" in str(ex) or "timed out" in str(ex)

    def test_main_node_only_lightpush__peer_only_filter(self):
        self.setup_first_receiving_node(lightpush="false", relay="false", filter="true")
        self.setup_lightpush_node(lightpush="true", relay="false")
        try:
            self.light_push_node.send_light_push_message(self.create_payload())
            raise AssertionError("Light push with non lightpush peer worked!!!")
        except Exception as ex:
            assert "Failed to request a message push: dial_failure" in str(ex) or "timed out" in str(ex)

    def test_main_node_only_lightpush__peer_only_relay(self):
        self.setup_first_receiving_node(lightpush="false", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.setup_lightpush_node(lightpush="true", relay="false")
        try:
            self.light_push_node.send_light_push_message(self.create_payload())
            raise AssertionError("Light push with non lightpush peer worked!!!")
        except Exception as ex:
            assert "Failed to request a message push: dial_failure" in str(ex) or "timed out" in str(ex)

    def test_main_node_only_lightpush__peer_full(self):
        self.setup_first_receiving_node(lightpush="true", relay="true", filter="true")
        self.setup_lightpush_node(lightpush="true", relay="false")
        self.subscribe_to_pubsub_topics_via_relay()
        self.check_light_pushed_message_reaches_receiving_peer()

    def test_main_node_full__peer_full(self):
        self.setup_first_receiving_node(lightpush="true", relay="true", filter="true")
        self.setup_lightpush_node(lightpush="true", relay="true", filter="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.check_light_pushed_message_reaches_receiving_peer()

    def test_multiple_lightpush_nodes(self):
        self.setup_first_receiving_node(lightpush="true", relay="true")
        self.setup_lightpush_node(lightpush="true", relay="false")
        self.setup_second_lightpush_node(lightpush="true", relay="false")
        self.subscribe_to_pubsub_topics_via_relay()
        self.check_light_pushed_message_reaches_receiving_peer(sender=self.light_push_node)
        self.check_light_pushed_message_reaches_receiving_peer(sender=self.light_push_node2)

    def test_multiple_receiving_nodes__relay_node1_forwards_lightpushed_message_to_relay_node2(self):
        self.setup_first_receiving_node(lightpush="true", relay="true")
        self.setup_second_receiving_node(lightpush="false", relay="true")
        self.setup_lightpush_node(lightpush="true", relay="false")
        self.subscribe_to_pubsub_topics_via_relay()
        self.check_light_pushed_message_reaches_receiving_peer(sender=self.light_push_node)

    def test_multiple_receiving_nodes__relay_node1_forwards_lightpushed_message_to_filter_node2(self):
        self.setup_first_receiving_node(lightpush="true", relay="true", filter="true")
        self.setup_second_receiving_node(lightpush="false", relay="false", filternode=self.receiving_node1.get_multiaddr_with_id())
        self.setup_lightpush_node(lightpush="true", relay="false")
        self.subscribe_to_pubsub_topics_via_relay(node=self.receiving_node1)
        self.subscribe_to_pubsub_topics_via_filter(node=self.receiving_node2)
        self.check_light_pushed_message_reaches_receiving_peer(sender=self.light_push_node)
        get_messages_response = self.receiving_node2.get_filter_messages(self.test_content_topic)
        assert len(get_messages_response) == 1, "Lightpushed message was not relayed to the filter node"
