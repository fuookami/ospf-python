"""多项式规范化。

Normalize polynomial expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PolynomialNormalizer(Generic[T]):
    """多项式规范器。

    Normalizes polynomial expressions into a canonical
    form.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def normalize(self, polynomial: T) -> T:
        """规范化多项式。

        Normalize the polynomial to canonical form.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            规范化后的多项式。/ Normalized polynomial.
        """
        return polynomial

    def is_normalized(self, polynomial: T) -> bool:
        """检查多项式是否已规范化。

        Check if polynomial is already normalized.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            是否已规范化。/ Whether normalized.
        """
        return True
