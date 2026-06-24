"""线性/二次运算操作。

Linear and quadratic polynomial operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class LinearQuadraticOps(Generic[T]):
    """线性/二次多项式运算集。

    Operations specific to linear and quadratic
    polynomials.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def solve_linear(
        self,
        polynomial: T,
        variable: str,
    ) -> float | None:
        """求解线性方程 ax + b = 0。

        Solve linear equation ax + b = 0.

        Args:
            polynomial: 线性多项式。/ Linear polynomial.
            variable: 求解变量。/ Variable to solve.

        Returns:
            解或 None。/ Solution or None.
        """
        # TODO: 实现线性求解逻辑
        # TODO: implement linear solve logic
        return None

    def solve_quadratic(
        self,
        polynomial: T,
        variable: str,
    ) -> tuple[float, ...]:
        """求解二次方程 ax^2 + bx + c = 0。

        Solve quadratic equation ax^2 + bx + c = 0.

        Args:
            polynomial: 二次多项式。/ Quadratic polynomial.
            variable: 求解变量。/ Variable to solve.

        Returns:
            解的元组。/ Tuple of solutions.
        """
        # TODO: 实现二次求解逻辑
        # TODO: implement quadratic solve logic
        return ()

    def discriminant(
        self,
        polynomial: T,
        variable: str,
    ) -> float:
        """计算二次方程判别式 b^2 - 4ac。

        Compute discriminant b^2 - 4ac.

        Args:
            polynomial: 二次多项式。/ Quadratic polynomial.
            variable: 变量名。/ Variable name.

        Returns:
            判别式值。/ Discriminant value.
        """
        # TODO: 实现判别式计算
        # TODO: implement discriminant calculation
        raise NotImplementedError
