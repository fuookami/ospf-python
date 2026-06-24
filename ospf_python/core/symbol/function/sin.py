"""正弦函数符号 / Sin function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Sin(FunctionSymbol):
    """正弦 / Sin.

    正弦函数符号实现。
    Sin function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Sin"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        import math

        return math.sin(args[0]) if args else 0.0

    @staticmethod
    def create() -> Sin:
        """创建正弦 / Create Sin.

        Returns:
            正弦实例 / Sin instance.
        """
        return Sin(name="Sin")
