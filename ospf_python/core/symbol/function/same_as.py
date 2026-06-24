"""等同于函数符号 / SameAs function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class SameAs(FunctionSymbol):
    """等同于 / SameAs.

    等同于函数符号实现。
    SameAs function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "SameAs"
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
        return 1.0 if args[0] == args[1] else 0.0

    @staticmethod
    def create() -> SameAs:
        """创建等同于 / Create SameAs.

        Returns:
            等同于实例 / SameAs instance.
        """
        return SameAs(name="SameAs")
