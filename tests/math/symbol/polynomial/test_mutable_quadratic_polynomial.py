"""可变二次多项式测试。

Mutable quadratic polynomial tests.

测试 MutableQuadraticPolynomial 的创建、项操作、求值和转换。
Tests MutableQuadraticPolynomial creation, term operations,
evaluation, and conversion.
"""

from __future__ import annotations

import pytest

from ospf_python.math.symbol.monomial.quadratic_monomial import (
    QuadraticMonomial,
)
from ospf_python.math.symbol.polynomial.mutable_quadratic_polynomial import (
    MutableQuadraticPolynomial,
)
from ospf_python.math.symbol.polynomial.quadratic_polynomial import (
    QuadraticPolynomial,
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
def xy_term(x: Symbol, y: Symbol) -> QuadraticMonomial:
    """二次项 1.0 * x * y。/ Quadratic term 1.0 * x * y."""
    return QuadraticMonomial.create(lhs=x, rhs=y)


@pytest.fixture()
def x2_term(x: Symbol) -> QuadraticMonomial:
    """二次项 1.0 * x * x。/ Quadratic term 1.0 * x * x."""
    return QuadraticMonomial.create(lhs=x, rhs=x)


# ── Creation tests ───────────────────────────────────────────────


class TestMutableQuadraticPolynomialCreation:
    """可变二次多项式创建测试。"""

    def test_zero(self) -> None:
        """零多项式。/ Zero polynomial."""
        p = MutableQuadraticPolynomial.zero()
        assert p.is_zero
        assert p.degree == 0
        assert p.constant == 0.0

    def test_default_constructor(self) -> None:
        """默认构造函数。/ Default constructor."""
        p = MutableQuadraticPolynomial()
        assert p.is_zero
        assert len(p.quadratic_terms) == 0
        assert len(p.linear_terms) == 0

    def test_initial_state(self) -> None:
        """初始状态检查。/ Initial state check."""
        p = MutableQuadraticPolynomial()
        assert p.quadratic_terms == []
        assert p.linear_terms == {}
        assert p.constant == 0.0


# ── Term addition tests ─────────────────────────────────────────


class TestMutableQuadraticPolynomialAddTerms:
    """可变二次多项式添加项测试。"""

    def test_add_quadratic_term(
        self, xy_term: QuadraticMonomial
    ) -> None:
        """添加二次项。/ Add quadratic term."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        assert len(p.quadratic_terms) == 1
        assert p.degree == 2

    def test_add_multiple_quadratic_terms(
        self,
        xy_term: QuadraticMonomial,
        x2_term: QuadraticMonomial,
    ) -> None:
        """添加多个二次项。/ Add multiple quadratic terms."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        p.add_quadratic_term(x2_term)
        assert len(p.quadratic_terms) == 2

    def test_add_linear_coefficient(
        self, x: Symbol
    ) -> None:
        """添加线性系数。/ Add linear coefficient."""
        p = MutableQuadraticPolynomial()
        p.add_linear_coefficient(x, 3.0)
        assert p.linear_terms[x] == 3.0
        assert p.degree == 1

    def test_add_linear_coefficient_accumulate(
        self, x: Symbol
    ) -> None:
        """累加线性系数。/ Accumulate linear coefficient."""
        p = MutableQuadraticPolynomial()
        p.add_linear_coefficient(x, 2.0)
        p.add_linear_coefficient(x, 3.0)
        assert p.linear_terms[x] == 5.0

    def test_add_constant(self) -> None:
        """添加常数项。/ Add constant term."""
        p = MutableQuadraticPolynomial()
        p.add_constant(5.0)
        assert p.constant == 5.0

    def test_add_constant_twice(self) -> None:
        """两次添加常数项。/ Add constant twice."""
        p = MutableQuadraticPolynomial()
        p.add_constant(3.0)
        p.add_constant(4.0)
        assert p.constant == 7.0


# ── Term removal tests ───────────────────────────────────────────


class TestMutableQuadraticPolynomialRemoveTerms:
    """可变二次多项式移除项测试。"""

    def test_remove_quadratic_term(
        self, xy_term: QuadraticMonomial
    ) -> None:
        """移除二次项。/ Remove quadratic term."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        p.remove_quadratic_term(xy_term)
        assert len(p.quadratic_terms) == 0

    def test_remove_quadratic_term_not_present(
        self, xy_term: QuadraticMonomial
    ) -> None:
        """移除不存在的二次项引发错误。/ Remove absent term raises."""
        p = MutableQuadraticPolynomial()
        with pytest.raises(ValueError):
            p.remove_quadratic_term(xy_term)


# ── Property tests ───────────────────────────────────────────────


class TestMutableQuadraticPolynomialProperties:
    """可变二次多项式属性测试。"""

    def test_degree_zero(self) -> None:
        """零多项式次数为 0。/ Degree 0 for zero polynomial."""
        p = MutableQuadraticPolynomial()
        assert p.degree == 0

    def test_degree_one(
        self, x: Symbol
    ) -> None:
        """仅线性项时次数为 1。/ Degree 1 with linear terms."""
        p = MutableQuadraticPolynomial()
        p.add_linear_coefficient(x, 2.0)
        assert p.degree == 1

    def test_degree_two(
        self, xy_term: QuadraticMonomial
    ) -> None:
        """有二次项时次数为 2。/ Degree 2 with quadratic terms."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        assert p.degree == 2

    def test_is_zero_empty(self) -> None:
        """空多项式为零。/ Empty polynomial is zero."""
        p = MutableQuadraticPolynomial()
        assert p.is_zero

    def test_is_zero_with_constant(self) -> None:
        """非零常数不是零多项式。/ Non-zero constant is not zero."""
        p = MutableQuadraticPolynomial()
        p.add_constant(1.0)
        assert not p.is_zero

    def test_is_zero_with_linear(
        self, x: Symbol
    ) -> None:
        """有线性项不是零多项式。/ Linear terms not zero."""
        p = MutableQuadraticPolynomial()
        p.add_linear_coefficient(x, 1.0)
        assert not p.is_zero

    def test_is_zero_with_quadratic(
        self, xy_term: QuadraticMonomial
    ) -> None:
        """有二次项不是零多项式。/ Quadratic terms not zero."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        assert not p.is_zero

    def test_symbols_deduplicated(
        self, x2_term: QuadraticMonomial, x: Symbol
    ) -> None:
        """符号去重。/ Symbols are deduplicated."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(x2_term)
        p.add_linear_coefficient(x, 1.0)
        syms = p.symbols
        assert len(syms) == 1
        assert syms[0] == x

    def test_symbols_multiple(
        self,
        xy_term: QuadraticMonomial,
        x: Symbol,
        y: Symbol,
    ) -> None:
        """多个符号。/ Multiple symbols."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        syms = p.symbols
        assert x in syms
        assert y in syms

    def test_quadratic_terms_returns_copy(
        self, xy_term: QuadraticMonomial
    ) -> None:
        """二次项列表返回副本。/ Quadratic terms returns copy."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        terms = p.quadratic_terms
        terms.clear()
        assert len(p.quadratic_terms) == 1

    def test_linear_terms_returns_copy(
        self, x: Symbol
    ) -> None:
        """线性项映射返回副本。/ Linear terms returns copy."""
        p = MutableQuadraticPolynomial()
        p.add_linear_coefficient(x, 2.0)
        terms = p.linear_terms
        terms.clear()
        assert x in p.linear_terms


# ── Evaluate tests ───────────────────────────────────────────────


class TestMutableQuadraticPolynomialEvaluate:
    """可变二次多项式求值测试。"""

    def test_evaluate_constant_only(self) -> None:
        """仅常数项求值。/ Evaluate constant only."""
        p = MutableQuadraticPolynomial()
        p.add_constant(7.0)
        assert p.evaluate({}) == 7.0

    def test_evaluate_linear_only(
        self, x: Symbol
    ) -> None:
        """仅线性项求值。/ Evaluate linear only."""
        p = MutableQuadraticPolynomial()
        p.add_linear_coefficient(x, 3.0)
        assert p.evaluate({x: 2.0}) == 6.0

    def test_evaluate_quadratic_only(
        self, xy_term: QuadraticMonomial,
        x: Symbol,
        y: Symbol,
    ) -> None:
        """仅二次项求值。/ Evaluate quadratic only."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(
            QuadraticMonomial.create(
                coefficient=2.0, lhs=x, rhs=y,
            )
        )
        assert p.evaluate({x: 3.0, y: 4.0}) == 24.0

    def test_evaluate_full_polynomial(
        self, x: Symbol, y: Symbol
    ) -> None:
        """完整多项式求值。/ Evaluate full polynomial."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(
            QuadraticMonomial.create(
                coefficient=2.0, lhs=x, rhs=y,
            )
        )
        p.add_linear_coefficient(x, 3.0)
        p.add_constant(1.0)
        # 2*3*4 + 3*3 + 1 = 24 + 9 + 1 = 34
        assert p.evaluate({x: 3.0, y: 4.0}) == 34.0

    def test_evaluate_missing_binding(
        self, x: Symbol
    ) -> None:
        """缺失绑定默认为 0。/ Missing binding defaults to 0."""
        p = MutableQuadraticPolynomial()
        p.add_linear_coefficient(x, 5.0)
        assert p.evaluate({}) == 0.0

    def test_evaluate_zero_polynomial(self) -> None:
        """零多项式求值为 0。/ Zero polynomial evaluates to 0."""
        p = MutableQuadraticPolynomial()
        assert p.evaluate({}) == 0.0


# ── Clear tests ──────────────────────────────────────────────────


class TestMutableQuadraticPolynomialClear:
    """可变二次多项式清空测试。"""

    def test_clear(
        self,
        xy_term: QuadraticMonomial,
        x: Symbol,
    ) -> None:
        """清空所有项。/ Clear all terms."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        p.add_linear_coefficient(x, 2.0)
        p.add_constant(3.0)
        p.clear()
        assert p.is_zero
        assert p.degree == 0

    def test_clear_empty(self) -> None:
        """清空空多项式无错误。/ Clear empty polynomial."""
        p = MutableQuadraticPolynomial()
        p.clear()
        assert p.is_zero


# ── Conversion tests ─────────────────────────────────────────────


class TestMutableQuadraticPolynomialConversion:
    """可变二次多项式转换测试。"""

    def test_to_immutable_zero(self) -> None:
        """零多项式转换。/ Convert zero polynomial."""
        p = MutableQuadraticPolynomial()
        imm = p.to_immutable()
        assert isinstance(imm, QuadraticPolynomial)
        assert imm.is_zero

    def test_to_immutable_preserves_data(
        self, x: Symbol, y: Symbol
    ) -> None:
        """转换保留数据。/ Conversion preserves data."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(
            QuadraticMonomial.create(
                coefficient=2.0, lhs=x, rhs=y,
            )
        )
        p.add_linear_coefficient(x, 3.0)
        p.add_constant(5.0)
        imm = p.to_immutable()
        assert len(imm.quadratic_terms) == 1
        assert imm.linear_terms[x] == 3.0
        assert imm.constant == 5.0
        assert imm.evaluate({x: 3.0, y: 4.0}) == 38.0

    def test_to_immutable_independence(
        self, x: Symbol
    ) -> None:
        """转换后修改不影响不可变副本。/ Mutations after conversion do not affect immutable copy."""
        p = MutableQuadraticPolynomial()
        p.add_linear_coefficient(x, 2.0)
        imm = p.to_immutable()
        p.add_linear_coefficient(x, 3.0)
        assert imm.linear_terms[x] == 2.0


# ── String representation tests ──────────────────────────────────


class TestMutableQuadraticPolynomialStr:
    """可变二次多项式字符串测试。"""

    def test_str_zero(self) -> None:
        """零多项式字符串。/ Zero polynomial string."""
        p = MutableQuadraticPolynomial()
        s = str(p)
        assert "0.0" in s

    def test_str_with_terms(
        self, xy_term: QuadraticMonomial
    ) -> None:
        """带项的字符串。/ String with terms."""
        p = MutableQuadraticPolynomial()
        p.add_quadratic_term(xy_term)
        p.add_constant(5.0)
        s = str(p)
        assert "x" in s
        assert "5.0" in s
