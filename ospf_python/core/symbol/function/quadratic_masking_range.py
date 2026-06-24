"""二次掩码范围函数符号 / QuadraticMaskingRange function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class QuadraticMaskingRange(FunctionSymbol):
    """二次掩码范围 / QuadraticMaskingRange.

    二次掩码范围函数符号实现。
    QuadraticMaskingRange function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        lower: 下界 / Lower bound.
        upper: 上界 / Upper bound.
        coeff: 系数 / Coefficient.
    """

    name: str = "QuadraticMaskingRange"
    """函数符号名称 / Function symbol name."""

    lower: float = 0.0
    """下界 / Lower bound."""

    upper: float = 1.0
    """上界 / Upper bound."""

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
        val = args[0]
        if val < self.lower or val > self.upper:
            return 0.0
        return self.coeff * val * val

    @staticmethod
    def create(
        *,
        lower: float = 0.0,
        upper: float = 1.0,
        coeff: float = 1.0,
    ) -> QuadraticMaskingRange:
        """创建二次掩码范围 / Create QuadraticMaskingRange.

        Args:
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.
            coeff: 系数 / Coefficient.

        Returns:
            二次掩码范围实例 / QuadraticMaskingRange instance.
        """
        return QuadraticMaskingRange(lower=lower, upper=upper, coeff=coeff)
