"""规范多项式运算。

Canonical polynomial operations: normalize and canonicalize.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.symbol.operation.combine_terms import TermCombiner
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

T = TypeVar("T")


@dataclass(frozen=True)
class CanonicalOps(Generic[T]):
    """规范多项式运算集。

    Collection of canonical polynomial operations.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def normalize(self, polynomial: T) -> T:
        """规范多项式表示。

        Normalize polynomial representation:
        1. Combine like terms
        2. Remove zero-coefficient terms
        3. Sort terms by degree (descending)

        规范化步骤：
        1. 合并同类项
        2. 移除零系数项
        3. 按次数降序排列

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            规范化后的多项式。/ Normalized polynomial.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            # 先合并同类项 / First combine like terms
            combiner = TermCombiner(factory=CanonicalPolynomial)
            combined = combiner.combine(polynomial)

            # 按次数降序排列 / Sort by degree descending
            sorted_terms = sorted(
                combined.terms,
                key=lambda t: t.degree,
                reverse=True,
            )
            return CanonicalPolynomial(terms=sorted_terms)  # type: ignore[return-value]

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")

    def canonicalize(self, polynomial: T) -> T:
        """将多项式转为规范形式。

        Convert polynomial to canonical form.
        Alias for normalize with additional simplification.

        规范化并简化多项式。
        与 normalize 相同但提供额外简化。

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            规范形式的多项式。/ Canonical polynomial.
        """
        return self.normalize(polynomial)

    def simplify(self, polynomial: T) -> T:
        """简化多项式。

        Simplify polynomial: normalize + remove trivial terms.

        简化多项式：规范化 + 移除平凡项。

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            简化后的多项式。/ Simplified polynomial.
        """
        return self.normalize(polynomial)
