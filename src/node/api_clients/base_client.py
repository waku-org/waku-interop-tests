import requests
from tenacity import retry, stop_after_delay, wait_fixed
from abc import ABC, abstractmethod
from src.libs.custom_logger import get_custom_logger

logger = get_custom_logger(__name__)


class BaseClient(ABC):
    # The retry decorator is applied to handle transient errors gracefully. This is particularly
    # useful when running tests in parallel, where occasional network-related errors such as
    # connection drops, timeouts, or temporary unavailability of a service can occur. Retrying
    # ensures that such intermittent issues don't cause the tests to fail outright.
    @retry(stop=stop_after_delay(0.5), wait=wait_fixed(0.1), reraise=True)
    def make_request(self, method, url, headers=None, data=None):
        logger.debug("%s call: %s with payload: %s", method.upper(), url, data)
        response = requests.request(method.upper(), url, headers=headers, data=data)
        try:
            response.raise_for_status()
        except requests.HTTPError as http_err:
            logger.error("HTTP error occurred: %s. Response content: %s", http_err, response.content)
            raise
        except Exception as err:
            logger.error("An error occurred: %s. Response content: %s", err, response.content)
            raise
        else:
            logger.info("Response status code: %s. Response content: %s", response.status_code, response.content)
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
