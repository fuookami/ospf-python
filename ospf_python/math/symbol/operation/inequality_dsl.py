"""不等式 DSL。

DSL for building polynomial inequalities concisely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.symbol.inequality.canonical_inequality import (
    CanonicalInequality,
)
from ospf_python.math.symbol.inequality.comparison import (
    Comparison,
)

T = TypeVar("T")


@dataclass(frozen=True)
class InequalityDsl(Generic[T]):
    """不等式 DSL 入口。

    DSL entry point for building inequalities with
    concise syntax.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def le(
        self,
        left: T,
        right: T,
    ) -> CanonicalInequality[T]:
        """创建 <= 不等式。/ Create <= inequality."""
        return CanonicalInequality(
            left=left,
            right=right,
            comparison=Comparison.LE,
        )

    def ge(
        self,
        left: T,
        right: T,
    ) -> CanonicalInequality[T]:
        """创建 >= 不等式。/ Create >= inequality."""
        return CanonicalInequality(
            left=left,
            right=right,
            comparison=Comparison.GE,
        )

    def lt(
        self,
        left: T,
        right: T,
    ) -> CanonicalInequality[T]:
        """创建 < 不等式。/ Create < inequality."""
        return CanonicalInequality(
            left=left,
            right=right,
            comparison=Comparison.LT,
        )

    def gt(
        self,
        left: T,
        right: T,
    ) -> CanonicalInequality[T]:
        """创建 > 不等式。/ Create > inequality."""
        return CanonicalInequality(
            left=left,
            right=right,
            comparison=Comparison.GT,
        )

    def eq(
        self,
        left: T,
        right: T,
    ) -> CanonicalInequality[T]:
        """创建 == 等式。/ Create == equality."""
        return CanonicalInequality(
            left=left,
            right=right,
            comparison=Comparison.EQ,
        )
