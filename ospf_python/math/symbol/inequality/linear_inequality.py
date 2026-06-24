"""线性不等式。

Linear inequality representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from ospf_python.math.symbol.inequality.canonical_inequality import (
    CanonicalInequality,
)

T = TypeVar("T")


@dataclass(frozen=True)
class LinearInequality(CanonicalInequality[T]):
    """线性不等式，左右两侧均为线性多项式。

    Linear inequality where both sides are linear
    polynomials.

    Attributes:
        left: 左侧线性多项式。/ Left linear polynomial.
        right: 右侧线性多项式。/ Right linear polynomial.
        comparison: 比较运算符。/ Comparison operator.
    """

    @property
    def is_linear(self) -> bool:
        """是否为线性不等式。/ Whether linear."""
        return True

    def negated(self) -> LinearInequality[T]:
        """获取取反后的线性不等式。

        Get the negated linear inequality.

        Returns:
            取反后的线性不等式。/ Negated linear inequality.
        """
        return LinearInequality(
            left=self.left,
            right=self.right,
            comparison=self.comparison.negated,
        )

    def reversed(self) -> LinearInequality[T]:
        """获取左右互换后的线性不等式。

        Get the linear inequality with operands swapped.

        Returns:
            反转后的线性不等式。/ Reversed linear inequality.
        """
        return LinearInequality(
            left=self.right,
            right=self.left,
            comparison=self.comparison.reversed,
        )
