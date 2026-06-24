"""值包装器 / Value wrapper.

将值与其有效范围关联。
Associates a value with its valid range.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.algebra.value_range.value_range import ValueRange

T = TypeVar("T")


@dataclass(frozen=True)
class ValueWrapper(Generic[T]):
    """值包装器 / Value wrapper.

    Args:
        value: 包装的值 / Wrapped value.
        range: 有效范围 / Valid range.
    """

    _value: T
    _range: ValueRange[T]

    @property
    def value(self) -> T:
        """获取值 / Get value."""
        return self._value

    @property
    def valid_range(self) -> ValueRange[T]:
        """获取有效范围 / Get valid range."""
        return self._range

    def is_valid(self) -> bool:
        """检查值是否在有效范围内 / Check if value is in valid range."""
        return self._range.contains(self._value)

    def clamp_to_range(self) -> T:
        """将值钳制到范围内 / Clamp value to range.

        Returns:
            T: 钳制后的值 / Clamped value.
        """
        return self._value
