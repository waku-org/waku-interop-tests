from src.libs.common import delay
from src.steps.light_push import StepsLightPush


class TestRunningNodes(StepsLightPush):
    def test_main_node_only_lightpush__peer_only_lightpush(self):
        self.setup_first_receiving_node(lightpush="true", relay="false")
        self.setup_first_lightpush_node(lightpush="true", relay="false")
        try:
            self.light_push_node1.send_light_push_message(self.create_payload())
            raise AssertionError("Light push with non lightpush peer worked!!!")
        except Exception as ex:
            assert "Failed to request a message push: no waku relay found" in str(ex) or "timed out" in str(ex)

    def test_main_node_only_lightpush__peer_only_filter(self):
        self.setup_first_receiving_node(lightpush="false", relay="false", filter="true")
        self.setup_first_lightpush_node(lightpush="true", relay="false")
        try:
            self.light_push_node1.send_light_push_message(self.create_payload())
            raise AssertionError("Light push with non lightpush peer worked!!!")
        except Exception as ex:
            assert "Failed to request a message push: dial_failure" in str(ex) or "timed out" in str(ex)

    def test_main_node_only_lightpush__peer_only_relay(self):
        self.setup_first_receiving_node(lightpush="false", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.setup_first_lightpush_node(lightpush="true", relay="false")
        try:
            self.light_push_node1.send_light_push_message(self.create_payload())
            raise AssertionError("Light push with non lightpush peer worked!!!")
        except Exception as ex:
            assert "Failed to request a message push: dial_failure" in str(ex) or "timed out" in str(ex)

    def test_main_node_only_lightpush__peer_full(self):
        self.setup_first_receiving_node(lightpush="true", relay="true", filter="true")
        self.setup_first_lightpush_node(lightpush="true", relay="false")
        self.subscribe_to_pubsub_topics_via_relay()
        self.check_light_pushed_message_reaches_receiving_peer()

    def test_main_node_full__peer_full(self):
        self.setup_first_receiving_node(lightpush="true", relay="true", filter="true")
        self.setup_first_lightpush_node(lightpush="true", relay="true", filter="true")
        self.subscribe_to_pubsub_topics_via_relay()
        self.check_light_pushed_message_reaches_receiving_peer()

    def test_lightpush_node_with_relay_works_correctly(self):
        self.test_main_node_full__peer_full()
        self.light_push_node1.send_relay_message(self.create_message(), self.test_pubsub_topic)
        self.receiving_node1.send_relay_message(self.create_message(), self.test_pubsub_topic)
        delay(0.1)
        response1 = self.receiving_node1.get_relay_messages(self.test_pubsub_topic)
        assert len(response1) == 2
        response2 = self.light_push_node1.get_relay_messages(self.test_pubsub_topic)
        assert len(response2) == 2
