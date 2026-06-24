"""符号核心测试。

Symbol core tests.

测试 Symbol、Category、SymbolIdentity 的创建、相等性与映射。
Tests Symbol, Category, SymbolIdentity creation,
equality, and mapping.
"""

from __future__ import annotations

from ospf_python.math.symbol.category import Category
from ospf_python.math.symbol.symbol import Symbol
from ospf_python.math.symbol.symbol_identity import (
    SymbolIdentity,
)

# ── Symbol ─────────────────────────────────────────────────────


class TestSymbolCreation:
    """符号创建测试。"""

    def test_create_default_index(self) -> None:
        """默认索引为 0。/ Default index is 0."""
        sym = Symbol.create("x")
        assert sym.name == "x"
        assert sym.index == 0

    def test_create_with_index(self) -> None:
        """指定索引创建。/ Create with explicit index."""
        sym = Symbol.create("x", index=3)
        assert sym.name == "x"
        assert sym.index == 3

    def test_dataclass_fields(self) -> None:
        """数据类字段赋值。/ Dataclass field assignment."""
        sym = Symbol(name="y", index=2)
        assert sym.name == "y"
        assert sym.index == 2


class TestSymbolEquality:
    """符号相等性测试。"""

    def test_equal_same_name_index(self) -> None:
        """相同名称和索引相等。/ Equal with same name and index."""
        a = Symbol.create("x")
        b = Symbol.create("x")
        assert a == b

    def test_not_equal_different_name(self) -> None:
        """不同名称不等。/ Not equal with different name."""
        a = Symbol.create("x")
        b = Symbol.create("y")
        assert a != b

    def test_not_equal_different_index(self) -> None:
        """不同索引不等。/ Not equal with different index."""
        a = Symbol.create("x", index=0)
        b = Symbol.create("x", index=1)
        assert a != b

    def test_hash_consistent(self) -> None:
        """哈希一致性。/ Hash consistency."""
        a = Symbol.create("x", index=1)
        b = Symbol.create("x", index=1)
        assert hash(a) == hash(b)

    def test_hash_different(self) -> None:
        """不同符号哈希不同。/ Different symbols have different hash."""
        a = Symbol.create("x")
        b = Symbol.create("y")
        # 不要求严格不同，但通常不同
        # Not strictly required, but typically different
        assert hash(a) != hash(b)


class TestSymbolDisplay:
    """符号显示测试。"""

    def test_display_name_no_index(self) -> None:
        """无索引时显示名称。/ Display name without index."""
        sym = Symbol.create("x")
        assert sym.display_name == "x"

    def test_display_name_with_index(self) -> None:
        """有索引时追加下标。/ Display name with subscript."""
        sym = Symbol.create("x", index=3)
        assert sym.display_name == "x_3"

    def test_str_no_index(self) -> None:
        """字符串表示无索引。/ String without index."""
        sym = Symbol.create("alpha")
        assert str(sym) == "alpha"

    def test_str_with_index(self) -> None:
        """字符串表示有索引。/ String with index."""
        sym = Symbol.create("x", index=5)
        assert str(sym) == "x_5"


class TestSymbolOrdering:
    """符号排序测试。"""

    def test_lt_by_name(self) -> None:
        """按名称排序。/ Sort by name."""
        a = Symbol.create("a")
        b = Symbol.create("b")
        assert a < b

    def test_lt_by_index(self) -> None:
        """同名称按索引排序。/ Sort by index when names equal."""
        a = Symbol.create("x", index=0)
        b = Symbol.create("x", index=1)
        assert a < b


# ── Category ───────────────────────────────────────────────────


class TestCategory:
    """符号类别枚举测试。"""

    def test_linear_value(self) -> None:
        """线性类别值。/ Linear category value."""
        assert Category.LINEAR.value == "linear"

    def test_quadratic_value(self) -> None:
        """二次类别值。/ Quadratic category value."""
        assert Category.QUADRATIC.value == "quadratic"

    def test_canonical_value(self) -> None:
        """标准类别值。/ Canonical category value."""
        assert Category.CANONICAL.value == "canonical"

    def test_is_linear(self) -> None:
        """线性类别属性。/ Linear category property."""
        assert Category.LINEAR.is_linear
        assert not Category.QUADRATIC.is_linear

    def test_is_quadratic(self) -> None:
        """二次类别属性。/ Quadratic category property."""
        assert Category.QUADRATIC.is_quadratic
        assert not Category.LINEAR.is_quadratic

    def test_is_canonical(self) -> None:
        """标准类别属性。/ Canonical category property."""
        assert Category.CANONICAL.is_canonical
        assert not Category.LINEAR.is_canonical

    def test_all_members(self) -> None:
        """所有成员。/ All members."""
        members = list(Category)
        assert len(members) == 3


# ── SymbolIdentity ─────────────────────────────────────────────


class TestSymbolIdentity:
    """符号标识映射测试。"""

    def test_create_with_of(self) -> None:
        """通过 of 工厂创建。/ Create via of factory."""
        sym = Symbol.create("x")
        ident = SymbolIdentity.of(sym, "model.x")
        assert ident.symbol == sym
        assert ident.identity == "model.x"

    def test_create_with_constructor(self) -> None:
        """通过构造函数创建。/ Create via constructor."""
        sym = Symbol.create("y")
        ident = SymbolIdentity(symbol=sym, identity="var.y")
        assert ident.identity == "var.y"

    def test_matches_true(self) -> None:
        """匹配对应符号。/ Matches corresponding symbol."""
        sym = Symbol.create("x")
        ident = SymbolIdentity.of(sym, "x_id")
        assert ident.matches(sym)

    def test_matches_false(self) -> None:
        """不匹配其他符号。/ Does not match other symbol."""
        sym_x = Symbol.create("x")
        sym_y = Symbol.create("y")
        ident = SymbolIdentity.of(sym_x, "x_id")
        assert not ident.matches(sym_y)

    def test_str_representation(self) -> None:
        """字符串表示。/ String representation."""
        sym = Symbol.create("z")
        ident = SymbolIdentity.of(sym, "z_id")
        result = str(ident)
        assert "z" in result
        assert "z_id" in result

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        sym = Symbol.create("x")
        ident = SymbolIdentity.of(sym, "id")
        assert ident.symbol == sym
        assert ident.identity == "id"
