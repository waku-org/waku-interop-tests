import pytest
from datetime import timedelta, datetime
from src.libs.custom_logger import get_custom_logger
from src.steps.store import StepsStore

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("node_setup")
class TestTimeFilter(StepsStore):
    @pytest.fixture(scope="function", autouse=True)
    def setup_test_data(self):
        self.ts_pass = [
            {"description": "3 sec Past", "value": int((datetime.now() - timedelta(seconds=3)).timestamp() * 1e9)},
            {"description": "1 sec Past", "value": int((datetime.now() - timedelta(seconds=1)).timestamp() * 1e9)},
            {"description": "0.1 sec Past", "value": int((datetime.now() - timedelta(seconds=0.1)).timestamp() * 1e9)},
            {"description": "0.1 sec Future", "value": int((datetime.now() + timedelta(seconds=0.1)).timestamp() * 1e9)},
            {"description": "2 sec Future", "value": int((datetime.now() + timedelta(seconds=2)).timestamp() * 1e9)},
            {"description": "10 sec Future", "value": int((datetime.now() + timedelta(seconds=10)).timestamp() * 1e9)},
        ]
        self.ts_fail = [
            {"description": "20 sec Past", "value": int((datetime.now() - timedelta(seconds=20)).timestamp() * 1e9)},
            {"description": "40 sec Future", "value": int((datetime.now() + timedelta(seconds=40)).timestamp() * 1e9)},
        ]

    def test_messages_with_timestamps_close_to_now(self):
        failed_timestamps = []
        for timestamp in self.ts_pass:
            logger.debug(f'Running test with payload {timestamp["description"]}')
            message = self.create_message(timestamp=timestamp["value"])
            try:
                self.publish_message(message=message)
                self.check_published_message_is_stored(page_size=20, ascending="true")
            except Exception as ex:
                logger.error(f'Payload {timestamp["description"]} failed: {str(ex)}')
                failed_timestamps.append(timestamp["description"])
        assert not failed_timestamps, f"Timestamps failed: {failed_timestamps}"

    def test_messages_with_timestamps_far_from_now(self):
        success_timestamps = []
        for timestamp in self.ts_fail:
            logger.debug(f'Running test with payload {timestamp["description"]}')
            message = self.create_message(timestamp=timestamp["value"])
            try:
                self.publish_message(message=message)
                self.check_store_returns_empty_response()
            except Exception as ex:
                logger.error(f'Payload {timestamp["description"]} succeeded where it should have failed: {str(ex)}')
                success_timestamps.append(timestamp["description"])
        assert not success_timestamps, f"Timestamps succeeded: {success_timestamps}"

    def test_time_filter_matches_one_message(self):
        message_hash_list = []
        for timestamp in self.ts_pass:
            message = self.create_message(timestamp=timestamp["value"])
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(
                node,
                page_size=20,
                start_time=self.ts_pass[0]["value"] - 100000,
                end_time=self.ts_pass[0]["value"] + 100000,
            )
            assert len(store_response.messages) == 1, "Message count mismatch"
            assert store_response.message_hash(0) == message_hash_list[0], "Incorrect messaged filtered based on time"

    def test_time_filter_matches_multiple_messages(self):
        message_hash_list = []
        for timestamp in self.ts_pass:
            message = self.create_message(timestamp=timestamp["value"])
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(
                node,
                page_size=20,
                start_time=self.ts_pass[0]["value"] - 100000,
                end_time=self.ts_pass[4]["value"] + 100000,
            )
            assert len(store_response.messages) == 5, "Message count mismatch"
            for i in range(5):
                assert store_response.message_hash(i) == message_hash_list[i], f"Incorrect messaged filtered based on time at index {i}"

    def test_time_filter_matches_no_message(self):
        message_hash_list = []
        for timestamp in self.ts_pass:
            message = self.create_message(timestamp=timestamp["value"])
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(
                node,
                page_size=20,
                start_time=self.ts_pass[0]["value"] - 100000,
                end_time=self.ts_pass[0]["value"] - 100,
            )
            assert not store_response.messages, "Message count mismatch"

    def test_time_filter_start_time_equals_end_time(self):
        message_hash_list = []
        for timestamp in self.ts_pass:
            message = self.create_message(timestamp=timestamp["value"])
            self.publish_message(message=message)
            message_hash_list.append(self.compute_message_hash(self.test_pubsub_topic, message))
        for node in self.store_nodes:
            store_response = self.get_messages_from_store(
                node,
                page_size=20,
                start_time=self.ts_pass[0]["value"],
                end_time=self.ts_pass[0]["value"],
            )
            assert len(store_response.messages) == 1, "Message count mismatch"
            assert store_response.message_hash(0) == message_hash_list[0], "Incorrect messaged filtered based on time"
