"""余弦函数符号 / Cos function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Cos(FunctionSymbol):
    """余弦 / Cos.

    余弦函数符号实现。
    Cos function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Cos"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        import math

        return math.cos(args[0]) if args else 0.0

    @staticmethod
    def create() -> Cos:
        """创建余弦 / Create Cos.

        Returns:
            余弦实例 / Cos instance.
        """
        return Cos(name="Cos")
