"""条件函数符号 / If function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class If(FunctionSymbol):
    """条件 / If.

    条件函数符号实现。
    If function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "If"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if len(args) < 3:
            return 0.0
        return args[1] if args[0] != 0.0 else args[2]

    @staticmethod
    def create() -> If:
        """创建条件 / Create If.

        Returns:
            条件实例 / If instance.
        """
        return If(name="If")
