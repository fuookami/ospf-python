"""符号物理量。

Symbol physical quantity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")


@dataclass(frozen=True)
class SymbolQuantity(Generic[T]):
    """符号与物理量的关联。

    Association of a symbol with a physical quantity.

    Attributes:
        symbol: 数学符号。/ Mathematical symbol.
        quantity: 物理量值。/ Physical quantity value.
    """

    symbol: Symbol
    quantity: T

    @staticmethod
    def create(symbol: Symbol, quantity: T) -> SymbolQuantity[T]:
        """创建符号物理量。/ Create a symbol quantity.

        Args:
            symbol: 数学符号。/ Mathematical symbol.
            quantity: 物理量值。/ Physical quantity value.

        Returns:
            符号物理量实例。/ Symbol quantity instance.
        """
        return SymbolQuantity(symbol=symbol, quantity=quantity)

    @property
    def name(self) -> str:
        """获取符号名称。/ Get symbol name."""
        return self.symbol.name

    @property
    def index(self) -> int:
        """获取符号索引。/ Get symbol index."""
        return self.symbol.index

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        return f"{self.symbol} = {self.quantity}"
