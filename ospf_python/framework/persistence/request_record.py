"""请求记录 / Request record.

定义持久化请求的记录结构。
Defines the record structure for persistence requests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RequestRecord:
    """请求记录 / Request record.

    记录持久化请求的完整信息，用于审计和调试。
    Records complete information of persistence requests
    for auditing and debugging.

    Attributes:
        request_id: 请求标识 / The request identifier.
        operation: 操作类型 / The operation type.
        timestamp: 请求时间戳 / The request timestamp.
        params: 请求参数 / The request parameters.
    """

    request_id: str
    operation: str
    timestamp: datetime
    params: dict[str, Any]
