"""IntermediateSymbol 测试。

测试中间符号的创建、属性和字符串格式。
Tests IntermediateSymbol creation, attributes, and string format.
"""

from __future__ import annotations

import pytest

from ospf_python.core.symbol.intermediate_symbol import (
    IntermediateSymbol,
)
from ospf_python.core.symbol.intermediate_symbol_expression_support import (
    IntermediateSymbolExpressionSupport,
)
from ospf_python.core.token.token import Token


class TestIntermediateSymbolCreation:
    """创建测试 / Creation tests."""

    def test_create(self) -> None:
        """创建中间符号。/ Create intermediate symbol."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(
            token=t,
            expression_name="sum_x",
        )
        assert s.name == "x"
        assert s.index == 0
        assert s.expression_name == "sum_x"

    def test_str(self) -> None:
        """字符串格式。/ String format."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(
            token=t,
            expression_name="sum",
        )
        assert str(s) == "sum(x[0])"

    def test_frozen(self) -> None:
        """不可变。/ Frozen."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(
            token=t,
            expression_name="sum",
        )
        with pytest.raises(AttributeError):
            s.expression_name = "changed"  # type: ignore[misc]


class TestIntermediateSymbolExpressionSupport:
    """表达式支持测试 / Expression support tests."""

    def test_register_and_resolve(self) -> None:
        """注册并解析。/ Register and resolve."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(
            token=t,
            expression_name="sum",
        )
        support = IntermediateSymbolExpressionSupport()
        support.register(s, "x + 1")
        assert support.resolve(s) == "x + 1"

    def test_resolve_missing(self) -> None:
        """解析不存在返回 None。/ Resolve missing."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(
            token=t,
            expression_name="sum",
        )
        support = IntermediateSymbolExpressionSupport()
        assert support.resolve(s) is None

    def test_is_registered(self) -> None:
        """判断已注册。/ Check registered."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(
            token=t,
            expression_name="sum",
        )
        support = IntermediateSymbolExpressionSupport()
        assert support.is_registered(s) is False
        support.register(s, "x + 1")
        assert support.is_registered(s) is True

    def test_count(self) -> None:
        """计数。/ Count."""
        support = IntermediateSymbolExpressionSupport()
        assert support.count == 0
        t = Token(name="x", index=0)
        s = IntermediateSymbol(
            token=t,
            expression_name="sum",
        )
        support.register(s, "x + 1")
        assert support.count == 1

    def test_clear(self) -> None:
        """清空。/ Clear."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(
            token=t,
            expression_name="sum",
        )
        support = IntermediateSymbolExpressionSupport()
        support.register(s, "x + 1")
        support.clear()
        assert support.count == 0
