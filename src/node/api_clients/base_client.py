import requests
from tenacity import retry, stop_after_delay, wait_fixed
from abc import ABC, abstractmethod
from src.env_vars import API_REQUEST_TIMEOUT
from src.libs.custom_logger import get_custom_logger

logger = get_custom_logger(__name__)


class BaseClient(ABC):
    # The retry decorator is applied to handle transient errors gracefully. This is particularly
    # useful when running tests in parallel, where occasional network-related errors such as
    # connection drops, timeouts, or temporary unavailability of a service can occur. Retrying
    # ensures that such intermittent issues don't cause the tests to fail outright.
    @retry(stop=stop_after_delay(0.5), wait=wait_fixed(0.1), reraise=True)
    def make_request(self, method, url, headers=None, data=None):
        logger.debug(f"{method.upper()} call: {url} with payload: {data}")
        response = requests.request(method.upper(), url, headers=headers, data=data, timeout=API_REQUEST_TIMEOUT)
        try:
            response.raise_for_status()
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}. Response content: {response.content}")
            raise
        except Exception as err:
            logger.error(f"An error occurred: {err}. Response content: {response.content}")
            raise
        else:
            logger.info(f"Response status code: {response.status_code}. Response content: {response.content}")
        return response

    @abstractmethod
    def info(self):
        pass

    @abstractmethod
    def set_subscriptions(self, pubsub_topics):
        pass

    @abstractmethod
    def send_message(self, message, pubsub_topic):
        pass

    @abstractmethod
    def get_messages(self, pubsub_topic):
        pass
