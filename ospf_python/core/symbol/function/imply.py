"""蕴含函数符号 / Imply function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Imply(FunctionSymbol):
    """蕴含 / Imply.

    蕴含函数符号实现。
    Imply function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Imply"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if len(args) < 2:
            return 1.0
        if args[0] == 0.0 or args[1] != 0.0:
            return 1.0
        return 0.0

    @staticmethod
    def create() -> Imply:
        """创建蕴含 / Create Imply.

        Returns:
            蕴含实例 / Imply instance.
        """
        return Imply(name="Imply")
