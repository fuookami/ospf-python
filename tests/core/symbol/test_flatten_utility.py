"""FlattenUtility 测试。

测试展平工具的创建和展平操作。
Tests FlattenUtility creation and flatten operations.
"""

from __future__ import annotations

from ospf_python.core.symbol.flatten.flatten_utility import (
    FlattenUtility,
)
from ospf_python.core.token.token import Token


class TestFlattenUtilityBasic:
    """基础测试 / Basic tests."""

    def test_flatten_token_like(self) -> None:
        """展平类令牌对象。/ Flatten token-like object."""
        util = FlattenUtility()
        t = Token(name="x", index=0)
        result = util.flatten(t)
        assert len(result) == 1
        assert result[0] == t

    def test_flatten_nested(self) -> None:
        """展平嵌套结构。/ Flatten nested structure."""

        class Node:
            def __init__(self, tokens):
                self.tokens = tokens

        t1 = Token(name="a", index=0)
        t2 = Token(name="b", index=1)
        t3 = Token(name="c", index=2)
        inner = Node([t2, t3])
        outer = Node([t1, inner])

        util = FlattenUtility()
        result = util.flatten(outer)
        assert len(result) == 3
        assert result == [t1, t2, t3]

    def test_flatten_with_token_attr(self) -> None:
        """展平带 token 属性的对象。/ Flatten with token attr."""
        t = Token(name="x", index=0)

        class Leaf:
            def __init__(self, token):
                self.token = token

        util = FlattenUtility()
        result = util.flatten(Leaf(t))
        assert len(result) == 1
        assert result[0] == t


class TestFlattenUtilityFactory:
    """工厂方法测试 / Factory method tests."""

    def test_create_factory(self) -> None:
        """工厂方法创建。/ Factory method create."""
        util = FlattenUtility.create(max_depth=50)
        assert util._max_depth == 50

    def test_max_depth_respected(self) -> None:
        """最大深度限制。/ Max depth respected."""

        class Node:
            def __init__(self, children):
                self.tokens = children

        leaf = Token(name="x", index=0)
        node = Node([leaf])
        for _ in range(200):
            node = Node([node])

        util = FlattenUtility.create(max_depth=5)
        result = util.flatten(node)
        assert len(result) == 0
