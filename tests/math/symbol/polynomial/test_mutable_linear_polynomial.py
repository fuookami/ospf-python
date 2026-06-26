"""可变线性多项式测试。

Mutable linear polynomial tests.

测试 MutableLinearPolynomial 的创建、项操作、求值和转换。
Tests MutableLinearPolynomial creation, term operations,
evaluation, and conversion.
"""

from __future__ import annotations

import pytest

from ospf_python.math.symbol.monomial.linear_monomial import (
    LinearMonomial,
)
from ospf_python.math.symbol.polynomial.linear_polynomial import (
    LinearPolynomial,
)
from ospf_python.math.symbol.polynomial.mutable_linear_polynomial import (
    MutableLinearPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture()
def x() -> Symbol:
    """符号 x。/ Symbol x."""
    return Symbol.create("x")


@pytest.fixture()
def y() -> Symbol:
    """符号 y。/ Symbol y."""
    return Symbol.create("y")


@pytest.fixture()
def x_term(x: Symbol) -> LinearMonomial:
    """线性项 1.0 * x。/ Linear term 1.0 * x."""
    return LinearMonomial.create(x)


@pytest.fixture()
def y_term(y: Symbol) -> LinearMonomial:
    """线性项 1.0 * y。/ Linear term 1.0 * y."""
    return LinearMonomial.create(y)


# ── Creation tests ───────────────────────────────────────────────


class TestMutableLinearPolynomialCreation:
    """可变线性多项式创建测试。"""

    def test_zero(self) -> None:
        """零多项式。/ Zero polynomial."""
        p = MutableLinearPolynomial.zero()
        assert p.is_zero
        assert p.degree == 0
        assert p.term_count == 0

    def test_default_constructor(self) -> None:
        """默认构造函数。/ Default constructor."""
        p = MutableLinearPolynomial()
        assert p.is_zero
        assert len(p.terms) == 0
        assert p.constant == 0.0

    def test_initial_state(self) -> None:
        """初始状态检查。/ Initial state check."""
        p = MutableLinearPolynomial()
        assert p.terms == []
        assert p.constant == 0.0


# ── Term addition tests ─────────────────────────────────────────


class TestMutableLinearPolynomialAddTerms:
    """可变线性多项式添加项测试。"""

    def test_add_term(self, x_term: LinearMonomial) -> None:
        """添加线性项。/ Add linear term."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        assert p.term_count == 1
        assert p.degree == 1

    def test_add_multiple_terms(
        self,
        x_term: LinearMonomial,
        y_term: LinearMonomial,
    ) -> None:
        """添加多个线性项。/ Add multiple linear terms."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        p.add_term(y_term)
        assert p.term_count == 2

    def test_add_constant(self) -> None:
        """添加常数项。/ Add constant term."""
        p = MutableLinearPolynomial()
        p.add_constant(5.0)
        assert p.constant == 5.0

    def test_add_constant_twice(self) -> None:
        """两次添加常数项。/ Add constant twice."""
        p = MutableLinearPolynomial()
        p.add_constant(3.0)
        p.add_constant(4.0)
        assert p.constant == 7.0


# ── Term removal tests ───────────────────────────────────────────


class TestMutableLinearPolynomialRemoveTerms:
    """可变线性多项式移除项测试。"""

    def test_remove_term(self, x_term: LinearMonomial) -> None:
        """移除线性项。/ Remove linear term."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        p.remove_term(x_term)
        assert p.term_count == 0

    def test_remove_term_not_present(
        self, x_term: LinearMonomial
    ) -> None:
        """移除不存在的项引发错误。/ Remove absent term raises."""
        p = MutableLinearPolynomial()
        with pytest.raises(ValueError):
            p.remove_term(x_term)


# ── Property tests ───────────────────────────────────────────────


class TestMutableLinearPolynomialProperties:
    """可变线性多项式属性测试。"""

    def test_degree_zero(self) -> None:
        """零多项式次数为 0。/ Degree 0 for zero polynomial."""
        p = MutableLinearPolynomial()
        assert p.degree == 0

    def test_degree_one(self, x_term: LinearMonomial) -> None:
        """线性多项式次数为 1。/ Degree 1 for linear polynomial."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        assert p.degree == 1

    def test_is_zero_empty(self) -> None:
        """空多项式为零。/ Empty polynomial is zero."""
        p = MutableLinearPolynomial()
        assert p.is_zero

    def test_is_zero_with_constant(self) -> None:
        """非零常数不是零多项式。/ Non-zero constant is not zero."""
        p = MutableLinearPolynomial()
        p.add_constant(1.0)
        assert not p.is_zero

    def test_is_zero_with_term(
        self, x_term: LinearMonomial
    ) -> None:
        """有项不是零多项式。/ With terms is not zero."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        assert not p.is_zero

    def test_term_count(self, x_term: LinearMonomial) -> None:
        """项数统计。/ Term count."""
        p = MutableLinearPolynomial()
        assert p.term_count == 0
        p.add_term(x_term)
        assert p.term_count == 1

    def test_symbols_deduplicated(
        self, x: Symbol, x_term: LinearMonomial
    ) -> None:
        """符号去重。/ Symbols deduplicated."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        p.add_term(LinearMonomial.create(x, coefficient=2.0))
        assert len(p.symbols) == 1
        assert p.symbols[0] == x

    def test_symbols_multiple(
        self,
        x_term: LinearMonomial,
        y_term: LinearMonomial,
        x: Symbol,
        y: Symbol,
    ) -> None:
        """多个符号。/ Multiple symbols."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        p.add_term(y_term)
        assert x in p.symbols
        assert y in p.symbols

    def test_terms_returns_copy(
        self, x_term: LinearMonomial
    ) -> None:
        """项列表返回副本。/ Terms returns copy."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        terms = p.terms
        terms.clear()
        assert p.term_count == 1


# ── Evaluate tests ───────────────────────────────────────────────


class TestMutableLinearPolynomialEvaluate:
    """可变线性多项式求值测试。"""

    def test_evaluate_constant_only(self) -> None:
        """仅常数项求值。/ Evaluate constant only."""
        p = MutableLinearPolynomial()
        p.add_constant(7.0)
        assert p.evaluate({}) == 7.0

    def test_evaluate_single_term(
        self, x: Symbol, x_term: LinearMonomial
    ) -> None:
        """单项求值。/ Evaluate single term."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        assert p.evaluate({x: 3.0}) == 3.0

    def test_evaluate_with_coefficient(
        self, x: Symbol
    ) -> None:
        """带系数求值。/ Evaluate with coefficient."""
        p = MutableLinearPolynomial()
        p.add_term(LinearMonomial.create(x, coefficient=4.0))
        assert p.evaluate({x: 2.0}) == 8.0

    def test_evaluate_full_polynomial(
        self, x: Symbol, y: Symbol
    ) -> None:
        """完整多项式求值。/ Evaluate full polynomial."""
        p = MutableLinearPolynomial()
        p.add_term(LinearMonomial.create(x, coefficient=2.0))
        p.add_term(LinearMonomial.create(y, coefficient=3.0))
        p.add_constant(1.0)
        # 2*5 + 3*4 + 1 = 10 + 12 + 1 = 23
        assert p.evaluate({x: 5.0, y: 4.0}) == 23.0

    def test_evaluate_missing_binding(
        self, x: Symbol, x_term: LinearMonomial
    ) -> None:
        """缺失绑定默认为 0。/ Missing binding defaults to 0."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        assert p.evaluate({}) == 0.0

    def test_evaluate_zero_polynomial(self) -> None:
        """零多项式求值为 0。/ Zero polynomial evaluates to 0."""
        p = MutableLinearPolynomial()
        assert p.evaluate({}) == 0.0


# ── Clear tests ──────────────────────────────────────────────────


class TestMutableLinearPolynomialClear:
    """可变线性多项式清空测试。"""

    def test_clear(
        self, x_term: LinearMonomial
    ) -> None:
        """清空所有项。/ Clear all terms."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        p.add_constant(3.0)
        p.clear()
        assert p.is_zero
        assert p.degree == 0

    def test_clear_empty(self) -> None:
        """清空空多项式无错误。/ Clear empty polynomial."""
        p = MutableLinearPolynomial()
        p.clear()
        assert p.is_zero


# ── Conversion tests ─────────────────────────────────────────────


class TestMutableLinearPolynomialConversion:
    """可变线性多项式转换测试。"""

    def test_to_immutable_zero(self) -> None:
        """零多项式转换。/ Convert zero polynomial."""
        p = MutableLinearPolynomial()
        imm = p.to_immutable()
        assert isinstance(imm, LinearPolynomial)
        assert imm.is_zero

    def test_to_immutable_preserves_data(
        self, x: Symbol
    ) -> None:
        """转换保留数据。/ Conversion preserves data."""
        p = MutableLinearPolynomial()
        p.add_term(LinearMonomial.create(x, coefficient=3.0))
        p.add_constant(5.0)
        imm = p.to_immutable()
        assert imm.term_count == 1
        assert imm.constant == 5.0
        assert imm.evaluate({x: 2.0}) == 11.0

    def test_to_immutable_independence(
        self, x: Symbol
    ) -> None:
        """转换后修改不影响副本。/ Mutations do not affect immutable copy."""
        p = MutableLinearPolynomial()
        p.add_term(LinearMonomial.create(x, coefficient=2.0))
        imm = p.to_immutable()
        p.add_term(LinearMonomial.create(x, coefficient=3.0))
        assert imm.term_count == 1


# ── String representation tests ──────────────────────────────────


class TestMutableLinearPolynomialStr:
    """可变线性多项式字符串测试。"""

    def test_str_zero(self) -> None:
        """零多项式字符串。/ Zero polynomial string."""
        p = MutableLinearPolynomial()
        s = str(p)
        assert "0.0" in s

    def test_str_with_terms(
        self, x_term: LinearMonomial
    ) -> None:
        """带项的字符串。/ String with terms."""
        p = MutableLinearPolynomial()
        p.add_term(x_term)
        p.add_constant(5.0)
        s = str(p)
        assert "x" in s
        assert "5.0" in s
