"""最大值函数符号 / Max function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Max(FunctionSymbol):
    """最大值 / Max.

    最大值函数符号实现。
    Max function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Max"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        return max(args) if args else 0.0

    @staticmethod
    def create() -> Max:
        """创建最大值 / Create Max.

        Returns:
            最大值实例 / Max instance.
        """
        return Max(name="Max")
