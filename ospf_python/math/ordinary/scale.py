"""比例/缩放类型。

Scale type for representing ratios and scaling factors.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scale:
    """比例因子，不可变封装。

    Immutable scale factor wrapper.

    Attributes:
        value: 比例值。/ Scale value.
    """

    value: float

    @staticmethod
    def identity() -> Scale:
        """单位比例 (1.0)。/ Identity scale (1.0)."""
        return Scale(value=1.0)

    @staticmethod
    def zero() -> Scale:
        """零比例 (0.0)。/ Zero scale (0.0)."""
        return Scale(value=0.0)

    def __mul__(self, other: Scale) -> Scale:
        """比例复合。/ Scale composition."""
        return Scale(value=self.value * other.value)

    def __truediv__(self, other: Scale) -> Scale:
        """比例除法。/ Scale division."""
        if other.value == 0.0:
            return Scale(value=0.0)
        return Scale(value=self.value / other.value)

    def __eq__(self, other: object) -> bool:
        """相等比较。/ Equality comparison."""
        if not isinstance(other, Scale):
            return NotImplemented
        return self.value == other.value

    def __ne__(self, other: object) -> bool:
        """不等比较。/ Inequality comparison."""
        if not isinstance(other, Scale):
            return NotImplemented
        return self.value != other.value

    def __hash__(self) -> int:
        """哈希值。/ Hash value."""
        return hash(self.value)

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"Scale({self.value})"

    def apply(self, value: float) -> float:
        """应用比例因子。/ Apply scale factor.

        Args:
            value: 输入值。/ Input value.

        Returns:
            缩放后的值。/ Scaled value.
        """
        return value * self.value

    def inverse(self) -> Scale:
        """计算逆比例。/ Compute inverse scale.

        Returns:
            逆比例。/ Inverse scale.
        """
        if self.value == 0.0:
            return Scale(value=0.0)
        return Scale(value=1.0 / self.value)
