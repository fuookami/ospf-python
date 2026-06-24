"""逻辑与函数符号 / And function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class And(FunctionSymbol):
    """逻辑与 / And.

    逻辑与函数符号实现。
    And function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "And"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        return float(all(a != 0.0 for a in args))

    @staticmethod
    def create() -> And:
        """创建逻辑与 / Create And.

        Returns:
            逻辑与实例 / And instance.
        """
        return And(name="And")
