"""符号标识序列化与反序列化。

Symbol identity serialization and deserialization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolIdentitySerde:
    """符号标识序列化器。

    Handles serialization and deserialization of symbol
    identity (variable name, index, etc.).

    Attributes:
        namespace: 命名空间前缀。/ Namespace prefix.
    """

    namespace: str = ""

    def serialize(self, name: str) -> str:
        """将符号名称序列化为完整标识。

        Serialize a symbol name to a full identity string.

        Args:
            name: 符号名称。/ Symbol name.

        Returns:
            完整标识字符串。/ Full identity string.
        """
        if self.namespace:
            return f"{self.namespace}.{name}"
        return name

    def deserialize(self, data: str) -> str:
        """从完整标识中提取符号名称。

        Extract symbol name from a full identity string.

        Args:
            data: 完整标识字符串。/ Full identity string.

        Returns:
            符号名称。/ Symbol name.
        """
        if self.namespace and data.startswith(f"{self.namespace}."):
            return data[len(self.namespace) + 1 :]
        return data
