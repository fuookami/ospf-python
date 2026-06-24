"""二次最小值函数符号 / QuadraticMin function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class QuadraticMin(FunctionSymbol):
    """二次最小值 / QuadraticMin.

    二次最小值函数符号实现。
    QuadraticMin function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        coeff: 系数 / Coefficient.
    """

    name: str = "QuadraticMin"
    """函数符号名称 / Function symbol name."""

    coeff: float = 1.0
    """系数 / Coefficient."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return 0.0
        return min(self.coeff * a * a for a in args)

    @staticmethod
    def create(
        *,
        coeff: float = 1.0,
    ) -> QuadraticMin:
        """创建二次最小值 / Create QuadraticMin.

        Args:
            coeff: 系数 / Coefficient.

        Returns:
            二次最小值实例 / QuadraticMin instance.
        """
        return QuadraticMin(coeff=coeff)
