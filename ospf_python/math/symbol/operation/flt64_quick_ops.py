"""Float64 快速运算。

Float64 quick operations for common polynomial tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Flt64QuickOps:
    """Float64 快速运算集。

    Collection of quick Float64 polynomial operations.

    Attributes:
        tolerance: 数值容差。/ Numerical tolerance.
    """

    tolerance: float = 1e-12

    def is_zero(self, value: float) -> bool:
        """判断值是否近似为零。

        Check if value is approximately zero.

        Args:
            value: 待检查的值。/ Value to check.

        Returns:
            是否近似为零。/ Whether approximately zero.
        """
        return abs(value) < self.tolerance

    def is_equal(
        self,
        a: float,
        b: float,
    ) -> bool:
        """判断两个值是否近似相等。

        Check if two values are approximately equal.

        Args:
            a: 第一个值。/ First value.
            b: 第二个值。/ Second value.

        Returns:
            是否近似相等。/ Whether approximately equal.
        """
        return abs(a - b) < self.tolerance
