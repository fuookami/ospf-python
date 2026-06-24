"""带维度符号测试。

Dimensioned symbol tests.

测试 DimensionedSymbol 的创建和属性。
Tests DimensionedSymbol creation and properties.
"""

from __future__ import annotations

from ospf_python.math.symbol.dimensioned_symbol import DimensionedSymbol
from ospf_python.math.symbol.symbol import Symbol

# ── DimensionedSymbol ───────────────────────────────────────────


class TestDimensionedSymbol:
    """带维度符号测试。"""

    def test_creation(self) -> None:
        """创建带维度符号。/ Create dimensioned symbol."""
        x = Symbol.create("x")
        ds = DimensionedSymbol.create(x, 3)
        assert ds.symbol == x
        assert ds.dimension == 3

    def test_name_property(self) -> None:
        """名称属性。/ Name property."""
        x = Symbol.create("x")
        ds = DimensionedSymbol.create(x, 2)
        assert ds.name == "x"

    def test_index_property(self) -> None:
        """索引属性。/ Index property."""
        x = Symbol.create("x", index=5)
        ds = DimensionedSymbol.create(x, 2)
        assert ds.index == 5

    def test_str(self) -> None:
        """字符串表示。/ String representation."""
        x = Symbol.create("x")
        ds = DimensionedSymbol.create(x, 3)
        assert str(ds) == "x(3)"

    def test_generic_type(self) -> None:
        """泛型类型。/ Generic type."""
        x = Symbol.create("x")
        ds = DimensionedSymbol.create(x, "meters")
        assert ds.dimension == "meters"

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        x = Symbol.create("x")
        ds = DimensionedSymbol.create(x, 1)
        assert ds.symbol == x
        assert ds.dimension == 1
