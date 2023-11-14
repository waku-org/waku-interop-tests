import os
from dotenv import load_dotenv

load_dotenv()  # This will load environment variables from a .env file if it exists


def get_env_var(var_name, default=None):
    env_var = os.getenv(var_name, default)
    if env_var is not None:
        print(f"{var_name}: {env_var}")
    else:
        print(f"{var_name} is not set; using default value: {default}")
    return env_var


# Configuration constants. Need to be upercase to appear in reports
NODE_1 = get_env_var("NODE_1", "wakuorg/go-waku:latest")
NODE_2 = get_env_var("NODE_2", "wakuorg/nwaku:latest")
DOCKER_LOG_DIR = get_env_var("DOCKER_LOG_DIR", "./log/docker")
NETWORK_NAME = get_env_var("NETWORK_NAME", "waku")
SUBNET = get_env_var("SUBNET", "172.18.0.0/16")
IP_RANGE = get_env_var("IP_RANGE", "172.18.0.0/24")
GATEWAY = get_env_var("GATEWAY", "172.18.0.1")
DEFAULT_PUBSUBTOPIC = get_env_var("DEFAULT_PUBSUBTOPIC", "/waku/2/default-waku/proto")
PROTOCOL = get_env_var("PROTOCOL", "REST")
RUNNING_IN_CI = get_env_var("CI")
