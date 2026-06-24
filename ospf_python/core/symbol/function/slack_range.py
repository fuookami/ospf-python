"""松弛范围函数符号 / SlackRange function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class SlackRange(FunctionSymbol):
    """松弛范围 / SlackRange.

    松弛范围函数符号实现。
    SlackRange function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        lower: 下界 / Lower bound.
        upper: 上界 / Upper bound.
    """

    name: str = "SlackRange"
    """函数符号名称 / Function symbol name."""

    lower: float = 0.0
    """下界 / Lower bound."""

    upper: float = 1.0
    """上界 / Upper bound."""

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
        return max(0.0, val - self.lower) + max(0.0, self.upper - val)

    @staticmethod
    def create(
        *,
        lower: float = 0.0,
        upper: float = 1.0,
    ) -> SlackRange:
        """创建松弛范围 / Create SlackRange.

        Args:
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.

        Returns:
            松弛范围实例 / SlackRange instance.
        """
        return SlackRange(lower=lower, upper=upper)
