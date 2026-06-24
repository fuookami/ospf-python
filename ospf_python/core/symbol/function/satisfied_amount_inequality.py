"""不等式满足数量函数符号 / SatisfiedAmountInequality function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class SatisfiedAmountInequality(FunctionSymbol):
    """不等式满足数量 / SatisfiedAmountInequality.

    不等式满足数量函数符号实现。
    SatisfiedAmountInequality function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        rhs: 右端值 / RHS value.
    """

    name: str = "SatisfiedAmountInequality"
    """函数符号名称 / Function symbol name."""

    rhs: float = 0.0
    """右端值 / RHS value."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        return float(sum(1 for a in args if a <= self.rhs))

    @staticmethod
    def create(
        *,
        rhs: float = 0.0,
    ) -> SatisfiedAmountInequality:
        """创建不等式满足数量 / Create SatisfiedAmountInequality.

        Args:
            rhs: 右端值 / RHS value.

        Returns:
            不等式满足数量实例 / SatisfiedAmountInequality instance.
        """
        return SatisfiedAmountInequality(rhs=rhs)
