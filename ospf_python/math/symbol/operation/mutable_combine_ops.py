"""可变合并运算操作。

Mutable combine operations for polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class MutableCombineOps(Generic[T]):
    """可变合并运算操作集。

    Operations for combining polynomials in a mutable
    accumulator pattern.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def sum(self, polynomials: list[T]) -> T:
        """求和多个多项式。

        Sum multiple polynomials.

        Args:
            polynomials: 多项式列表。/ Polynomial list.

        Returns:
            求和结果。/ Sum result.
        """
        # TODO: 实现求和逻辑
        # TODO: implement sum logic
        if not polynomials:
            raise NotImplementedError
        return polynomials[0]

    def product(self, polynomials: list[T]) -> T:
        """求积多个多项式。

        Compute product of multiple polynomials.

        Args:
            polynomials: 多项式列表。/ Polynomial list.

        Returns:
            求积结果。/ Product result.
        """
        # TODO: 实现求积逻辑
        # TODO: implement product logic
        if not polynomials:
            raise NotImplementedError
        return polynomials[0]
