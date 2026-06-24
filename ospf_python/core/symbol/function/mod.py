"""取模函数符号 / Mod function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Mod(FunctionSymbol):
    """取模 / Mod.

    取模函数符号实现。
    Mod function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        divisor: 除数 / Divisor.
    """

    name: str = "Mod"
    """函数符号名称 / Function symbol name."""

    divisor: float = 1.0
    """除数 / Divisor."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args or self.divisor == 0.0:
            return 0.0
        return args[0] % self.divisor

    @staticmethod
    def create(
        *,
        divisor: float = 1.0,
    ) -> Mod:
        """创建取模 / Create Mod.

        Args:
            divisor: 除数 / Divisor.

        Returns:
            取模实例 / Mod instance.
        """
        return Mod(divisor=divisor)
