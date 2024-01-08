import os
from dotenv import load_dotenv

load_dotenv()  # This will load environment variables from a .env file if it exists


def get_env_var(var_name, default=None):
    env_var = os.getenv(var_name, default)
    if env_var in [None, ""]:
        print(f"{var_name} is not set; using default value: {default}")
        env_var = default
    print(f"{var_name}: {env_var}")
    return env_var


# Configuration constants. Need to be upercase to appear in reports
DEFAULT_NWAKU = "harbor.status.im/wakuorg/nwaku:latest"
DEFAULT_GOWAKU = "harbor.status.im/wakuorg/go-waku:latest"
NODE_1 = get_env_var("NODE_1", DEFAULT_GOWAKU)
NODE_2 = get_env_var("NODE_2", DEFAULT_NWAKU)
ADDITIONAL_NODES = get_env_var("ADDITIONAL_NODES", f"{DEFAULT_NWAKU},{DEFAULT_GOWAKU},{DEFAULT_NWAKU}")
# more nodes need to follow the NODE_X pattern
DOCKER_LOG_DIR = get_env_var("DOCKER_LOG_DIR", "./log/docker")
NETWORK_NAME = get_env_var("NETWORK_NAME", "waku")
SUBNET = get_env_var("SUBNET", "172.18.0.0/16")
IP_RANGE = get_env_var("IP_RANGE", "172.18.0.0/24")
GATEWAY = get_env_var("GATEWAY", "172.18.0.1")
DEFAULT_PUBSUB_TOPIC = get_env_var("DEFAULT_PUBSUB_TOPIC", "/waku/2/default-waku/proto")
RUNNING_IN_CI = get_env_var("CI")
NODEKEY = get_env_var("NODEKEY", "30348dd51465150e04a5d9d932c72864c8967f806cce60b5d26afeca1e77eb68")
API_REQUEST_TIMEOUT = get_env_var("API_REQUEST_TIMEOUT", 10)
