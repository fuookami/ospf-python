"""乘积函数符号 / Product function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Product(FunctionSymbol):
    """乘积 / Product.

    乘积函数符号实现。
    Product function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str = "Product"
    """函数符号名称 / Function symbol name."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        result = 1.0
        for a in args:
            result *= a
        return result

    @staticmethod
    def create() -> Product:
        """创建乘积 / Create Product.

        Returns:
            乘积实例 / Product instance.
        """
        return Product(name="Product")
