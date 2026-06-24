"""令牌缓存上下文 / Token cache context."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token
    from ospf_python.core.token.token_cache_key import TokenCacheKey


class TokenCacheContext:
    """令牌缓存上下文 / Caching context for tokens.

    管理令牌操作的缓存，支持查找、存储和失效。
    Manages caching for token operations with lookup,
    storage, and invalidation support.

    Attributes:
        _cache: 缓存存储 / Cache storage.
    """

    def __init__(self) -> None:
        """初始化缓存上下文 / Initialize cache context."""
        self._cache: dict[TokenCacheKey, object] = {}

    def get(self, key: TokenCacheKey) -> object | None:
        """获取缓存值 / Get cached value.

        Args:
            key: 缓存键 / Cache key.

        Returns:
            缓存值或 None / Cached value or None.
        """
        return self._cache.get(key)

    def put(
        self,
        key: TokenCacheKey,
        value: object,
    ) -> None:
        """存储缓存值 / Store cached value.

        Args:
            key: 缓存键 / Cache key.
            value: 要缓存的值 / Value to cache.
        """
        self._cache[key] = value

    def invalidate(self, key: TokenCacheKey) -> bool:
        """使缓存项失效 / Invalidate cache entry.

        Args:
            key: 缓存键 / Cache key.

        Returns:
            是否成功失效 / Whether invalidation succeeded.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def invalidate_token(self, token: Token) -> int:
        """使令牌相关的所有缓存失效 / Invalidate all caches
        for a token.

        Args:
            token: 目标令牌 / Target token.

        Returns:
            失效的缓存项数量 / Number of invalidated entries.
        """
        keys_to_remove = [k for k in self._cache if k.token == token]
        for key in keys_to_remove:
            del self._cache[key]
        return len(keys_to_remove)

    def clear(self) -> None:
        """清空缓存 / Clear all caches."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """获取缓存大小 / Get cache size.

        Returns:
            缓存项数量 / Number of cached entries.
        """
        return len(self._cache)

    def contains(self, key: TokenCacheKey) -> bool:
        """判断缓存是否包含键 / Check if cache contains key.

        Args:
            key: 缓存键 / Cache key.

        Returns:
            是否包含 / Whether the key exists.
        """
        return key in self._cache
