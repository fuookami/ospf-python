"""可变标准多项式测试。

Mutable canonical polynomial tests.

测试 MutableCanonicalPolynomial 的创建、添加项、移除项、
清空、求值、次数、符号、不可变转换和字符串表示。
Tests MutableCanonicalPolynomial creation, add_term,
remove_term, clear, evaluate, degree, symbols,
to_immutable, and string representation.
"""

from __future__ import annotations

import pytest

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.polynomial.mutable_canonical_polynomial import (
    MutableCanonicalPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ── helpers ────────────────────────────────────────────────────

_x = Symbol.create("x")
_y = Symbol.create("y")

_m_x = CanonicalMonomial.single(_x)
_m_y = CanonicalMonomial.single(_y)
_m_c3 = CanonicalMonomial.constant(3.0)
_m_2x = CanonicalMonomial.single(_x, coefficient=2.0)


# ── creation tests ─────────────────────────────────────────────


class TestMutableCanonicalPolynomialCreation:
    """创建测试。/ Creation tests."""

    def test_default_creation(self) -> None:
        """默认构造为空多项式。/ Default creates empty."""
        p = MutableCanonicalPolynomial()
        assert p.is_zero is True
        assert p.term_count == 0

    def test_zero_factory(self) -> None:
        """零多项式工厂。/ Zero polynomial factory."""
        p = MutableCanonicalPolynomial.zero()
        assert p.is_zero is True
        assert p.degree == 0

    def test_with_initial_terms(self) -> None:
        """带初始项构造。/ Construction with initial terms."""
        p = MutableCanonicalPolynomial(_terms=[_m_x, _m_c3])
        assert p.term_count == 2
        assert p.is_zero is False


# ── add_term tests ─────────────────────────────────────────────


class TestMutableCanonicalPolynomialAddTerm:
    """添加项测试。/ add_term tests."""

    def test_add_single(self) -> None:
        """添加单项式。/ Add single monomial."""
        p = MutableCanonicalPolynomial.zero()
        p.add_term(_m_x)
        assert p.term_count == 1

    def test_add_multiple(self) -> None:
        """添加多项。/ Add multiple terms."""
        p = MutableCanonicalPolynomial.zero()
        p.add_term(_m_x)
        p.add_term(_m_y)
        p.add_term(_m_c3)
        assert p.term_count == 3

    def test_add_duplicate(self) -> None:
        """添加重复项。/ Add duplicate term."""
        p = MutableCanonicalPolynomial.zero()
        p.add_term(_m_x)
        p.add_term(_m_x)
        assert p.term_count == 2


# ── remove_term tests ──────────────────────────────────────────


class TestMutableCanonicalPolynomialRemoveTerm:
    """移除项测试。/ remove_term tests."""

    def test_remove_existing(self) -> None:
        """移除存在的项。/ Remove existing term."""
        p = MutableCanonicalPolynomial(_terms=[_m_x, _m_y])
        p.remove_term(_m_x)
        assert p.term_count == 1
        assert p.terms == [_m_y]

    def test_remove_nonexistent_raises(self) -> None:
        """移除不存在的项抛异常。

        Remove nonexistent term raises ValueError.
        """
        p = MutableCanonicalPolynomial(_terms=[_m_x])
        with pytest.raises(ValueError):
            p.remove_term(_m_y)

    def test_remove_all(self) -> None:
        """移除所有项。/ Remove all terms."""
        p = MutableCanonicalPolynomial(_terms=[_m_x, _m_y])
        p.remove_term(_m_x)
        p.remove_term(_m_y)
        assert p.is_zero is True


# ── clear tests ────────────────────────────────────────────────


class TestMutableCanonicalPolynomialClear:
    """清空测试。/ clear tests."""

    def test_clear_nonempty(self) -> None:
        """清空非空多项式。/ Clear non-empty polynomial."""
        p = MutableCanonicalPolynomial(
            _terms=[_m_x, _m_y, _m_c3],
        )
        p.clear()
        assert p.is_zero is True
        assert p.term_count == 0

    def test_clear_already_empty(self) -> None:
        """清空空多项式不抛异常。

        Clear empty polynomial does not raise.
        """
        p = MutableCanonicalPolynomial.zero()
        p.clear()
        assert p.is_zero is True


# ── terms property tests ───────────────────────────────────────


class TestMutableCanonicalPolynomialTerms:
    """terms 属性测试。/ terms property tests."""

    def test_terms_returns_copy(self) -> None:
        """返回列表副本。/ Returns list copy."""
        p = MutableCanonicalPolynomial(_terms=[_m_x])
        t = p.terms
        t.append(_m_y)
        assert p.term_count == 1

    def test_terms_order_preserved(self) -> None:
        """保持添加顺序。/ Order preserved."""
        p = MutableCanonicalPolynomial()
        p.add_term(_m_c3)
        p.add_term(_m_x)
        assert p.terms == [_m_c3, _m_x]


# ── degree tests ───────────────────────────────────────────────


class TestMutableCanonicalPolynomialDegree:
    """次数测试。/ degree tests."""

    def test_degree_empty(self) -> None:
        """空多项式次数为 0。/ Empty degree is 0."""
        p = MutableCanonicalPolynomial.zero()
        assert p.degree == 0

    def test_degree_constant(self) -> None:
        """常数次数为 0。/ Constant degree is 0."""
        p = MutableCanonicalPolynomial(_terms=[_m_c3])
        assert p.degree == 0

    def test_degree_linear(self) -> None:
        """线性次数为 1。/ Linear degree is 1."""
        p = MutableCanonicalPolynomial(_terms=[_m_x])
        assert p.degree == 1

    def test_degree_quadratic(self) -> None:
        """二次次数为 2。/ Quadratic degree is 2."""
        m_x2 = CanonicalMonomial.single(_x, power=2)
        p = MutableCanonicalPolynomial(_terms=[m_x2])
        assert p.degree == 2

    def test_degree_mixed(self) -> None:
        """混合项取最大次数。/ Mixed terms take max degree."""
        p = MutableCanonicalPolynomial(
            _terms=[_m_x, _m_c3, _m_y],
        )
        assert p.degree == 1


# ── is_zero / term_count tests ─────────────────────────────────


class TestMutableCanonicalPolynomialZeroCheck:
    """零多项式检查测试。/ is_zero tests."""

    def test_empty_is_zero(self) -> None:
        """空为零。/ Empty is zero."""
        assert MutableCanonicalPolynomial.zero().is_zero

    def test_nonempty_not_zero(self) -> None:
        """非空不为零。/ Non-empty is not zero."""
        p = MutableCanonicalPolynomial(_terms=[_m_c3])
        assert p.is_zero is False

    def test_term_count(self) -> None:
        """项数统计。/ Term count."""
        p = MutableCanonicalPolynomial(
            _terms=[_m_x, _m_y],
        )
        assert p.term_count == 2


# ── symbols tests ──────────────────────────────────────────────


class TestMutableCanonicalPolynomialSymbols:
    """符号测试。/ symbols tests."""

    def test_symbols_empty(self) -> None:
        """空多项式无符号。/ Empty has no symbols."""
        p = MutableCanonicalPolynomial.zero()
        assert p.symbols == []

    def test_symbols_unique(self) -> None:
        """符号去重。/ Symbols deduplicated."""
        m_x2 = CanonicalMonomial.single(_x, power=2)
        p = MutableCanonicalPolynomial(
            _terms=[_m_x, m_x2],
        )
        assert p.symbols == [_x]

    def test_symbols_multiple(self) -> None:
        """多符号。/ Multiple symbols."""
        p = MutableCanonicalPolynomial(
            _terms=[_m_x, _m_y],
        )
        assert _x in p.symbols
        assert _y in p.symbols


# ── evaluate tests ─────────────────────────────────────────────


class TestMutableCanonicalPolynomialEvaluate:
    """求值测试。/ evaluate tests."""

    def test_evaluate_empty(self) -> None:
        """空多项式求值为 0。/ Empty evaluates to 0."""
        p = MutableCanonicalPolynomial.zero()
        assert p.evaluate({_x: 5.0}) == 0.0

    def test_evaluate_constant(self) -> None:
        """常数求值。/ Constant evaluation."""
        p = MutableCanonicalPolynomial(_terms=[_m_c3])
        assert p.evaluate({}) == 3.0

    def test_evaluate_linear(self) -> None:
        """线性求值。/ Linear evaluation."""
        p = MutableCanonicalPolynomial(_terms=[_m_2x])
        assert p.evaluate({_x: 5.0}) == 10.0

    def test_evaluate_polynomial(self) -> None:
        """多项式求值。/ Polynomial evaluation.

        2x + 3 at x=4 equals 11.
        """
        p = MutableCanonicalPolynomial(
            _terms=[_m_2x, _m_c3],
        )
        assert p.evaluate({_x: 4.0}) == 11.0

    def test_evaluate_multivariable(self) -> None:
        """多变量求值。/ Multi-variable evaluation.

        x + y at x=3, y=7 equals 10.
        """
        p = MutableCanonicalPolynomial(
            _terms=[_m_x, _m_y],
        )
        assert p.evaluate({_x: 3.0, _y: 7.0}) == 10.0


# ── to_immutable tests ─────────────────────────────────────────


class TestMutableCanonicalPolynomialToImmutable:
    """不可变转换测试。/ to_immutable tests."""

    def test_to_immutable_type(self) -> None:
        """转换返回 CanonicalPolynomial。

        Returns CanonicalPolynomial.
        """
        p = MutableCanonicalPolynomial(_terms=[_m_x])
        result = p.to_immutable()
        assert isinstance(result, CanonicalPolynomial)

    def test_to_immutable_preserves_terms(self) -> None:
        """转换保留项。/ Conversion preserves terms."""
        p = MutableCanonicalPolynomial(
            _terms=[_m_x, _m_c3],
        )
        result = p.to_immutable()
        assert result.term_count == 2
        assert result.degree == 1

    def test_to_immutable_empty(self) -> None:
        """空多项式转换。/ Empty polynomial conversion."""
        p = MutableCanonicalPolynomial.zero()
        result = p.to_immutable()
        assert result.is_zero is True


# ── __str__ tests ──────────────────────────────────────────────


class TestMutableCanonicalPolynomialStr:
    """字符串表示测试。/ __str__ tests."""

    def test_str_empty(self) -> None:
        """空多项式显示 0。/ Empty shows 0."""
        p = MutableCanonicalPolynomial.zero()
        assert str(p) == "0"

    def test_str_single_term(self) -> None:
        """单项式字符串。/ Single term string."""
        p = MutableCanonicalPolynomial(_terms=[_m_c3])
        s = str(p)
        assert "3" in s

    def test_str_multiple_terms(self) -> None:
        """多项式字符串包含分隔符。

        Polynomial string contains separator.
        """
        p = MutableCanonicalPolynomial(
            _terms=[_m_x, _m_c3],
        )
        s = str(p)
        assert "+" in s
