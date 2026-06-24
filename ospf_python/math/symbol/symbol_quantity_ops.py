"""符号物理量运算。

Symbol quantity operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.symbol.symbol_quantity import SymbolQuantity

T = TypeVar("T")


@dataclass(frozen=True)
class SymbolQuantityOps(Generic[T]):
    """符号物理量运算工具。

    Symbol quantity operations utility.

    提供对符号物理量的算术运算支持。
    Provides arithmetic operations on symbol quantities.
    """

    @staticmethod
    def add(
        lhs: SymbolQuantity[T],
        rhs: SymbolQuantity[T],
    ) -> SymbolQuantity[T]:
        """两个符号物理量相加。/ Add two symbol quantities.

        Args:
            lhs: 左操作数。/ Left operand.
            rhs: 右操作数。/ Right operand.

        Returns:
            相加结果。/ Addition result.
        """
        return SymbolQuantity.create(
            symbol=lhs.symbol,
            quantity=lhs.quantity + rhs.quantity,  # type: ignore[operator]
        )

    @staticmethod
    def subtract(
        lhs: SymbolQuantity[T],
        rhs: SymbolQuantity[T],
    ) -> SymbolQuantity[T]:
        """两个符号物理量相减。/ Subtract two symbol quantities.

        Args:
            lhs: 左操作数。/ Left operand.
            rhs: 右操作数。/ Right operand.

        Returns:
            相减结果。/ Subtraction result.
        """
        return SymbolQuantity.create(
            symbol=lhs.symbol,
            quantity=lhs.quantity - rhs.quantity,  # type: ignore[operator]
        )

    @staticmethod
    def scale(
        sq: SymbolQuantity[T],
        factor: T,
    ) -> SymbolQuantity[T]:
        """缩放符号物理量。/ Scale a symbol quantity.

        Args:
            sq: 符号物理量。/ Symbol quantity.
            factor: 缩放因子。/ Scale factor.

        Returns:
            缩放结果。/ Scaled result.
        """
        return SymbolQuantity.create(
            symbol=sq.symbol,
            quantity=sq.quantity * factor,  # type: ignore[operator]
        )
