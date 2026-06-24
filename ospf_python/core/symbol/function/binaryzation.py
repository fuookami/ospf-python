"""二值化函数符号 / Binaryzation function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Binaryzation(FunctionSymbol):
    """二值化 / Binaryzation.

    二值化函数符号实现。
    Binaryzation function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        threshold: 阈值 / Threshold.
    """

    name: str = "Binaryzation"
    """函数符号名称 / Function symbol name."""

    threshold: float = 0.5
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
        return 1.0 if args[0] > self.threshold else 0.0

    @staticmethod
    def create(
        *,
        threshold: float = 0.5,
    ) -> Binaryzation:
        """创建二值化 / Create Binaryzation.

        Args:
            threshold: 阈值 / Threshold.

        Returns:
            二值化实例 / Binaryzation instance.
        """
        return Binaryzation(threshold=threshold)
