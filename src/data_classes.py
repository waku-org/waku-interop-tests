from dataclasses import dataclass
from typing import Optional


@dataclass
class KeyPair:
    privateKey: str
    publicKey: str


@dataclass
class MessageRpcQuery:
    payload: str  # Hex encoded data string without `0x` prefix.
    contentTopic: Optional[str] = None
    timestamp: Optional[int] = None  # Unix epoch time in nanoseconds as a 64-bit integer value.


@dataclass
class MessageRpcResponse:
    payload: str
    contentTopic: Optional[str] = None
    version: Optional[int] = None
    timestamp: Optional[int] = None  # Unix epoch time in nanoseconds as a 64-bit integer value.
    ephemeral: Optional[bool] = None
