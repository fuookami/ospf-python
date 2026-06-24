"""向上取整函数符号 / Ceiling function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Ceiling(FunctionSymbol):
    """向上取整 / Ceiling.

    向上取整函数符号实现。
    Ceiling function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Ceiling"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        import math

        return math.ceil(args[0]) if args else 0.0

    @staticmethod
    def create() -> Ceiling:
        """创建向上取整 / Create Ceiling.

        Returns:
            向上取整实例 / Ceiling instance.
        """
        return Ceiling(name="Ceiling")
