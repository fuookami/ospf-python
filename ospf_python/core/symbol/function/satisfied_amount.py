"""满足数量函数符号 / SatisfiedAmount function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class SatisfiedAmount(FunctionSymbol):
    """满足数量 / SatisfiedAmount.

    满足数量函数符号实现。
    SatisfiedAmount function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "SatisfiedAmount"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        return float(sum(1 for a in args if a != 0.0))

    @staticmethod
    def create() -> SatisfiedAmount:
        """创建满足数量 / Create SatisfiedAmount.

        Returns:
            满足数量实例 / SatisfiedAmount instance.
        """
        return SatisfiedAmount(name="SatisfiedAmount")
