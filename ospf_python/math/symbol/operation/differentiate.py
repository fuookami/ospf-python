"""符号微分。

Symbolic differentiation of polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Differentiator(Generic[T]):
    """符号微分器。

    Performs symbolic differentiation on polynomials.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def differentiate(
        self,
        polynomial: T,
        variable: str,
    ) -> T:
        """对指定变量求导。

        Differentiate with respect to a variable.

        Args:
            polynomial: 输入多项式。/ Input polynomial.
            variable: 求导变量。/ Variable to diff.

        Returns:
            导数多项式。/ Derivative polynomial.
        """
        return polynomial
