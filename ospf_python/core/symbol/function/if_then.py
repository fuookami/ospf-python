"""蕴含条件函数符号 / IfThen function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class IfThen(FunctionSymbol):
    """蕴含条件 / IfThen.

    蕴含条件函数符号实现。
    IfThen function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "IfThen"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if len(args) < 2:
            return 0.0
        return args[1] if args[0] != 0.0 else 0.0

    @staticmethod
    def create() -> IfThen:
        """创建蕴含条件 / Create IfThen.

        Returns:
            蕴含条件实例 / IfThen instance.
        """
        return IfThen(name="IfThen")
