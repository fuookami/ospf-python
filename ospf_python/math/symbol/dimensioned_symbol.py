"""带维度符号。

Dimensioned symbol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")


@dataclass(frozen=True)
class DimensionedSymbol(Generic[T]):
    """带维度的符号，将符号与维度信息关联。

    Symbol with dimension, associating a symbol with dimension info.

    Attributes:
        symbol: 数学符号。/ Mathematical symbol.
        dimension: 维度值。/ Dimension value.
    """

    symbol: Symbol
    dimension: T

    @staticmethod
    def create(symbol: Symbol, dimension: T) -> DimensionedSymbol[T]:
        """创建带维度符号。/ Create a dimensioned symbol.

        Args:
            symbol: 数学符号。/ Mathematical symbol.
            dimension: 维度值。/ Dimension value.

        Returns:
            带维度符号实例。/ Dimensioned symbol instance.
        """
        return DimensionedSymbol(symbol=symbol, dimension=dimension)

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
        return f"{self.symbol}({self.dimension})"
