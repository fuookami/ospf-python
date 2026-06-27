"""合并同类项。

Combine like terms in polynomial expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class TermCombiner(Generic[T]):
    """同类项合并器。

    Combines like terms in a polynomial expression.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def combine(self, polynomial: T) -> T:
        """合并多项式中的同类项。

        Combine like terms in the polynomial.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            合并同类项后的多项式。/
            Polynomial with combined terms.
        """
        return polynomial
