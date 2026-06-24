"""多项式因式分解。

Polynomial factorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Factor(Generic[T]):
    """多项式因子。

    A polynomial factor with its multiplicity.

    Attributes:
        expression: 因子表达式。/ Factor expression.
        multiplicity: 重数。/ Multiplicity.
    """

    expression: T
    multiplicity: int


@dataclass(frozen=True)
class Factorization(Generic[T]):
    """因式分解结果。

    Factorization result containing a list of factors.

    Attributes:
        factors: 因子列表。/ List of factors.
    """

    factors: tuple[Factor[T], ...]


@dataclass(frozen=True)
class PolynomialFactorizer(Generic[T]):
    """多项式因式分解器。

    Performs polynomial factorization.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def factorize(self, polynomial: T) -> Factorization[T]:
        """对多项式进行因式分解。

        Factorize the polynomial.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            因式分解结果。/ Factorization result.
        """
        # TODO: 实现因式分解逻辑
        # TODO: implement factorization logic
        return Factorization(
            factors=(
                Factor(
                    expression=polynomial,
                    multiplicity=1,
                ),
            )
        )
