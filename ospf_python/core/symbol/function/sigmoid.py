"""S型函数函数符号 / Sigmoid function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Sigmoid(FunctionSymbol):
    """S型函数 / Sigmoid.

    S型函数函数符号实现。
    Sigmoid function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        scale: 缩放因子 / Scale factor.
    """

    name: str = "Sigmoid"
    """函数符号名称 / Function symbol name."""

    scale: float = 1.0
    """缩放因子 / Scale factor."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        import math

        if not args:
            return 0.5
        return 1.0 / (1.0 + math.exp(-self.scale * args[0]))

    @staticmethod
    def create(
        *,
        scale: float = 1.0,
    ) -> Sigmoid:
        """创建S型函数 / Create Sigmoid.

        Args:
            scale: 缩放因子 / Scale factor.

        Returns:
            S型函数实例 / Sigmoid instance.
        """
        return Sigmoid(scale=scale)
