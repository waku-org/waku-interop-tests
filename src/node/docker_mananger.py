import os
from src.libs.custom_logger import get_custom_logger
import random
import threading
import docker
from src.env_vars import NETWORK_NAME, SUBNET, IP_RANGE, GATEWAY
from docker.types import IPAMConfig, IPAMPool
from docker.errors import NotFound

logger = get_custom_logger(__name__)


class DockerManager:
    def __init__(self, image):
        self._image = image
        self._client = docker.from_env()
        logger.debug(f"Docker client initialized with image {self._image}")

    def create_network(self, network_name=NETWORK_NAME):
        logger.debug(f"Attempting to create or retrieve network {network_name}")
        networks = self._client.networks.list(names=[network_name])
        if networks:
            logger.debug(f"Network {network_name} already exists")
            return networks[0]

        network = self._client.networks.create(
            network_name,
            driver="bridge",
            ipam=IPAMConfig(driver="default", pool_configs=[IPAMPool(subnet=SUBNET, iprange=IP_RANGE, gateway=GATEWAY)]),
        )
        logger.debug(f"Network {network_name} created")
        return network

    def start_container(self, image_name, ports, args, log_path, container_ip):
        cli_args = []
        for key, value in args.items():
            if isinstance(value, list):  # Check if value is a list
                cli_args.extend([f"--{key}={item}" for item in value])  # Add a command for each item in the list
            else:
                cli_args.append(f"--{key}={value}")  # Add a single command
        port_bindings = {f"{port}/tcp": ("", port) for port in ports}
        logger.debug(f"Starting container with image {image_name}")
        logger.debug(f"Using args {cli_args}")
        container = self._client.containers.run(image_name, command=cli_args, ports=port_bindings, detach=True, remove=True, auto_remove=True)

        network = self._client.networks.get(NETWORK_NAME)
        network.connect(container, ipv4_address=container_ip)

        logger.debug(f"Container started with ID {container.short_id}. Setting up logs at {log_path}")
        log_thread = threading.Thread(target=self._log_container_output, args=(container, log_path))
        log_thread.daemon = True
        log_thread.start()

        return container

    def _log_container_output(self, container, log_path):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "wb+") as log_file:
            for chunk in container.logs(stream=True):
                log_file.write(chunk)

    def generate_ports(self, base_port=None, count=6):
        if base_port is None:
            base_port = random.randint(1024, 65535 - count)
        ports = [base_port + i for i in range(count)]
        logger.debug(f"Generated ports {ports}")
        return ports

    @staticmethod
    def generate_random_ext_ip():
        base_ip_fragments = ["172", "18"]
        ext_ip = ".".join(base_ip_fragments + [str(random.randint(0, 255)) for _ in range(2)])
        logger.debug(f"Generated random external IP {ext_ip}")
        return ext_ip

    def is_container_running(self, container):
        try:
            refreshed_container = self._client.containers.get(container.id)
            return refreshed_container.status == "running"
        except NotFound:
            logger.error(f"Container with ID {container.id} not found")
            return False

    @property
    def image(self):
        return self._image
