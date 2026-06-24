"""带容差的数值。

Toleranced value.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Toleranced:
    """带容差的浮点值。

    Float value with tolerance for approximate comparison.

    Attributes:
        value: 标称值。/ Nominal value.
        tolerance: 容差范围。/ Tolerance range.
    """

    value: float
    tolerance: float

    def is_close(
        self,
        other: Toleranced,
        *,
        rel_tol: float = 1e-9,
        abs_tol: float | None = None,
    ) -> bool:
        """检查与另一容差值是否接近。

        Check closeness to another toleranced value.

        Args:
            other: 另一个容差值。/ Another toleranced value.
            rel_tol: 相对容差。/ Relative tolerance.
            abs_tol: 绝对容差，默认使用自身 tolerance。
                Absolute tolerance, defaults to self.tolerance.

        Returns:
            是否接近。/ Whether close.
        """
        effective_abs = abs_tol if abs_tol is not None else self.tolerance
        return math.isclose(
            self.value,
            other.value,
            rel_tol=rel_tol,
            abs_tol=effective_abs,
        )

    def __eq__(self, other: object) -> bool:
        """带容差的相等比较。

        Equality comparison with tolerance.

        Args:
            other: 另一个对象。/ Another object.

        Returns:
            是否在容差内相等。/ Whether equal within tolerance.
        """
        if not isinstance(other, Toleranced):
            return NotImplemented
        return abs(self.value - other.value) <= self.tolerance
