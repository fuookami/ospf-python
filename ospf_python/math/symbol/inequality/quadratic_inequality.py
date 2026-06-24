"""二次不等式。

Quadratic inequality representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from ospf_python.math.symbol.inequality.canonical_inequality import (
    CanonicalInequality,
)

T = TypeVar("T")


@dataclass(frozen=True)
class QuadraticInequality(CanonicalInequality[T]):
    """二次不等式，左右两侧均为二次多项式。

    Quadratic inequality where both sides are quadratic
    polynomials.

    Attributes:
        left: 左侧二次多项式。/ Left quadratic polynomial.
        right: 右侧二次多项式。/ Right quadratic polynomial.
        comparison: 比较运算符。/ Comparison operator.
    """

    @property
    def is_quadratic(self) -> bool:
        """是否为二次不等式。/ Whether quadratic."""
        return True

    def negated(self) -> QuadraticInequality[T]:
        """获取取反后的二次不等式。

        Get the negated quadratic inequality.

        Returns:
            取反后的二次不等式。/ Negated quadratic inequality.
        """
        return QuadraticInequality(
            left=self.left,
            right=self.right,
            comparison=self.comparison.negated,
        )

    def reversed(self) -> QuadraticInequality[T]:
        """获取左右互换后的二次不等式。

        Get the quadratic inequality with operands swapped.

        Returns:
            反转后的二次不等式。/ Reversed quadratic inequality.
        """
        return QuadraticInequality(
            left=self.right,
            right=self.left,
            comparison=self.comparison.reversed,
        )
