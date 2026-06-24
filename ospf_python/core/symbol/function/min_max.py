"""最小最大值函数符号 / MinMax function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class MinMax(FunctionSymbol):
    """最小最大值 / MinMax.

    最小最大值函数符号实现。
    MinMax function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        lower_cap: 下限 / Lower cap.
        upper_cap: 上限 / Upper cap.
    """

    name: str = "MinMax"
    """函数符号名称 / Function symbol name."""

    lower_cap: float = 0.0
    """下限 / Lower cap."""

    upper_cap: float = 1.0
    """上限 / Upper cap."""

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
        return max(self.lower_cap, min(val, self.upper_cap))

    @staticmethod
    def create(
        *,
        lower_cap: float = 0.0,
        upper_cap: float = 1.0,
    ) -> MinMax:
        """创建最小最大值 / Create MinMax.

        Args:
            lower_cap: 下限 / Lower cap.
            upper_cap: 上限 / Upper cap.

        Returns:
            最小最大值实例 / MinMax instance.
        """
        return MinMax(lower_cap=lower_cap, upper_cap=upper_cap)
