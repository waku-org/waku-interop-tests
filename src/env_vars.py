import os
import logging

logger = logging.getLogger(__name__)


def get_env_var(var_name, default):
    env_var = os.getenv(var_name, default)
    logger.debug(f"{var_name}: {env_var}")
    return env_var


# Configuration constants
NODE_1 = get_env_var("NODE_1", "wakuorg/nwaku:deploy-wakuv2-test")
NODE_2 = get_env_var("NODE_2", "wakuorg/go-waku:latest")
LOG_DIR = get_env_var("LOG_DIR", "./log")
NETWORK_NAME = get_env_var("NETWORK_NAME", "waku")
SUBNET = get_env_var("SUBNET", "172.18.0.0/16")
IP_RANGE = get_env_var("IP_RANGE", "172.18.0.0/24")
GATEWAY = get_env_var("GATEWAY", "172.18.0.1")
DEFAULT_PUBSUBTOPIC = get_env_var("DEFAULT_PUBSUBTOPIC", "/waku/2/default-waku/proto")
