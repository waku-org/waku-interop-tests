import pytest
from src.libs.custom_logger import get_custom_logger
from src.steps.store import StepsStore
from src.env_vars import PG_PASS, PG_USER

logger = get_custom_logger(__name__)


@pytest.mark.usefixtures("start_postgres_container")
class TestExternalDb(StepsStore):
    def test_postgres_db(self):
        self.setup_first_publishing_node(store="true", relay="true", store_message_db_url=f"postgres://{PG_USER}:{PG_PASS}@postgres:5432/postgres")
        self.setup_first_store_node(store="true", relay="true")
        self.subscribe_to_pubsub_topics_via_relay()
        message = self.create_message()
        self.publish_message(message=message)
        self.check_published_message_is_stored(page_size=5, ascending="true")
        assert len(self.store_response.messages) == 1
