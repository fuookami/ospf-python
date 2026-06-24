"""二次线性函数符号 / QuadraticLinear function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class QuadraticLinear(FunctionSymbol):
    """二次线性 / QuadraticLinear.

    二次线性函数符号实现。
    QuadraticLinear function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        quadratic_coeff: 二次系数 / Quadratic coefficient.
        linear_coeff: 线性系数 / Linear coefficient.
        intercept: 截距 / Intercept.
    """

    name: str = "QuadraticLinear"
    """函数符号名称 / Function symbol name."""

    quadratic_coeff: float = 1.0
    """二次系数 / Quadratic coefficient."""

    linear_coeff: float = 0.0
    """线性系数 / Linear coefficient."""

    intercept: float = 0.0
    """截距 / Intercept."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return 0.0
        return (
            self.quadratic_coeff * args[0] * args[0]
            + self.linear_coeff * args[0]
            + self.intercept
        )

    @staticmethod
    def create(
        *,
        quadratic_coeff: float = 1.0,
        linear_coeff: float = 0.0,
        intercept: float = 0.0,
    ) -> QuadraticLinear:
        """创建二次线性 / Create QuadraticLinear.

        Args:
            quadratic_coeff: 二次系数 / Quadratic coefficient.
            linear_coeff: 线性系数 / Linear coefficient.
            intercept: 截距 / Intercept.

        Returns:
            二次线性实例 / QuadraticLinear instance.
        """
        return QuadraticLinear(
            quadratic_coeff=quadratic_coeff,
            linear_coeff=linear_coeff,
            intercept=intercept,
        )
