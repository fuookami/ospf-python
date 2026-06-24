"""符号维度注册表。

Symbol dimension registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class SymbolDimensionRegistry:
    """符号维度注册表，管理符号到维度的映射。

    Symbol dimension registry managing symbol-to-dimension mappings.

    Attributes:
        _registry: 内部映射存储。/ Internal mapping storage.
    """

    _registry: dict[Symbol, object] = field(
        default_factory=dict,
    )

    def register(self, symbol: Symbol, dimension: object) -> None:
        """注册符号维度。/ Register symbol dimension.

        Args:
            symbol: 符号。/ The symbol.
            dimension: 维度值。/ Dimension value.
        """
        self._registry[symbol] = dimension

    def get(self, symbol: Symbol) -> object | None:
        """获取符号维度。/ Get symbol dimension.

        Args:
            symbol: 符号。/ The symbol.

        Returns:
            维度值，未注册时返回 None。
            Dimension value, None if not registered.
        """
        return self._registry.get(symbol)

    def contains(self, symbol: Symbol) -> bool:
        """检查符号是否已注册。/ Check if symbol is registered.

        Args:
            symbol: 符号。/ The symbol.

        Returns:
            是否已注册。/ Whether registered.
        """
        return symbol in self._registry

    def symbols(self) -> list[Symbol]:
        """获取所有已注册符号。/ Get all registered symbols.

        Returns:
            已注册符号列表。/ List of registered symbols.
        """
        return list(self._registry.keys())

    def __len__(self) -> int:
        """获取注册数量。/ Get registration count."""
        return len(self._registry)
