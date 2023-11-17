from dataclasses import dataclass, field
from marshmallow_dataclass import class_schema
from typing import Optional, Union


@dataclass
class MessageRpcResponse:
    payload: str
    contentTopic: str
    version: Optional[int]
    timestamp: Optional[int]
    ephemeral: Optional[bool]
    meta: Optional[str]
    rateLimitProof: Optional[Union[dict, str]] = field(default_factory=dict)
    rate_limit_proof: Optional[dict] = field(default_factory=dict)


message_rpc_response_schema = class_schema(MessageRpcResponse)()
