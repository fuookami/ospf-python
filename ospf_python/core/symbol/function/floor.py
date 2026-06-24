"""向下取整函数符号 / Floor function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Floor(FunctionSymbol):
    """向下取整 / Floor.

    向下取整函数符号实现。
    Floor function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Floor"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        import math

        return math.floor(args[0]) if args else 0.0

    @staticmethod
    def create() -> Floor:
        """创建向下取整 / Create Floor.

        Returns:
            向下取整实例 / Floor instance.
        """
        return Floor(name="Floor")
