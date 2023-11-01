import base64


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
