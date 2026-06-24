"""微分运算操作。

Differentiation operations for polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.symbol.operation.differentiate import (
        Differentiator,
    )

T = TypeVar("T")


@dataclass(frozen=True)
class DifferentiateOps(Generic[T]):
    """微分运算操作集。

    Collection of differentiation operations.

    Attributes:
        differentiator: 微分器。/ Differentiator.
    """

    differentiator: Differentiator[T]

    def grad(
        self,
        polynomial: T,
        variables: list[str],
    ) -> list[T]:
        """计算梯度向量。

        Compute gradient vector.

        Args:
            polynomial: 输入多项式。/ Input polynomial.
            variables: 变量列表。/ Variable list.

        Returns:
            梯度向量（各分量的偏导数）。/
            Gradient vector (partial derivatives).
        """
        return [self.differentiator.differentiate(polynomial, var) for var in variables]

    def hessian(
        self,
        polynomial: T,
        variables: list[str],
    ) -> list[list[T]]:
        """计算 Hessian 矩阵。

        Compute Hessian matrix.

        Args:
            polynomial: 输入多项式。/ Input polynomial.
            variables: 变量列表。/ Variable list.

        Returns:
            Hessian 矩阵。/ Hessian matrix.
        """
        grad = self.grad(polynomial, variables)
        return [
            [self.differentiator.differentiate(g, var) for var in variables]
            for g in grad
        ]
