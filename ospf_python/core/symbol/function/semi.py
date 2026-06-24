"""半连续函数符号 / Semi function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Semi(FunctionSymbol):
    """半连续 / Semi.

    半连续函数符号实现。
    Semi function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        lower: 下界 / Lower bound.
        upper: 上界 / Upper bound.
    """

    name: str = "Semi"
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
        if val == 0.0:
            return 0.0
        return max(self.lower, min(val, self.upper))

    @staticmethod
    def create(
        *,
        lower: float = 0.0,
        upper: float = 1.0,
    ) -> Semi:
        """创建半连续 / Create Semi.

        Args:
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.

        Returns:
            半连续实例 / Semi instance.
        """
        return Semi(lower=lower, upper=upper)
