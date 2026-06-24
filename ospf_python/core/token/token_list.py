"""令牌有序集合 / Ordered token collection."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


class TokenList:
    """令牌有序集合 / Ordered collection of tokens.

    维护令牌的插入顺序，支持按索引快速查找。
    Maintains insertion order of tokens with fast index-based
    lookup.

    Attributes:
        _items: 内部令牌列表 / Internal token list.
        _index_map: 索引到位置的映射 / Index-to-position map.
    """

    def __init__(self) -> None:
        """初始化空令牌列表 / Initialize empty token list."""
        self._items: list[Token] = []
        self._index_map: dict[int, int] = {}

    def add(self, token: Token) -> None:
        """添加令牌 / Add token.

        Args:
            token: 待添加的令牌 / Token to add.
        """
        pos = len(self._items)
        self._items.append(token)
        self._index_map[token.index] = pos

    def get_by_index(self, index: int) -> Token | None:
        """按索引获取令牌 / Get token by index.

        Args:
            index: 令牌索引 / Token index.

        Returns:
            令牌或 None / Token or None.
        """
        pos = self._index_map.get(index)
        if pos is None:
            return None
        return self._items[pos]

    def remove_by_index(self, index: int) -> bool:
        """按索引移除令牌 / Remove token by index.

        Args:
            index: 令牌索引 / Token index.

        Returns:
            是否成功移除 / Whether removal succeeded.
        """
        pos = self._index_map.pop(index, None)
        if pos is None:
            return False
        self._items.pop(pos)
        # 重建索引映射 / Rebuild index map
        self._index_map = {t.index: i for i, t in enumerate(self._items)}
        return True

    def contains(self, index: int) -> bool:
        """判断是否包含指定索引 / Check if index exists.

        Args:
            index: 令牌索引 / Token index.

        Returns:
            是否包含 / Whether the index exists.
        """
        return index in self._index_map

    @property
    def size(self) -> int:
        """获取令牌数量 / Get token count.

        Returns:
            令牌数量 / Number of tokens.
        """
        return len(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Token]:
        return iter(self._items)

    def __bool__(self) -> bool:
        return len(self._items) > 0
