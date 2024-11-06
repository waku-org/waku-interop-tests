import pytest
from src.env_vars import NODE_1, NODE_2, STRESS_ENABLED
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

    @pytest.mark.timeout(60 * 5)
    def test_filter_30_senders_1_receiver(self):
        total_senders = 30
        node_list = []

        logger.debug(f"Start {total_senders} nodes to publish messages ")
        self.node1.start(relay="true")
        node_list.append(self.node1)
        for i in range(total_senders - 1):
            node_list.append(WakuNode(NODE_1, f"node{i + 1}_{self.test_id}"))
            delay(0.1)
            node_list[i + 1].start(relay="true", discv5_bootstrap_node=node_list[i].get_enr_uri())
            delay(2)

        logger.debug(f"Start filter node and subscribed filter node ")
        self.node31 = WakuNode(NODE_2, f"node31_{self.test_id}")
        self.node32 = WakuNode(NODE_2, f"node32_{self.test_id}")
        self.node31.start(relay="true", filter="true", store="false", discv5_bootstrap_node=node_list[total_senders - 1].get_enr_uri())
        self.node32.start(relay="false", filter="true", filternode=self.node31.get_multiaddr_with_id(), store="false")

        node_list.append(self.node31)

        logger.debug(f"Subscribe nodes to relay  pubsub topic {self.test_pubsub_topic}")
        for node in node_list:
            node.set_relay_subscriptions([self.test_pubsub_topic])
        self.wait_for_autoconnection(node_list, hard_wait=50)

        logger.debug(f"Node32 make filter request to pubsubtopic {self.test_pubsub_topic} and content topic  {self.test_content_topic}")
        self.node32.set_filter_subscriptions({"requestId": "1", "contentFilters": [self.test_content_topic], "pubsubTopic": self.test_pubsub_topic})
        delay(1)

        logger.debug(f"{total_senders} Nodes publish {total_senders} messages")
        for node in node_list[:-1]:
            self.publish_message(sender=node, pubsub_topic=self.test_pubsub_topic, message=self.create_message())
            delay(1)

        logger.debug("Node 32 requests messages of subscribed filter topic")
        messages_response = self.get_filter_messages(self.test_content_topic, pubsub_topic=self.test_pubsub_topic, node=self.node32)

        logger.debug(f"Total number received messages for node 32 is {len(messages_response)}")
        assert len(messages_response) == total_senders, f"Received messages != published which is {total_senders} !!"

    def test_filter_3_senders_45_msg_1_receiver(self):
        messages_num = 45
        total_senders = 3
        self.node4 = WakuNode(NODE_2, f"node3_{self.test_id}")
        self.node5 = WakuNode(NODE_2, f"node3_{self.test_id}")
        node_list = []

        logger.debug("Start 5 nodes")
        self.node1.start(relay="true", store="true")
        self.node2.start(relay="true", store="false", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node3.start(relay="true", store="true", filter="true", discv5_bootstrap_node=self.node2.get_enr_uri())
        self.node4.start(relay="true", filter="true", store="false", discv5_bootstrap_node=self.node1.get_enr_uri())
        self.node5.start(
            relay="false", filter="true", filternode=self.node4.get_multiaddr_with_id(), store="false", discv5_bootstrap_node=self.node3.get_enr_uri()
        )

        logger.debug(f"Subscribe nodes to relay  pubsub topic {self.test_pubsub_topic}")
        node_list = [self.node1, self.node2, self.node3, self.node4]
        for node in node_list:
            node.set_relay_subscriptions([self.test_pubsub_topic])
        self.wait_for_autoconnection(node_list, hard_wait=30)

        logger.debug(f"Node5 makes filter request pubsubtopic {self.test_pubsub_topic} and content topic {self.test_content_topic}")
        self.node5.set_filter_subscriptions({"requestId": "1", "contentFilters": [self.test_content_topic], "pubsubTopic": self.test_pubsub_topic})
        delay(1)

        logger.debug(f" {total_senders} Nodes publish {messages_num} message")
        for node in node_list[:-1]:
            for i in range(messages_num // total_senders):
                self.publish_message(sender=node, pubsub_topic=self.test_pubsub_topic, message=self.create_message())
                delay(0.2)

        logger.debug(f"Node5 requests messages of subscribed filter topic {self.test_pubsub_topic}")
        messages_response = self.get_filter_messages(self.test_content_topic, pubsub_topic=self.test_pubsub_topic, node=self.node5)
        logger.debug(f"Response for node 5 is {messages_response}")
        assert len(messages_response) == messages_num, f"Received messages != published which is{messages_num} !!"

    @pytest.mark.timeout(60 * 3)
    def test_filter_many_subscribed_nodes(self):
        max_subscribed_nodes = 30
        if STRESS_ENABLED:
            max_subscribed_nodes = 500
        node_list = []
        logger.debug("Start 2 nodes")
        self.node1.start(relay="true", store="true")
        self.node2.start(relay="true", filter="true", store="false", discv5_bootstrap_node=self.node1.get_enr_uri())

        logger.debug(f"Subscribe nodes to relay  pubsub topic {self.test_pubsub_topic}")
        node_list_relay = [self.node1, self.node2]
        for node in node_list_relay:
            node.set_relay_subscriptions([self.test_pubsub_topic])
        self.wait_for_autoconnection(node_list_relay, hard_wait=30)

        logger.debug(f"{max_subscribed_nodes} Node start and making filter requests to node2")
        for i in range(max_subscribed_nodes):
            node_list.append(WakuNode(NODE_2, f"node{i}_{self.test_id}"))
            delay(0.1)
            node_list[i].start(relay="false", filter="true", filternode=self.node2.get_multiaddr_with_id(), store="false")
            delay(1)
            node_list[i].set_filter_subscriptions(
                {"requestId": "1", "contentFilters": [self.test_content_topic], "pubsubTopic": self.test_pubsub_topic}
            )
            delay(1)

        logger.debug("Node1 publish message")
        self.publish_message(sender=self.node1, pubsub_topic=self.test_pubsub_topic, message=self.create_message())
        delay(2)

        logger.debug(f"{max_subscribed_nodes} Node requests the published message of subscribed filter topic")
        for i in range(max_subscribed_nodes):
            messages_response = self.get_filter_messages(self.test_content_topic, pubsub_topic=self.test_pubsub_topic, node=node_list[i])
            logger.debug(f"Response for node {i} is {messages_response}")
            assert len(messages_response) == 1, "Received message count doesn't match sent "
