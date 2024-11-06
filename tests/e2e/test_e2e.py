import pytest
from src.env_vars import NODE_1, NODE_2
from src.libs.common import delay
from src.libs.custom_logger import get_custom_logger
from src.node.waku_node import WakuNode
from src.steps.filter import StepsFilter
from src.steps.light_push import StepsLightPush
from src.steps.relay import StepsRelay
from src.steps.store import StepsStore

logger = get_custom_logger(__name__)

"""
In those tests we aim to combine multiple protocols/node types and create a more end-to-end scenario
"""


class TestE2E(StepsFilter, StepsStore, StepsRelay, StepsLightPush):
    @pytest.fixture(scope="function", autouse=True)
    def nodes(self):
        self.node1 = WakuNode(NODE_2, f"node1_{self.test_id}")
        self.node2 = WakuNode(NODE_1, f"node2_{self.test_id}")
        self.node3 = WakuNode(NODE_2, f"node3_{self.test_id}")

    def test_relay_receiving_node_not_connected_directly_to_relaying_node(self):
        self.node1.start(relay="true")
        self.node2.start(relay="true", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="true", discv5_bootstrap_node=self.node2.get_enr_uri())

        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])
        self.node3.set_relay_subscriptions([self.test_pubsub_topic])

        # for e2e scenarios I think waiting for autoconnection is important instead of forcing connection via API calls
        # that's why the bellow code is commented to showcase this difference. In case we uncomment it, the connection will be faster
        # self.add_node_peer(self.node2, [self.node1.get_multiaddr_with_id()])
        # self.add_node_peer(self.node3, [self.node2.get_multiaddr_with_id()])
        self.wait_for_autoconnection([self.node1, self.node2, self.node3], hard_wait=30)

        # self.node1 relays and we check that self.node3 receives the message
        self.check_published_message_reaches_relay_peer(sender=self.node1, peer_list=[self.node3], message_propagation_delay=1)

    def test_filter_node_not_connected_directly_to_relaying_node(self):
        self.node1.start(filter="true", relay="true")
        self.node2.start(filter="true", relay="true", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="false", filternode=self.node2.get_multiaddr_with_id(), discv5_bootstrap_node=self.node2.get_enr_uri())

        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])
        self.node3.set_filter_subscriptions({"requestId": "1", "contentFilters": [self.test_content_topic], "pubsubTopic": self.test_pubsub_topic})

        # for e2e scenarios I think waiting for autoconnection is important instead of forcing connection via API calls
        # that's why the bellow code is commented to showcase this difference. In case we uncomment it, the connection will be faster
        # self.add_node_peer(self.node2, [self.node1.get_multiaddr_with_id()])
        # self.add_node_peer(self.node3, [self.node2.get_multiaddr_with_id()])
        self.wait_for_autoconnection([self.node1, self.node2, self.node3], hard_wait=30)

        # self.node1 relays and we check that self.node3 receives the message
        self.check_published_message_reaches_filter_peer(sender=self.node1, peer_list=[self.node3], message_propagation_delay=1)

    def test_store_node_not_connected_directly_to_relaying_node(self):
        self.node1.start(relay="true")
        self.node2.start(store="true", relay="true", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="false", storenode=self.node2.get_multiaddr_with_id(), discv5_bootstrap_node=self.node2.get_enr_uri())

        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])
        # self.node1 relays and we check that self.node3 receives the message

        # for e2e scenarios I think waiting for autoconnection is important instead of forcing connection via API calls
        # that's why the bellow code is commented to showcase this difference. In case we uncomment it, the connection will be faster
        # self.add_node_peer(self.node2, [self.node1.get_multiaddr_with_id()])
        # self.add_node_peer(self.node3, [self.node2.get_multiaddr_with_id()])
        self.wait_for_autoconnection([self.node1, self.node2], hard_wait=30)

        self.publish_message(sender=self.node1)
        self.check_published_message_is_stored(page_size=50, ascending="true", store_node=self.node3)

    def test_relay_receiving_node_not_connected_directly_to_lightpushing_node(self):
        self.node1.start(lightpush="true", relay="true")
        self.node2.start(
            lightpush="true", relay="true", discv5_bootstrap_node=self.node1.get_enr_uri(), lightpushnode=self.node1.get_multiaddr_with_id()
        )
        self.node3.start(relay="true", discv5_bootstrap_node=self.node2.get_enr_uri())

        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])
        self.node3.set_relay_subscriptions([self.test_pubsub_topic])

        # for e2e scenarios I think waiting for autoconnection is important instead of forcing connection via API calls
        # that's why the bellow code is commented to showcase this difference. In case we uncomment it, the connection will be faster
        # self.add_node_peer(self.node2, [self.node1.get_multiaddr_with_id()])
        # self.add_node_peer(self.node3, [self.node2.get_multiaddr_with_id()])
        self.wait_for_autoconnection([self.node1, self.node2, self.node3], hard_wait=30)

        # self.node1 light pushed and we check that self.node3 receives the message
        self.check_light_pushed_message_reaches_receiving_peer(sender=self.node1, peer_list=[self.node3])

    def test_filter_node_not_connected_directly_to_lightpushing_node(self):
        self.node1.start(lightpush="true")
        self.node2.start(
            lightpush="true",
            filter="true",
            relay="true",
            discv5_bootstrap_node=self.node1.get_enr_uri(),
            lightpushnode=self.node1.get_multiaddr_with_id(),
        )
        self.node3.start(relay="false", filternode=self.node2.get_multiaddr_with_id(), discv5_bootstrap_node=self.node2.get_enr_uri())

        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])
        self.node3.set_filter_subscriptions({"requestId": "1", "contentFilters": [self.test_content_topic], "pubsubTopic": self.test_pubsub_topic})

        # for e2e scenarios I think waiting for autoconnection is important instead of forcing connection via API calls
        # that's why the bellow code is commented to showcase this difference. In case we uncomment it, the connection will be faster
        # self.add_node_peer(self.node2, [self.node1.get_multiaddr_with_id()])
        # self.add_node_peer(self.node3, [self.node2.get_multiaddr_with_id()])
        self.wait_for_autoconnection([self.node1, self.node2, self.node3], hard_wait=30)

        # self.node1 light pushed and we check that self.node3 receives the message
        self.node1.send_light_push_message(self.create_payload())
        delay(1)
        get_messages_response = self.get_filter_messages(self.test_content_topic, pubsub_topic=self.test_pubsub_topic, node=self.node3)
        assert len(get_messages_response) == 1, f"Expected 1 message but got {len(get_messages_response)}"

    def test_store_node_not_connected_directly_to_lightpushing_node(self):
        self.node1.start(lightpush="true")
        self.node2.start(
            lightpush="true",
            store="true",
            relay="true",
            discv5_bootstrap_node=self.node1.get_enr_uri(),
            lightpushnode=self.node1.get_multiaddr_with_id(),
        )
        self.node3.start(relay="false", storenode=self.node2.get_multiaddr_with_id(), discv5_bootstrap_node=self.node2.get_enr_uri())

        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])

        # for e2e scenarios I think waiting for autoconnection is important instead of forcing connection via API calls
        # that's why the bellow code is commented to showcase this difference. In case we uncomment it, the connection will be faster
        # self.add_node_peer(self.node2, [self.node1.get_multiaddr_with_id()])
        # self.add_node_peer(self.node3, [self.node2.get_multiaddr_with_id()])
        self.wait_for_autoconnection([self.node1, self.node2], hard_wait=30)

        # self.node1 light pushed and we check that self.node3 receives the message
        message = self.create_message()
        self.node1.send_light_push_message(self.create_payload(message=message))
        delay(1)
        self.check_published_message_is_stored(page_size=50, ascending="true", store_node=self.node3, messages_to_check=[message])

    def test_chain_of_relay_nodes(self):
        self.node4 = WakuNode(NODE_2, f"node4_{self.test_id}")
        self.node5 = WakuNode(NODE_2, f"node5_{self.test_id}")
        self.node6 = WakuNode(NODE_2, f"node6_{self.test_id}")
        self.node7 = WakuNode(NODE_2, f"node7_{self.test_id}")
        self.node8 = WakuNode(NODE_2, f"node8_{self.test_id}")
        self.node9 = WakuNode(NODE_2, f"node9_{self.test_id}")
        self.node10 = WakuNode(NODE_2, f"node10_{self.test_id}")

        self.node1.start(relay="true")
        self.node2.start(relay="true", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="true", discv5_bootstrap_node=self.node2.get_enr_uri())
        self.node4.start(relay="true", discv5_bootstrap_node=self.node3.get_enr_uri())
        self.node5.start(relay="true", discv5_bootstrap_node=self.node4.get_enr_uri())
        self.node6.start(relay="true", discv5_bootstrap_node=self.node5.get_enr_uri())
        self.node7.start(relay="true", discv5_bootstrap_node=self.node6.get_enr_uri())
        self.node8.start(relay="true", discv5_bootstrap_node=self.node7.get_enr_uri())
        self.node9.start(relay="true", discv5_bootstrap_node=self.node8.get_enr_uri())
        self.node10.start(relay="true", discv5_bootstrap_node=self.node9.get_enr_uri())

        node_list = [self.node1, self.node2, self.node3, self.node4, self.node5, self.node6, self.node7, self.node8, self.node9, self.node10]
        for node in node_list:
            node.set_relay_subscriptions([self.test_pubsub_topic])

        self.wait_for_autoconnection(node_list, hard_wait=30)

        # self.node1 relays and we check that self.node10 receives the message
        self.check_published_message_reaches_relay_peer(sender=self.node1, peer_list=[self.node10], message_propagation_delay=1)

    @pytest.mark.skipif("go-waku" in NODE_2, reason="Test works only with nwaku")
    def test_store_filter_interaction_with_six_nodes(self):
        logger.debug("Create  6 nodes")
        self.node4 = WakuNode(NODE_2, f"node3_{self.test_id}")
        self.node5 = WakuNode(NODE_2, f"node3_{self.test_id}")
        self.node6 = WakuNode(NODE_2, f"node3_{self.test_id}")

        logger.debug("Start 5 nodes with their corresponding config")
        self.node1.start(relay="true", store="true")
        self.node2.start(relay="true", store="true", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="true", store="true", discv5_bootstrap_node=self.node2.get_enr_uri())
        self.node4.start(relay="true", filter="true", store="true", discv5_bootstrap_node=self.node3.get_enr_uri())
        self.node6.start(relay="false", filter="true", filternode=self.node4.get_multiaddr_with_id())

        logger.debug("Subscribe nodes to relay  pubsub topics")
        node_list = [self.node1, self.node2, self.node3, self.node4]
        for node in node_list:
            node.set_relay_subscriptions([self.test_pubsub_topic])

        logger.debug("Wait for all nodes auto connection")
        self.wait_for_autoconnection(node_list, hard_wait=30)

        logger.debug(f"Node6 subscribe to filter for pubsubtopic {self.test_pubsub_topic}")
        self.node6.set_filter_subscriptions({"requestId": "1", "contentFilters": [self.test_content_topic], "pubsubTopic": self.test_pubsub_topic})

        logger.debug(f"Node1 publish message for topic {self.test_pubsub_topic}")
        message = self.create_message()
        self.publish_message(sender=self.node1, pubsub_topic=self.test_pubsub_topic, message=message)
        delay(5)

        logger.debug(f"Node6 inquery for filter messages on pubsubtopic {self.test_pubsub_topic} & contenttopic{self.test_content_topic}")
        messages_response = self.get_filter_messages(self.test_content_topic, pubsub_topic=self.test_pubsub_topic, node=self.node6)
        logger.debug(f"Filter inquiry response is {messages_response}")
        assert len(messages_response) == 1, f"filtered messages count doesn't match published messages"

        logger.debug("Node5 goes live !!")
        self.node5.start(relay="false", storenode=self.node4.get_multiaddr_with_id(), discv5_bootstrap_node=self.node4.get_enr_uri())
        delay(2)
        logger.debug("Node5 makes request to get stored messages ")
        self.check_published_message_is_stored(page_size=50, ascending="true", store_node=self.node5, messages_to_check=[message])

    @pytest.mark.skipif("go-waku" in NODE_2, reason="Test works only with nwaku")
    def test_repeated_filter_requestID(self):
        logger.debug("Create 3 nodes")
        logger.debug("Start 3 nodes with their corresponding config")
        self.node1.start(relay="true", store="true")
        self.node2.start(relay="true", store="true", filter="true", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="true", filternode=self.node2.get_multiaddr_with_id(), store="false", discv5_bootstrap_node=self.node2.get_enr_uri())

        logger.debug("Subscribe nodes to relay  pubsub topics")
        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])

        logger.debug("Wait for all nodes auto connection")
        node_list = [self.node1, self.node2]
        self.wait_for_autoconnection(node_list, hard_wait=30)

        logger.debug(f"Node3 subscribe to filter for pubsubtopic  {self.test_pubsub_topic} 2 times with same request id")
        self.node3.set_filter_subscriptions({"requestId": "1", "contentFilters": [self.test_content_topic], "pubsubTopic": self.test_pubsub_topic})
        self.node3.set_filter_subscriptions({"requestId": "1", "contentFilters": [self.test_content_topic], "pubsubTopic": self.test_pubsub_topic})

        logger.debug(f"Node1 publish message for topic {self.test_pubsub_topic}")
        self.publish_message(sender=self.node1, pubsub_topic=self.test_pubsub_topic, message=self.create_message())
        delay(5)
        messages_response = self.get_filter_messages(self.test_content_topic, pubsub_topic=self.test_pubsub_topic, node=self.node6)
        logger.debug(f"Response for node 6 is {messages_response}")
        assert len(messages_response) == 1, f"filtered messages count doesn't match published messages"
        messages_response = self.get_filter_messages(self.test_content_topic, pubsub_topic=self.test_pubsub_topic, node=self.node6)
        logger.debug(f"Respoense for node6 using same request ID is {messages_response}")
        # note: additional steps will be added to test the correct expected response on sending 2 requests with same ID

    def test_msg_not_stored_when_ephemeral_true(self):
        logger.debug("Start 3 nodes ")
        self.node1.start(relay="true", store="true")
        self.node2.start(store="true", relay="true", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="false", storenode=self.node2.get_multiaddr_with_id(), discv5_bootstrap_node=self.node2.get_enr_uri())

        logger.debug(f"Subscribe node1 ,2 to pubtopic {self.test_pubsub_topic}")
        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])
        self.wait_for_autoconnection([self.node1, self.node2], hard_wait=30)

        logger.debug("Node1 publish message with flag ephemeral = True")
        message = self.create_message(ephemeral=True)
        self.publish_message(sender=self.node1, pubsub_topic=self.test_pubsub_topic, message=message)
        delay(3)
        try:
            logger.debug("Node3 makes store request to get messages")
            self.check_published_message_is_stored(page_size=50, ascending="true", store_node=self.node3, messages_to_check=[message])
            raise Exception("Messages shouldn't be stores when ephemeral = true")
        except Exception as e:
            logger.debug(f"Response for store when ephemeral = true is str{e}")
            assert e.args[0].find("'messages': []"), "response for store shouldn't contain messages"
            logger.debug("Message isn't stored as ephemeral = True")

    @pytest.mark.skipif("go-waku" in NODE_2, reason="Test works only with nwaku")
    def test_msg_stored_when_ephemeral_false(self):
        logger.debug("Start 3 nodes")
        self.node1.start(relay="true", store="true")
        self.node2.start(store="true", relay="true", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="false", storenode=self.node2.get_multiaddr_with_id(), discv5_bootstrap_node=self.node2.get_enr_uri())

        logger.debug(f"Subscribe node1 ,2 to pubtopic {self.test_pubsub_topic}")
        self.node1.set_relay_subscriptions([self.test_pubsub_topic])
        self.node2.set_relay_subscriptions([self.test_pubsub_topic])
        self.wait_for_autoconnection([self.node1, self.node2], hard_wait=30)

        logger.debug("Node1 publish message with ephemeral = false")
        message = self.create_message(ephemeral=False)
        self.publish_message(sender=self.node1, pubsub_topic=self.test_pubsub_topic, message=message)
        delay(3)
        logger.debug("Check if message is stored")
        self.check_published_message_is_stored(page_size=50, ascending="true", store_node=self.node3, messages_to_check=[message])
