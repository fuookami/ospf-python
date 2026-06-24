"""TokenCacheContext 测试。

测试缓存上下文的存取、失效和清空。
Tests TokenCacheContext put, get, invalidate, and clear.
"""

from __future__ import annotations

from ospf_python.core.token.token import Token
from ospf_python.core.token.token_cache_context import (
    TokenCacheContext,
)
from ospf_python.core.token.token_cache_key import TokenCacheKey


class TestTokenCacheContextBasic:
    """基础操作测试 / Basic operation tests."""

    def test_empty_cache(self) -> None:
        """空缓存。/ Empty cache."""
        ctx = TokenCacheContext()
        assert ctx.size == 0

    def test_put_and_get(self) -> None:
        """存取操作。/ Put and get."""
        ctx = TokenCacheContext()
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        ctx.put(key, 42)
        assert ctx.get(key) == 42

    def test_get_missing_returns_none(self) -> None:
        """不存在返回 None。/ Missing returns None."""
        ctx = TokenCacheContext()
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        assert ctx.get(key) is None

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        ctx = TokenCacheContext()
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        assert ctx.contains(key) is False
        ctx.put(key, 42)
        assert ctx.contains(key) is True


class TestTokenCacheContextInvalidate:
    """失效测试 / Invalidate tests."""

    def test_invalidate(self) -> None:
        """使缓存失效。/ Invalidate cache."""
        ctx = TokenCacheContext()
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        ctx.put(key, 42)
        assert ctx.invalidate(key) is True
        assert ctx.get(key) is None

    def test_invalidate_missing_returns_false(self) -> None:
        """失效不存在返回 False。/ Invalidate missing."""
        ctx = TokenCacheContext()
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        assert ctx.invalidate(key) is False

    def test_invalidate_token(self) -> None:
        """按令牌失效所有缓存。/ Invalidate all for token."""
        ctx = TokenCacheContext()
        t = Token(name="x", index=0)
        k1 = TokenCacheKey(token=t, operation="eval")
        k2 = TokenCacheKey(token=t, operation="norm")
        ctx.put(k1, 1)
        ctx.put(k2, 2)
        count = ctx.invalidate_token(t)
        assert count == 2
        assert ctx.size == 0

    def test_clear(self) -> None:
        """清空缓存。/ Clear cache."""
        ctx = TokenCacheContext()
        t = Token(name="x", index=0)
        ctx.put(TokenCacheKey(token=t, operation="a"), 1)
        ctx.put(TokenCacheKey(token=t, operation="b"), 2)
        ctx.clear()
        assert ctx.size == 0
