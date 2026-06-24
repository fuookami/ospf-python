"""符号标识映射。

Symbol identity mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class SymbolIdentity:
    """符号到标识的映射。

    Mapping from symbol to its identity.

    Attributes:
        symbol: 符号。/ The symbol.
        identity: 标识字符串。/ Identity string.
    """

    symbol: Symbol
    identity: str

    @staticmethod
    def of(symbol: Symbol, identity: str) -> SymbolIdentity:
        """创建符号标识映射。/ Create a symbol identity mapping.

        Args:
            symbol: 符号。/ The symbol.
            identity: 标识字符串。/ Identity string.

        Returns:
            符号标识映射实例。/ Symbol identity mapping instance.
        """
        return SymbolIdentity(symbol=symbol, identity=identity)

    def matches(self, symbol: Symbol) -> bool:
        """检查是否匹配给定符号。/ Check if matches the given symbol.

        Args:
            symbol: 待检查符号。/ Symbol to check.

        Returns:
            是否匹配。/ Whether matched.
        """
        return self.symbol == symbol

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        return f"{self.symbol} -> {self.identity}"
