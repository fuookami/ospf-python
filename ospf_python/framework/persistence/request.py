"""持久化请求 / Persistence request.

定义持久化操作的请求数据结构。
Defines the request data structure for persistence operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Request:
    """持久化请求 / Persistence request.

    封装持久化操作的请求参数，包括操作类型和数据。
    Wraps request parameters for persistence operations,
    including operation type and data.

    Attributes:
        operation: 操作类型 / The operation type.
        data: 请求数据 / The request data.
        entity_name: 目标实体名称 / The target entity name.
    """

    operation: str
    data: dict[str, Any]
    entity_name: str = ""
