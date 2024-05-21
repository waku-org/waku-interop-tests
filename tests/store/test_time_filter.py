import pytest
from datetime import timedelta, datetime
from src.libs.custom_logger import get_custom_logger
from src.steps.store import StepsStore

logger = get_custom_logger(__name__)


## tests with time filters


@pytest.mark.usefixtures("node_setup")
class TestTimeFilter(StepsStore):
    def test_messages_with_timestamps_close_to_now(self):
        ts = [
            {"description": "3 sec Past", "value": int((datetime.now() - timedelta(seconds=3)).timestamp() * 1e9)},
            {"description": "1 sec Past", "value": int((datetime.now() - timedelta(seconds=1)).timestamp() * 1e9)},
            {"description": "0.1 sec Past", "value": int((datetime.now() - timedelta(seconds=0.1)).timestamp() * 1e9)},
            {"description": "0.1 sec Future", "value": int((datetime.now() + timedelta(seconds=0.1)).timestamp() * 1e9)},
            {"description": "2 sec Future", "value": int((datetime.now() + timedelta(seconds=2)).timestamp() * 1e9)},
            {"description": "10 sec Future", "value": int((datetime.now() + timedelta(seconds=10)).timestamp() * 1e9)},
        ]
        failed_timestamps = []
        for timestamp in ts:
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
        ts = [
            {"description": "20 sec Past", "value": int((datetime.now() - timedelta(seconds=20)).timestamp() * 1e9)},
            {"description": "40 sec Future", "value": int((datetime.now() + timedelta(seconds=40)).timestamp() * 1e9)},
        ]
        for timestamp in ts:
            logger.debug(f'Running test with payload {timestamp["description"]}')
            message = self.create_message(timestamp=timestamp["value"])
            try:
                self.publish_message(message=message)
                self.check_store_returns_empty_response()
            except Exception as ex:
                logger.error(f'Payload {timestamp["description"]} succeeded where it should have failed: {str(ex)}')
                success_timestamps.append(timestamp["description"])
        assert not success_timestamps, f"Timestamps succeeded: {success_timestamps}"
