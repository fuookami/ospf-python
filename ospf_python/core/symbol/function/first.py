"""取首元素函数符号 / First function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class First(FunctionSymbol):
    """取首元素 / First.

    取首元素函数符号实现。
    First function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "First"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        return args[0] if args else 0.0

    @staticmethod
    def create() -> First:
        """创建取首元素 / Create First.

        Returns:
            取首元素实例 / First instance.
        """
        return First(name="First")
