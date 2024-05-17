import pytest
from datetime import timedelta, datetime
from src.libs.custom_logger import get_custom_logger
from src.steps.store import StepsStore

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("node_setup")
class TestTimeFilter(StepsStore):
    def test_messages_with_timestamps_close_to_now(self):
        failed_timestamps = []
        sample_ts = [
            int((datetime.now() - timedelta(seconds=2)).timestamp() * 1e9),
            int((datetime.now() + timedelta(seconds=2)).timestamp() * 1e9),
            int((datetime.now() + timedelta(seconds=10)).timestamp() * 1e9),
        ]
        for timestamp in sample_ts:
            logger.debug(f"Running test with timestamp {timestamp}")
            message = self.create_message(timestamp=timestamp)
            try:
                self.publish_message(message=message)
                self.check_published_message_is_stored(page_size=5, ascending="true")
            except Exception as ex:
                logger.error(f"Timestamp {timestamp} failed: {str(ex)}")
                failed_timestamps.append(timestamp)
        assert not failed_timestamps, f"Timestamps failed: {failed_timestamps}"
