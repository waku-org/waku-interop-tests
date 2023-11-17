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


def get_nodes(defaults):
    nodes = []
    # First, use the defaults provided
    for node_var_name, default_value in defaults.items():
        node = get_env_var(node_var_name, default_value)
        nodes.append(node)
    # Now check for additional NODE_X variables
    index = len(defaults) + 1
    while True:
        extra_node_var_name = f"NODE_{index}"
        extra_node = get_env_var(extra_node_var_name)
        if not extra_node:  # Break the loop if an additional NODE_X is not set
            break
        nodes.append(extra_node)
        index += 1
    return nodes


# Configuration constants. Need to be upercase to appear in reports
NODE_LIST = get_nodes(defaults={"NODE_1": "wakuorg/go-waku:latest", "NODE_2": "wakuorg/nwaku:latest", "NODE_3": "wakuorg/go-waku:latest"})
# more nodes need to follow the NODE_X pattern
DOCKER_LOG_DIR = get_env_var("DOCKER_LOG_DIR", "./log/docker")
NETWORK_NAME = get_env_var("NETWORK_NAME", "waku")
SUBNET = get_env_var("SUBNET", "172.18.0.0/16")
IP_RANGE = get_env_var("IP_RANGE", "172.18.0.0/24")
GATEWAY = get_env_var("GATEWAY", "172.18.0.1")
DEFAULT_PUBSUB_TOPIC = get_env_var("DEFAULT_PUBSUB_TOPIC", "/waku/2/default-waku/proto")
PROTOCOL = get_env_var("PROTOCOL", "REST")
RUNNING_IN_CI = get_env_var("CI")
NODEKEY = get_env_var("NODEKEY", "30348dd51465150e04a5d9d932c72864c8967f806cce60b5d26afeca1e77eb68")
API_REQUEST_TIMEOUT = get_env_var("API_REQUEST_TIMEOUT", 10)
