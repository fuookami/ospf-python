"""绝对值函数符号 / Abs function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Abs(FunctionSymbol):
    """绝对值 / Abs.

    绝对值函数符号实现。
    Abs function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Abs"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        return abs(args[0]) if args else 0.0

    @staticmethod
    def create() -> Abs:
        """创建绝对值 / Create Abs.

        Returns:
            绝对值实例 / Abs instance.
        """
        return Abs(name="Abs")
