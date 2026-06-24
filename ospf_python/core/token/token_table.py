"""令牌映射表 / Token-to-value mapping table."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


class TokenTable:
    """令牌映射表 / Token-to-value mapping table.

    将令牌映射到任意值，支持增删查改。
    Maps tokens to arbitrary values with CRUD support.

    Attributes:
        _data: 内部映射存储 / Internal mapping storage.
    """

    def __init__(self) -> None:
        """初始化空映射表 / Initialize empty table."""
        self._data: dict[int, object] = {}

    def get(self, token: Token) -> object | None:
        """获取令牌对应的值 / Get value for token.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            对应的值或 None / Associated value or None.
        """
        return self._data.get(token.index)

    def set(self, token: Token, value: object) -> None:
        """设置令牌对应的值 / Set value for token.

        Args:
            token: 目标令牌 / Target token.
            value: 要设置的值 / Value to set.
        """
        self._data[token.index] = value

    def remove(self, token: Token) -> bool:
        """移除令牌映射 / Remove token mapping.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            是否成功移除 / Whether removal succeeded.
        """
        if token.index in self._data:
            del self._data[token.index]
            return True
        return False

    def contains(self, token: Token) -> bool:
        """判断是否包含令牌 / Check if token exists.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            是否包含 / Whether the token exists.
        """
        return token.index in self._data

    def clear(self) -> None:
        """清空映射表 / Clear the table."""
        self._data.clear()

    @property
    def size(self) -> int:
        """获取映射数量 / Get mapping count.

        Returns:
            映射数量 / Number of mappings.
        """
        return len(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return len(self._data) > 0

    def keys(self) -> list[int]:
        """获取所有键 / Get all keys.

        Returns:
            键列表 / List of keys.
        """
        return list(self._data.keys())

    def values(self) -> list[object]:
        """获取所有值 / Get all values.

        Returns:
            值列表 / List of values.
        """
        return list(self._data.values())

    def items(self) -> Iterator[tuple[int, object]]:
        """获取所有键值对 / Get all key-value pairs.

        Returns:
            键值对迭代器 / Key-value pair iterator.
        """
        return iter(self._data.items())
