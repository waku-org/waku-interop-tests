import pytest
from src.env_vars import NODE_1, NODE_2
from src.libs.common import to_base64
from src.node.store_response import StoreResponse
from src.steps.store import StepsStore


@pytest.mark.xfail("go_waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1109")
@pytest.mark.usefixtures("node_setup")
class TestCursor(StepsStore):
    # we implicitly test the reusabilty of the cursor for multiple nodes

    def test_get_multiple_2000_store_messages(self):
        expected_message_hash_list = []
        for i in range(2000):
            message = self.create_message(payload=to_base64(f"Message_{i}"))
            self.publish_message(message=message)
            expected_message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        store_response = StoreResponse({"paginationCursor": "", "pagination_cursor": ""}, self.store_node1)
        response_message_hash_list = []
        while store_response.pagination_cursor is not None:
            cursor = store_response.pagination_cursor
            store_response = self.get_messages_from_store(self.store_node1, page_size=100, cursor=cursor)
            for index in range(len(store_response.messages)):
                response_message_hash_list.append(store_response.message_hash(index))
        assert len(expected_message_hash_list) == len(response_message_hash_list), "Message count mismatch"
        assert expected_message_hash_list == response_message_hash_list, "Message hash mismatch"

    @pytest.mark.parametrize("cursor_index, message_count", [[2, 4], [3, 20], [10, 40], [19, 20], [19, 50], [110, 120]])
    def test_different_cursor_and_indexes(self, cursor_index, message_count):
        message_hash_list = []
        cursor = ""
        cursor_index = cursor_index if cursor_index < 100 else 100
        for i in range(message_count):
            message = self.create_message(payload=to_base64(f"Message_{i}"))
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=cursor_index)
            assert len(store_response.messages) == cursor_index
            cursor = store_response.pagination_cursor
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=100, ascending="true", cursor=cursor)
            assert len(store_response.messages) == message_count - cursor_index
            for index in range(len(store_response.messages)):
                assert store_response.message_hash(index) == message_hash_list[cursor_index + index], f"Message hash at index {index} doesn't match"

    def test_passing_cursor_not_returned_in_paginationCursor(self):
        cursor = ""
        for i in range(10):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=5)
            # retrieving the cursor with the message hash of the 3rd message stored
            cursor = store_response.message_hash(2)
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=100, cursor=cursor)
            assert len(store_response.messages) == 7, "Message count mismatch"

    def test_passing_cursor_of_the_last_message_from_the_store(self):
        cursor = ""
        for i in range(10):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=10)
            # retrieving the cursor with the message hash of the last message stored
            cursor = store_response.message_hash(9)
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=100, cursor=cursor)
            assert len(store_response.messages) == 0, "Message count mismatch"

    @pytest.mark.xfail("go-waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1110")
    @pytest.mark.xfail("nwaku" in (NODE_1 + NODE_2), reason="Bug reported: https://github.com/waku-org/nwaku/issues/2716")
    def test_passing_cursor_of_non_existing_message_from_the_store(self):
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        # creating a cursor to a message that doesn't exist
        wrong_message = self.create_message(payload=to_base64("test"))
        cursor = self.compute_message_hash(self.test_pubsub_topic, wrong_message)
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=100, cursor=cursor)
            assert len(store_response.messages) == 0, "Message count mismatch"

    @pytest.mark.xfail("go-waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1110")
    @pytest.mark.xfail("nwaku" in (NODE_1 + NODE_2), reason="Bug reported: https://github.com/waku-org/nwaku/issues/2716")
    def test_passing_invalid_cursor(self):
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        # creating a invalid base64 cursor
        cursor = to_base64("test")
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=100, cursor=cursor)
            assert len(store_response.messages) == 0, "Message count mismatch"

    @pytest.mark.xfail("go-waku" in NODE_2, reason="Bug reported: https://github.com/waku-org/go-waku/issues/1110")
    @pytest.mark.xfail("nwaku" in (NODE_1 + NODE_2), reason="Bug reported: https://github.com/waku-org/nwaku/issues/2716")
    def test_passing_non_base64_cursor(self):
        for i in range(4):
            self.publish_message(message=self.create_message(payload=to_base64(f"Message_{i}")))
        # creating a non base64 cursor
        cursor = "test"
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(node, page_size=100, cursor=cursor)
            assert len(store_response.messages) == 0, "Message count mismatch"
