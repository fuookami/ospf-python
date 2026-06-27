"""多项式序列化/反序列化。

Polynomial serialization and deserialization operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class SerdeOps(Generic[T]):
    """序列化/反序列化操作集。

    Collection of serialization and deserialization
    operations.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def serialize(self, polynomial: T) -> str:
        """将多项式序列化为字符串。

        Serialize polynomial to string.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            序列化字符串。/ Serialized string.
        """
        return repr(polynomial)

    def deserialize(self, data: str) -> T | None:
        """从字符串反序列化多项式。

        Deserialize polynomial from string.

        Args:
            data: 序列化字符串。/ Serialized string.

        Returns:
            反序列化结果或 None。/
            Deserialized polynomial or None.
        """
        return None
