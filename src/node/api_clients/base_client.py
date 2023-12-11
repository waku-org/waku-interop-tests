import requests
from tenacity import retry, stop_after_delay, wait_fixed
from abc import ABC, abstractmethod
from src.env_vars import API_REQUEST_TIMEOUT
from src.libs.custom_logger import get_custom_logger

logger = get_custom_logger(__name__)


class BaseClient(ABC):
    def make_request(self, method, url, headers=None, data=None):
        logger.debug(f"{method.upper()} call: {url} with payload: {data}")
        response = requests.request(method.upper(), url, headers=headers, data=data, timeout=API_REQUEST_TIMEOUT)
        try:
            response.raise_for_status()
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}. Response content: {response.content}")
            raise Exception(f"Error: {http_err} with response: {response.content}")
        except Exception as err:
            logger.error(f"An error occurred: {err}. Response content: {response.content}")
            raise Exception(f"Error: {err} with response: {response.content}")
        else:
            logger.info(f"Response status code: {response.status_code}. Response content: {response.content}")
        return response

    @abstractmethod
    def info(self):
        pass

    @abstractmethod
    def set_relay_subscriptions(self, pubsub_topics):
        pass

    @abstractmethod
    def delete_relay_subscriptions(self, pubsub_topics):
        pass

    @abstractmethod
    def send_relay_message(self, message, pubsub_topic):
        pass

    @abstractmethod
    def get_relay_messages(self, pubsub_topic):
        pass

    @abstractmethod
    def set_filter_subscriptions(self, subscription):
        pass

    @abstractmethod
    def get_filter_messages(self, content_topic):
        pass
