"""其中之一函数符号 / OneOf function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class OneOf(FunctionSymbol):
    """其中之一 / OneOf.

    其中之一函数符号实现。
    OneOf function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "OneOf"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        count = sum(1 for a in args if a != 0.0)
        return 1.0 if count == 1 else 0.0

    @staticmethod
    def create() -> OneOf:
        """创建其中之一 / Create OneOf.

        Returns:
            其中之一实例 / OneOf instance.
        """
        return OneOf(name="OneOf")
