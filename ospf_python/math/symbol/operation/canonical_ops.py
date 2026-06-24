"""规范多项式运算。

Canonical polynomial operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

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

        Normalize polynomial representation.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            规范化后的多项式。/ Normalized polynomial.
        """
        # TODO: 实现规范化逻辑
        # TODO: implement normalization logic
        return polynomial

    def canonicalize(self, polynomial: T) -> T:
        """将多项式转为规范形式。

        Convert polynomial to canonical form.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            规范形式的多项式。/ Canonical polynomial.
        """
        # TODO: 实现规范化逻辑
        # TODO: implement canonicalization logic
        return polynomial
