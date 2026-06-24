"""令牌模块测试。

测试令牌、令牌集合、映射表、缓存和注册功能。
Tests tokens, token lists, tables, caching, and registration.
"""

from __future__ import annotations

import threading

import pytest

from ospf_python.core.token import (
    ConcurrentTokenTable,
    Token,
    TokenCacheContext,
    TokenCacheKey,
    TokenList,
    TokenTable,
    TokenTableRegistrationSupport,
)

# ---------------------------------------------------------------------------
# Token 测试
# ---------------------------------------------------------------------------


class TestToken:
    """令牌基础测试 / Token basic tests."""

    def test_create_token(self) -> None:
        """创建令牌。/ Create token."""
        t = Token(name="x", index=0)
        assert t.name == "x"
        assert t.index == 0

    def test_create_factory(self) -> None:
        """工厂方法创建令牌。/ Factory method creates token."""
        t = Token.create(name="y", index=1)
        assert t.name == "y"
        assert t.index == 1

    def test_str_format(self) -> None:
        """字符串格式正确。/ String format is correct."""
        t = Token(name="x", index=5)
        assert str(t) == "x[5]"

    def test_is_frozen(self) -> None:
        """令牌不可变。/ Token is frozen."""
        t = Token(name="x", index=0)
        with pytest.raises(AttributeError):
            t.name = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        """令牌相等性。/ Token equality."""
        t1 = Token(name="x", index=0)
        t2 = Token(name="x", index=0)
        assert t1 == t2

    def test_inequality_different_name(self) -> None:
        """不同名称不等。/ Different name not equal."""
        t1 = Token(name="x", index=0)
        t2 = Token(name="y", index=0)
        assert t1 != t2

    def test_inequality_different_index(self) -> None:
        """不同索引不等。/ Different index not equal."""
        t1 = Token(name="x", index=0)
        t2 = Token(name="x", index=1)
        assert t1 != t2

    def test_hash_consistency(self) -> None:
        """哈希一致性。/ Hash consistency."""
        t1 = Token(name="x", index=0)
        t2 = Token(name="x", index=0)
        assert hash(t1) == hash(t2)

    def test_usable_in_set(self) -> None:
        """可用于集合。/ Usable in set."""
        t1 = Token(name="x", index=0)
        t2 = Token(name="x", index=0)
        s = {t1, t2}
        assert len(s) == 1

    def test_usable_as_dict_key(self) -> None:
        """可用作字典键。/ Usable as dict key."""
        t = Token(name="x", index=0)
        d = {t: "value"}
        assert d[Token(name="x", index=0)] == "value"


# ---------------------------------------------------------------------------
# TokenList 测试
# ---------------------------------------------------------------------------


class TestTokenList:
    """令牌列表测试 / Token list tests."""

    def test_empty_list(self) -> None:
        """空列表。/ Empty list."""
        tl = TokenList()
        assert tl.size == 0
        assert len(tl) == 0
        assert not tl

    def test_add_token(self) -> None:
        """添加令牌。/ Add token."""
        tl = TokenList()
        tl.add(Token(name="x", index=0))
        assert tl.size == 1
        assert tl

    def test_get_by_index(self) -> None:
        """按索引获取。/ Get by index."""
        tl = TokenList()
        t = Token(name="x", index=5)
        tl.add(t)
        assert tl.get_by_index(5) == t

    def test_get_missing_index_returns_none(self) -> None:
        """不存在的索引返回 None。/ Missing index returns None."""
        tl = TokenList()
        assert tl.get_by_index(99) is None

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        tl = TokenList()
        tl.add(Token(name="x", index=0))
        assert tl.contains(0) is True
        assert tl.contains(1) is False

    def test_remove_by_index(self) -> None:
        """按索引移除。/ Remove by index."""
        tl = TokenList()
        tl.add(Token(name="x", index=0))
        assert tl.remove_by_index(0) is True
        assert tl.size == 0

    def test_remove_missing_returns_false(self) -> None:
        """移除不存在的返回 False。/ Remove missing returns False."""
        tl = TokenList()
        assert tl.remove_by_index(99) is False

    def test_iter(self) -> None:
        """迭代令牌。/ Iterate tokens."""
        tl = TokenList()
        t1 = Token(name="a", index=0)
        t2 = Token(name="b", index=1)
        tl.add(t1)
        tl.add(t2)
        assert list(tl) == [t1, t2]

    def test_add_multiple_and_order(self) -> None:
        """多个令牌保持顺序。/ Multiple tokens maintain order."""
        tl = TokenList()
        tokens = [Token(name=f"t{i}", index=i) for i in range(5)]
        for t in tokens:
            tl.add(t)
        assert list(tl) == tokens


# ---------------------------------------------------------------------------
# TokenTable 测试
# ---------------------------------------------------------------------------


class TestTokenTable:
    """令牌映射表测试 / Token table tests."""

    def test_empty_table(self) -> None:
        """空映射表。/ Empty table."""
        tt = TokenTable()
        assert tt.size == 0
        assert not tt

    def test_set_and_get(self) -> None:
        """设置并获取。/ Set and get."""
        tt = TokenTable()
        t = Token(name="x", index=0)
        tt.set(t, 42)
        assert tt.get(t) == 42

    def test_get_missing_returns_none(self) -> None:
        """不存在的键返回 None。/ Missing key returns None."""
        tt = TokenTable()
        t = Token(name="x", index=0)
        assert tt.get(t) is None

    def test_overwrite_value(self) -> None:
        """覆盖已有值。/ Overwrite existing value."""
        tt = TokenTable()
        t = Token(name="x", index=0)
        tt.set(t, 1)
        tt.set(t, 2)
        assert tt.get(t) == 2

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        tt = TokenTable()
        t = Token(name="x", index=0)
        assert tt.contains(t) is False
        tt.set(t, "v")
        assert tt.contains(t) is True

    def test_remove(self) -> None:
        """移除映射。/ Remove mapping."""
        tt = TokenTable()
        t = Token(name="x", index=0)
        tt.set(t, "v")
        assert tt.remove(t) is True
        assert tt.contains(t) is False

    def test_remove_missing_returns_false(self) -> None:
        """移除不存在返回 False。/ Remove missing returns False."""
        tt = TokenTable()
        t = Token(name="x", index=0)
        assert tt.remove(t) is False

    def test_clear(self) -> None:
        """清空映射表。/ Clear table."""
        tt = TokenTable()
        tt.set(Token(name="a", index=0), 1)
        tt.set(Token(name="b", index=1), 2)
        tt.clear()
        assert tt.size == 0

    def test_keys_values_items(self) -> None:
        """键值对遍历。/ Keys, values, items."""
        tt = TokenTable()
        t0 = Token(name="a", index=0)
        t1 = Token(name="b", index=1)
        tt.set(t0, "x")
        tt.set(t1, "y")
        assert set(tt.keys()) == {0, 1}
        assert set(tt.values()) == {"x", "y"}
        assert set(tt.items()) == {(0, "x"), (1, "y")}

    def test_size_after_operations(self) -> None:
        """操作后大小正确。/ Size after operations."""
        tt = TokenTable()
        t0 = Token(name="a", index=0)
        t1 = Token(name="b", index=1)
        tt.set(t0, 1)
        tt.set(t1, 2)
        assert tt.size == 2
        tt.remove(t0)
        assert tt.size == 1


# ---------------------------------------------------------------------------
# ConcurrentTokenTable 测试
# ---------------------------------------------------------------------------


class TestConcurrentTokenTable:
    """并发令牌表测试 / Concurrent token table tests."""

    def test_basic_set_get(self) -> None:
        """基本设置和获取。/ Basic set and get."""
        ctt = ConcurrentTokenTable()
        t = Token(name="x", index=0)
        ctt.set(t, 42)
        assert ctt.get(t) == 42

    def test_thread_safety(self) -> None:
        """线程安全写入。/ Thread-safe writes."""
        ctt = ConcurrentTokenTable()
        errors: list[Exception] = []

        def writer(start: int) -> None:
            try:
                for i in range(100):
                    t = Token(name=f"t{start + i}", index=start + i)
                    ctt.set(t, i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i * 100,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert ctt.size == 400

    def test_remove(self) -> None:
        """移除操作。/ Remove operation."""
        ctt = ConcurrentTokenTable()
        t = Token(name="x", index=0)
        ctt.set(t, 1)
        assert ctt.remove(t) is True
        assert ctt.get(t) is None

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        ctt = ConcurrentTokenTable()
        t = Token(name="x", index=0)
        assert ctt.contains(t) is False
        ctt.set(t, 1)
        assert ctt.contains(t) is True

    def test_clear(self) -> None:
        """清空操作。/ Clear operation."""
        ctt = ConcurrentTokenTable()
        ctt.set(Token(name="a", index=0), 1)
        ctt.clear()
        assert ctt.size == 0


# ---------------------------------------------------------------------------
# TokenCacheKey 测试
# ---------------------------------------------------------------------------


class TestTokenCacheKey:
    """缓存键测试 / Cache key tests."""

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


# ---------------------------------------------------------------------------
# TokenCacheContext 测试
# ---------------------------------------------------------------------------


class TestTokenCacheContext:
    """缓存上下文测试 / Cache context tests."""

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

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        ctx = TokenCacheContext()
        t = Token(name="x", index=0)
        key = TokenCacheKey(token=t, operation="eval")
        assert ctx.contains(key) is False
        ctx.put(key, 42)
        assert ctx.contains(key) is True


# ---------------------------------------------------------------------------
# TokenTableRegistrationSupport 测试
# ---------------------------------------------------------------------------


class TestTokenTableRegistrationSupport:
    """注册辅助工具测试 / Registration support tests."""

    def test_register_new_token(self) -> None:
        """注册新令牌。/ Register new token."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        assert reg.register(t, "value") is True
        assert reg.is_registered(t) is True

    def test_register_existing_token(self) -> None:
        """注册已存在令牌。/ Register existing token."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        reg.register(t, "v1")
        assert reg.register(t, "v2") is False

    def test_unregister(self) -> None:
        """注销令牌。/ Unregister token."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        reg.register(t, "v")
        assert reg.unregister(t) is True
        assert reg.is_registered(t) is False

    def test_unregister_missing_returns_false(self) -> None:
        """注销不存在返回 False。/ Unregister missing."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        assert reg.unregister(t) is False

    def test_get_value(self) -> None:
        """获取注册值。/ Get registered value."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        reg.register(t, 42)
        assert reg.get_value(t) == 42

    def test_get_value_missing_returns_none(self) -> None:
        """获取不存在返回 None。/ Get missing returns None."""
        reg = TokenTableRegistrationSupport()
        t = Token(name="x", index=0)
        assert reg.get_value(t) is None

    def test_registered_count(self) -> None:
        """已注册数量。/ Registered count."""
        reg = TokenTableRegistrationSupport()
        assert reg.registered_count == 0
        reg.register(Token(name="a", index=0), 1)
        reg.register(Token(name="b", index=1), 2)
        assert reg.registered_count == 2

    def test_clear(self) -> None:
        """清空注册。/ Clear registrations."""
        reg = TokenTableRegistrationSupport()
        reg.register(Token(name="a", index=0), 1)
        reg.register(Token(name="b", index=1), 2)
        reg.clear()
        assert reg.registered_count == 0
