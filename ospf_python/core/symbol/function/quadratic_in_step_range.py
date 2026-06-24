"""二次步进范围内函数符号 / QuadraticInStepRange function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class QuadraticInStepRange(FunctionSymbol):
    """二次步进范围内 / QuadraticInStepRange.

    二次步进范围内函数符号实现。
    QuadraticInStepRange function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        step: 步长 / Step.
        coeff: 系数 / Coefficient.
    """

    name: str = "QuadraticInStepRange"
    """函数符号名称 / Function symbol name."""

    step: float = 1.0
    """步长 / Step."""

    coeff: float = 1.0
    """系数 / Coefficient."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args or self.step == 0.0:
            return 0.0
        val = args[0]
        idx = int(val / self.step)
        return self.coeff * idx * idx

    @staticmethod
    def create(
        *,
        step: float = 1.0,
        coeff: float = 1.0,
    ) -> QuadraticInStepRange:
        """创建二次步进范围内 / Create QuadraticInStepRange.

        Args:
            step: 步长 / Step.
            coeff: 系数 / Coefficient.

        Returns:
            二次步进范围内实例 / QuadraticInStepRange instance.
        """
        return QuadraticInStepRange(step=step, coeff=coeff)
