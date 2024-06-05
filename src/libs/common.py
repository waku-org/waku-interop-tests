import uuid
from datetime import datetime
from time import sleep
from src.libs.custom_logger import get_custom_logger
import os
import base64
import allure

logger = get_custom_logger(__name__)


def bytes_to_hex(byte_array):
    return "".join(format(byte, "02x") for byte in byte_array)


def to_base64(input_data):
    if isinstance(input_data, str):
        input_bytes = input_data.encode()
    elif isinstance(input_data, int):
        input_bytes = str(input_data).encode()
    elif isinstance(input_data, bytes):
        input_bytes = input_data
    else:
        input_bytes = str(input_data).encode()
    base64_encoded = base64.b64encode(input_bytes)
    return base64_encoded.decode()


def attach_allure_file(file):
    logger.debug(f"Attaching file {file}")
    allure.attach.file(file, name=os.path.basename(file), attachment_type=allure.attachment_type.TEXT)


def delay(num_seconds):
    logger.debug(f"Sleeping for {num_seconds} seconds")
    sleep(num_seconds)


def gen_step_id():
    return f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}__{str(uuid.uuid4())}"


def peer_info2id(peer, is_nwaku=True):
    return peer_info2multiaddr(peer, is_nwaku).split("/")[-1]


def peer_info2multiaddr(peer, is_nwaku=True):
    if is_nwaku:
        return peer["multiaddr"]
    else:
        return peer["multiaddrs"][0]


def multiaddr2id(multiaddr):
    return multiaddr.split("/")[-1]
