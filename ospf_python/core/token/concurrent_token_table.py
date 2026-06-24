"""线程安全令牌映射表 / Thread-safe token table."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from ospf_python.core.token.token_table import TokenTable

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


class ConcurrentTokenTable:
    """线程安全令牌映射表 / Thread-safe token-to-value mapping.

    在 TokenTable 基础上加锁保护并发访问。
    Wraps TokenTable with a lock for thread-safe access.

    Attributes:
        _table: 内部令牌表 / Inner token table.
        _lock: 读写锁 / Read-write lock.
    """

    def __init__(self) -> None:
        """初始化并发映射表 / Initialize concurrent table."""
        self._table = TokenTable()
        self._lock = threading.Lock()

    def get(self, token: Token) -> object | None:
        """线程安全获取值 / Thread-safe get.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            对应的值或 None / Associated value or None.
        """
        with self._lock:
            return self._table.get(token)

    def set(self, token: Token, value: object) -> None:
        """线程安全设置值 / Thread-safe set.

        Args:
            token: 目标令牌 / Target token.
            value: 要设置的值 / Value to set.
        """
        with self._lock:
            self._table.set(token, value)

    def remove(self, token: Token) -> bool:
        """线程安全移除 / Thread-safe remove.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            是否成功移除 / Whether removal succeeded.
        """
        with self._lock:
            return self._table.remove(token)

    def contains(self, token: Token) -> bool:
        """线程安全包含检查 / Thread-safe contains check.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            是否包含 / Whether the token exists.
        """
        with self._lock:
            return self._table.contains(token)

    def clear(self) -> None:
        """线程安全清空 / Thread-safe clear."""
        with self._lock:
            self._table.clear()

    @property
    def size(self) -> int:
        """获取映射数量 / Get mapping count.

        Returns:
            映射数量 / Number of mappings.
        """
        with self._lock:
            return self._table.size
