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

    @staticmethod
    def from_display_name(text: str) -> Symbol:
        """按显示名重建符号，还原 ``name_index`` 形式。

        Rebuild a symbol from its display name, restoring the ``name_index`` form.

        ``display_name`` 对非零索引输出 ``name_index``。不还原索引会让序列化往返得到另一个
        符号（``Symbol('y', 1)`` 变成 ``Symbol('y_1', 0)``），求值时它的绑定查不到，
        整个项被静默丢掉。
        ``display_name`` renders a non-zero index as ``name_index``. Not restoring the index
        makes a serialisation round trip yield a different symbol (``Symbol('y', 1)`` becomes
        ``Symbol('y_1', 0)``), so its bindings are not found at evaluation time and the whole
        term is silently dropped.

        后缀能解析成整数时按索引处理，因此名为 ``y_1`` 且索引为 0 的字面量会被读成
        ``('y', 1)`` —— 两者本来就有相同的显示名，这个格式本身就带歧义。
        A numeric suffix is read as the index, so a literal named ``y_1`` with index 0 reads as
        ``('y', 1)``; both already share one display name, so the format is ambiguous anyway.

        Args:
            text: 显示名。/ Display name.

        Returns:
            符号。/ Symbol.
        """
        name, _, suffix = text.rpartition("_")
        if name and suffix.isdigit():
            return Symbol(name=name, index=int(suffix))
        return Symbol(name=text, index=0)

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
