"""平衡三值化函数符号 / BalanceTernaryzation function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class BalanceTernaryzation(FunctionSymbol):
    """平衡三值化 / BalanceTernaryzation.

    平衡三值化函数符号实现。
    BalanceTernaryzation function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        threshold: 阈值 / Threshold.
    """

    name: str = "BalanceTernaryzation"
    """函数符号名称 / Function symbol name."""

    threshold: float = 0.0
    """阈值 / Threshold."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return 0.0
        val = args[0]
        if val > self.threshold:
            return 1.0
        if val < -self.threshold:
            return -1.0
        return 0.0

    @staticmethod
    def create(
        *,
        threshold: float = 0.0,
    ) -> BalanceTernaryzation:
        """创建平衡三值化 / Create BalanceTernaryzation.

        Args:
            threshold: 阈值 / Threshold.

        Returns:
            平衡三值化实例 / BalanceTernaryzation instance.
        """
        return BalanceTernaryzation(threshold=threshold)
