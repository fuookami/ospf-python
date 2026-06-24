"""四舍五入函数符号 / Rounding function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Rounding(FunctionSymbol):
    """四舍五入 / Rounding.

    四舍五入函数符号实现。
    Rounding function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        decimals: 小数位 / Decimal places.
    """

    name: str = "Rounding"
    """函数符号名称 / Function symbol name."""

    decimals: int = 0
    """小数位 / Decimal places."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return 0.0
        factor = 10**self.decimals
        return float(round(args[0] * factor) / factor)

    @staticmethod
    def create(
        *,
        decimals: int = 0,
    ) -> Rounding:
        """创建四舍五入 / Create Rounding.

        Args:
            decimals: 小数位 / Decimal places.

        Returns:
            四舍五入实例 / Rounding instance.
        """
        return Rounding(decimals=decimals)
