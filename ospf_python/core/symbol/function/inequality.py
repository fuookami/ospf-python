"""不等式函数符号 / Inequality function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Inequality(FunctionSymbol):
    """不等式 / Inequality.

    不等式函数符号实现。
    Inequality function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        rhs: 右端值 / RHS value.
        tolerance: 容差 / Tolerance.
    """

    name: str = "Inequality"
    """函数符号名称 / Function symbol name."""

    rhs: float = 0.0
    """右端值 / RHS value."""

    tolerance: float = 1e-6
    """容差 / Tolerance."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return 0.0
        return 1.0 if args[0] <= self.rhs + self.tolerance else 0.0

    @staticmethod
    def create(
        *,
        rhs: float = 0.0,
        tolerance: float = 1e-6,
    ) -> Inequality:
        """创建不等式 / Create Inequality.

        Args:
            rhs: 右端值 / RHS value.
            tolerance: 容差 / Tolerance.

        Returns:
            不等式实例 / Inequality instance.
        """
        return Inequality(rhs=rhs, tolerance=tolerance)
