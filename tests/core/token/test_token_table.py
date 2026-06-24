"""TokenTable 测试。

测试令牌映射表的增删查改。
Tests TokenTable set, get, remove, and clear.
"""

from __future__ import annotations

from ospf_python.core.token.token import Token
from ospf_python.core.token.token_table import TokenTable


class TestTokenTableBasic:
    """基础操作测试 / Basic operation tests."""

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


class TestTokenTableQuery:
    """查询测试 / Query tests."""

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        tt = TokenTable()
        t = Token(name="x", index=0)
        assert tt.contains(t) is False
        tt.set(t, "v")
        assert tt.contains(t) is True

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


class TestTokenTableRemove:
    """移除测试 / Remove tests."""

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
