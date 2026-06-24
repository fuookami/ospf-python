"""TokenList 测试。

测试令牌列表的增删查改和迭代。
Tests TokenList add, remove, query, and iteration.
"""

from __future__ import annotations

from ospf_python.core.token.token import Token
from ospf_python.core.token.token_list import TokenList


class TestTokenListBasic:
    """基础操作测试 / Basic operation tests."""

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

    def test_add_multiple_and_order(self) -> None:
        """多个令牌保持顺序。/ Multiple tokens maintain order."""
        tl = TokenList()
        tokens = [Token(name=f"t{i}", index=i) for i in range(5)]
        for t in tokens:
            tl.add(t)
        assert list(tl) == tokens


class TestTokenListQuery:
    """查询测试 / Query tests."""

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


class TestTokenListRemove:
    """移除测试 / Remove tests."""

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


class TestTokenListIteration:
    """迭代测试 / Iteration tests."""

    def test_iter(self) -> None:
        """迭代令牌。/ Iterate tokens."""
        tl = TokenList()
        t1 = Token(name="a", index=0)
        t2 = Token(name="b", index=1)
        tl.add(t1)
        tl.add(t2)
        assert list(tl) == [t1, t2]

    def test_iter_empty(self) -> None:
        """空列表迭代。/ Empty list iteration."""
        tl = TokenList()
        assert list(tl) == []
