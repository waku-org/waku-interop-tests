import json
import requests
from src.env_vars import API_REQUEST_TIMEOUT
from src.libs.custom_logger import get_custom_logger

logger = get_custom_logger(__name__)


class BaseClient:
    def make_request(self, method, url, headers=None, data=None):
        self.log_request_as_curl(method, url, headers, data)
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

    def log_request_as_curl(self, method, url, headers, data):
        if data:
            try:
                data_dict = json.loads(data)
                if "timestamp" in data_dict:
                    data_dict["timestamp"] = "TIMESTAMP_PLACEHOLDER"
                data = json.dumps(data_dict)
                data = data.replace('"TIMESTAMP_PLACEHOLDER"', "'$(date +%s%N)'")
            except json.JSONDecodeError:
                logger.error("Invalid JSON data provided")
        headers_str_for_log = " ".join([f'-H "{key}: {value}"' for key, value in headers.items()]) if headers else ""
        curl_cmd = f"curl -v -X {method.upper()} \"{url}\" {headers_str_for_log} -d '{data}'"
        logger.info(curl_cmd)
