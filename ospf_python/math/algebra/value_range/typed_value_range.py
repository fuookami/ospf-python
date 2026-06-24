"""带类型的值域定义。

Typed value range definition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.algebra.value_range.value_range import (
        ValueRange,
    )

T = TypeVar("T")


@dataclass(frozen=True)
class TypedValueRange:
    """带类型信息的值域。

    A value range annotated with a type name.

    Attributes:
        type_name: 类型名称。/ Type name.
        range: 值域。/ Value range.
    """

    type_name: str
    range: ValueRange[object]

    @staticmethod
    def of(
        type_name: str,
        range: ValueRange[object],
    ) -> TypedValueRange:
        """工厂方法。/ Factory method.

        Args:
            type_name: 类型名称。/ Type name.
            range: 值域。/ Value range.

        Returns:
            带类型的值域。/ Typed value range.
        """
        return TypedValueRange(
            type_name=type_name,
            range=range,
        )

    def contains(self, value: object) -> bool:
        """检查值是否在值域内。

        Check if a value is within this typed range.

        Args:
            value: 待检查的值。/ Value to check.

        Returns:
            是否在值域内。/ Whether in range.
        """
        return self.range.contains(value)
