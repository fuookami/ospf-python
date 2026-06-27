"""不等式运算。

Operations on polynomial inequalities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.symbol.inequality.canonical_inequality import (
        CanonicalInequality,
    )

T = TypeVar("T")


@dataclass(frozen=True)
class InequalityOps(Generic[T]):
    """不等式运算集。

    Collection of operations on inequalities.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def simplify(
        self,
        inequality: CanonicalInequality[T],
    ) -> CanonicalInequality[T]:
        """简化不等式。

        Simplify the inequality.

        Args:
            inequality: 输入不等式。/ Input inequality.

        Returns:
            简化后的不等式。/ Simplified inequality.
        """
        return inequality

    def merge(
        self,
        left: CanonicalInequality[T],
        right: CanonicalInequality[T],
    ) -> list[CanonicalInequality[T]]:
        """合并两个不等式。

        Merge two inequalities.

        Args:
            left: 左侧不等式。/ Left inequality.
            right: 右侧不等式。/ Right inequality.

        Returns:
            合并后的不等式列表。/ Merged inequalities.
        """
        return [left, right]
