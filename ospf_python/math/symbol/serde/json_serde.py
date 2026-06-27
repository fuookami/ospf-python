"""JSON 序列化与反序列化。

JSON serialization and deserialization.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


class _JsonEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，支持 dataclass 和 Enum。

    Custom JSON encoder supporting dataclass and Enum.
    """

    def default(self, obj: Any) -> Any:
        """处理不可直接序列化的对象。

        Handle objects that cannot be serialized directly.

        Args:
            obj: 待序列化的对象。/ Object to serialize.

        Returns:
            JSON 可序列化的对象。/
            JSON-serializable object.
        """
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


class JsonSerde:
    """JSON 序列化/反序列化工具。

    JSON serialization and deserialization utility.

    支持 dataclass 和 Enum 类型的自动转换。
    Supports automatic conversion of dataclass
    and Enum types.
    """

    @staticmethod
    def to_json(obj: Any) -> str:
        """将对象序列化为 JSON 字符串。

        Serialize an object to a JSON string.

        Args:
            obj: 待序列化的对象。/ Object to serialize.

        Returns:
            JSON 字符串。/ JSON string.
        """
        return json.dumps(
            obj,
            cls=_JsonEncoder,
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def from_json(text: str) -> Any:
        """从 JSON 字符串反序列化。

        Deserialize from a JSON string.

        Args:
            text: JSON 字符串。/ JSON string.

        Returns:
            反序列化后的对象。/ Deserialized object.
        """
        return json.loads(text)
