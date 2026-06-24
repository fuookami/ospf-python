"""规范不等式。

Canonical inequality representation with left/right
polynomials and comparison operator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.symbol.inequality.comparison import (
        Comparison,
    )

T = TypeVar("T")


@dataclass(frozen=True)
class CanonicalInequality(Generic[T]):
    """规范不等式，由左右多项式和比较运算符组成。

    Canonical inequality composed of left and right
    polynomials with a comparison operator.

    Attributes:
        left: 左侧多项式。/ Left polynomial.
        right: 右侧多项式。/ Right polynomial.
        comparison: 比较运算符。/ Comparison operator.
    """

    left: T
    right: T
    comparison: Comparison

    @property
    def is_linear(self) -> bool:
        """是否为线性不等式。/ Whether linear."""
        # 子类应覆盖此属性 / Subclasses should override
        return False

    @property
    def is_quadratic(self) -> bool:
        """是否为二次不等式。/ Whether quadratic."""
        # 子类应覆盖此属性 / Subclasses should override
        return False

    def negated(self) -> CanonicalInequality[T]:
        """获取取反后的不等式。

        Get the negated inequality.

        Returns:
            取反后的不等式。/ Negated inequality.
        """
        return CanonicalInequality(
            left=self.left,
            right=self.right,
            comparison=self.comparison.negated,
        )

    def reversed(self) -> CanonicalInequality[T]:
        """获取左右互换后的不等式。

        Get the inequality with operands swapped.

        Returns:
            反转后的不等式。/ Reversed inequality.
        """
        return CanonicalInequality(
            left=self.right,
            right=self.left,
            comparison=self.comparison.reversed,
        )
