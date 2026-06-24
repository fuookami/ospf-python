"""符号定义。

Symbol definition.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Symbol:
    """数学符号，由名称和索引唯一标识。

    Mathematical symbol uniquely identified by name and index.

    Attributes:
        name: 符号名称。/ Symbol name.
        index: 符号索引。/ Symbol index.
    """

    name: str
    index: int

    @staticmethod
    def create(name: str, index: int = 0) -> Symbol:
        """创建符号。/ Create a symbol.

        Args:
            name: 符号名称。/ Symbol name.
            index: 符号索引，默认 0。/ Symbol index, defaults to 0.

        Returns:
            新符号实例。/ New symbol instance.
        """
        return Symbol(name=name, index=index)

    @property
    def display_name(self) -> str:
        """获取显示名称。/ Get display name.

        索引为 0 时仅返回名称，否则追加下标。
        Returns name only when index is 0, otherwise appends subscript.
        """
        if self.index == 0:
            return self.name
        return f"{self.name}_{self.index}"

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        return self.display_name

    def __hash__(self) -> int:
        """哈希值。/ Hash value."""
        return hash((self.name, self.index))
