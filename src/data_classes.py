from dataclasses import dataclass, field
from marshmallow_dataclass import class_schema
from typing import Optional


@dataclass
class MessageRpcQuery:
    payload: str
    contentTopic: str
    timestamp: Optional[int] = None


@dataclass
class MessageRpcResponse:
    payload: str
    contentTopic: str
    version: Optional[int]
    timestamp: int
    ephemeral: Optional[bool]
    rateLimitProof: Optional[dict] = field(default_factory=dict)
    rate_limit_proof: Optional[dict] = field(default_factory=dict)


message_rpc_response_schema = class_schema(MessageRpcResponse)()
