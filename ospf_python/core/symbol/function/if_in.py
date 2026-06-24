"""范围内条件函数符号 / IfIn function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class IfIn(FunctionSymbol):
    """范围内条件 / IfIn.

    范围内条件函数符号实现。
    IfIn function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        lower: 下界 / Lower bound.
        upper: 上界 / Upper bound.
    """

    name: str = "IfIn"
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
        if self.lower <= val <= self.upper:
            return 1.0
        return 0.0

    @staticmethod
    def create(
        *,
        lower: float = 0.0,
        upper: float = 1.0,
    ) -> IfIn:
        """创建范围内条件 / Create IfIn.

        Args:
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.

        Returns:
            范围内条件实例 / IfIn instance.
        """
        return IfIn(lower=lower, upper=upper)
