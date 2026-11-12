"""步进范围内函数符号 / InStepRange function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)
from ospf_python.utils.numeric import is_near_integer


@dataclass(frozen=True)
class InStepRange(FunctionSymbol):
    """步进范围内 / InStepRange.

    步进范围内函数符号实现。
    InStepRange function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        step: 步长 / Step.
        lower: 下界 / Lower bound.
        upper: 上界 / Upper bound.
    """

    name: str = "InStepRange"
    """函数符号名称 / Function symbol name."""

    step: float = 1.0
    """步长 / Step."""

    lower: float = 0.0
    """下界 / Lower bound."""

    upper: float = 1.0
    """上界 / Upper bound."""

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
        if val < self.lower or val > self.upper:
            return 0.0
        # 浮点取模余数不可靠：(1.0 - 0.0) % 0.1 == 0.09999999999999995，
        # 于是连步长本身都被判成"不在步上"。改判比值是否贴近整数。
        # A float remainder is unreliable: (1.0 - 0.0) % 0.1 == 0.09999999999999995, so even the
        # step value itself is judged off-grid. Test whether the ratio nears an integer instead.
        return 1.0 if is_near_integer((val - self.lower) / self.step) else 0.0

    @staticmethod
    def create(
        *,
        step: float = 1.0,
        lower: float = 0.0,
        upper: float = 1.0,
    ) -> InStepRange:
        """创建步进范围内 / Create InStepRange.

        Args:
            step: 步长 / Step.
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.

        Returns:
            步进范围内实例 / InStepRange instance.
        """
        return InStepRange(step=step, lower=lower, upper=upper)
