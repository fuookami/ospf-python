"""TokenCacheKey 测试。

测试缓存键的创建、相等性和哈希。
Tests TokenCacheKey creation, equality, and hashing.
"""

from __future__ import annotations

from ospf_python.core.token.token import Token
from ospf_python.core.token.token_cache_key import TokenCacheKey


class TestTokenCacheKeyCreation:
    """创建测试 / Creation tests."""

    def test_create_cache_key(self) -> None:
        """创建缓存键。/ Create cache key."""
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        assert key.token == t
        assert key.operation == "eval"

    def test_create_factory(self) -> None:
        """工厂方法创建。/ Factory method create."""
        t = Token(name="x", index=0)
        key = TokenCacheKey.create(token=t, operation="norm")
        assert key.operation == "norm"

    def test_str_format(self) -> None:
        """字符串格式。/ String format."""
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        assert str(key) == "x[0]:eval"


class TestTokenCacheKeyEquality:
    """相等性测试 / Equality tests."""

    def test_equality(self) -> None:
        """相等性。/ Equality."""
        t = Token(name="x", index=0)
        k1 = TokenCacheKey(token=t, operation="eval")
        k2 = TokenCacheKey(token=t, operation="eval")
        assert k1 == k2

    def test_inequality_different_op(self) -> None:
        """不同操作不等。/ Different operation not equal."""
        t = Token(name="x", index=0)
        k1 = TokenCacheKey(token=t, operation="eval")
        k2 = TokenCacheKey(token=t, operation="norm")
        assert k1 != k2

    def test_hash_consistency(self) -> None:
        """哈希一致性。/ Hash consistency."""
        t = Token(name="x", index=0)
        k1 = TokenCacheKey(token=t, operation="eval")
        k2 = TokenCacheKey(token=t, operation="eval")
        assert hash(k1) == hash(k2)

    def test_usable_as_dict_key(self) -> None:
        """可用作字典键。/ Usable as dict key."""
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        d = {key: 42}
        assert d[TokenCacheKey(token=t, operation="eval")] == 42
