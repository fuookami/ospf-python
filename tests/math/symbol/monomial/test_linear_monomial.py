"""线性单项式测试。

Linear monomial tests.

测试 LinearMonomial 的创建、求值和操作。
Tests LinearMonomial creation, evaluation, and operations.
"""

from __future__ import annotations

from ospf_python.math.symbol.monomial.linear_monomial import (
    LinearMonomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ── LinearMonomial creation ─────────────────────────────────────


class TestLinearMonomialCreation:
    """线性单项式创建测试。"""

    def test_create_default(self) -> None:
        """默认系数创建。/ Default coefficient creation."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x)
        assert m.coefficient == 1.0
        assert m.symbol == x

    def test_create_with_coefficient(self) -> None:
        """指定系数创建。/ Create with coefficient."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x, coefficient=2.5)
        assert m.coefficient == 2.5


# ── LinearMonomial properties ───────────────────────────────────


class TestLinearMonomialProperties:
    """线性单项式属性测试。"""

    def test_degree_always_one(self) -> None:
        """次数始终为 1。/ Degree is always 1."""
        x = Symbol.create("x")
        assert LinearMonomial.create(x).degree == 1

    def test_name_and_index(self) -> None:
        """名称和索引。/ Name and index."""
        x = Symbol.create("x", index=2)
        m = LinearMonomial.create(x)
        assert m.name == "x"
        assert m.index == 2


# ── LinearMonomial operations ───────────────────────────────────


class TestLinearMonomialOperations:
    """线性单项式操作测试。"""

    def test_evaluate(self) -> None:
        """求值。/ Evaluate."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x, coefficient=3.0)
        assert m.evaluate(4.0) == 12.0

    def test_negate(self) -> None:
        """取反。/ Negate."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x, coefficient=2.0)
        neg = m.negate()
        assert neg.coefficient == -2.0

    def test_scale(self) -> None:
        """缩放。/ Scale."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x, coefficient=2.0)
        scaled = m.scale(3.0)
        assert scaled.coefficient == 6.0

    def test_str_unit_coefficient(self) -> None:
        """系数为 1 时的字符串。/ String when coefficient is 1."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x)
        assert str(m) == "x"
