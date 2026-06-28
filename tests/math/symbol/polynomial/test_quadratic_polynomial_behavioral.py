"""Behavioral tests for QuadraticPolynomial.

Targets: degree, is_zero, symbols, evaluate, __str__,
zero(), of() factory methods, and edge cases.
"""

from __future__ import annotations

import pytest

from ospf_python.math.symbol.monomial.quadratic_monomial import QuadraticMonomial
from ospf_python.math.symbol.polynomial.quadratic_polynomial import QuadraticPolynomial
from ospf_python.math.symbol.symbol import Symbol


class TestQuadraticPolynomialConstruction:
    """二次多项式构建测试。/ QuadraticPolynomial construction tests."""

    def test_zero_factory(self) -> None:
        """zero() 创建零多项式。/ zero() creates zero polynomial."""
        p = QuadraticPolynomial.zero()
        assert p.is_zero
        assert p.degree == 0

    def test_of_factory_with_quadratic_terms(self) -> None:
        """of() 从二次项构建。/ of() builds from quadratic terms."""
        x = Symbol.create(name="x", index=0)
        qm = QuadraticMonomial.create(coefficient=1.0, lhs=x, rhs=x)
        p = QuadraticPolynomial.of(qm)
        assert len(p.quadratic_terms) == 1

    def test_of_factory_with_linear_and_constant(self) -> None:
        """of() 含线性项和常数。/ of() with linear and constant."""
        x = Symbol.create(name="x", index=0)
        p = QuadraticPolynomial.of(
            linear={x: 3.0},
            constant=5.0,
        )
        assert p.linear_terms[x] == pytest.approx(3.0)
        assert p.constant == pytest.approx(5.0)

    def test_default_construction(self) -> None:
        """默认构造创建零多项式。/ Default construction creates zero."""
        p = QuadraticPolynomial()
        assert p.is_zero
        assert p.quadratic_terms == []
        assert p.linear_terms == {}
        assert p.constant == pytest.approx(0.0)


class TestQuadraticPolynomialProperties:
    """二次多项式属性测试。/ QuadraticPolynomial properties tests."""

    def test_degree_quadratic(self) -> None:
        """二次项时 degree 为 2。/ Degree is 2 when quadratic terms present."""
        x = Symbol.create(name="x", index=0)
        qm = QuadraticMonomial.create(coefficient=1.0, lhs=x, rhs=x)
        p = QuadraticPolynomial(quadratic_terms=[qm])
        assert p.degree == 2

    def test_degree_linear(self) -> None:
        """只有线性项时 degree 为 1。/ Degree is 1 when only linear terms."""
        x = Symbol.create(name="x", index=0)
        p = QuadraticPolynomial(linear_terms={x: 3.0})
        assert p.degree == 1

    def test_degree_constant(self) -> None:
        """只有常数项时 degree 为 0。/ Degree is 0 when only constant."""
        p = QuadraticPolynomial(constant=5.0)
        assert p.degree == 0

    def test_is_zero_true(self) -> None:
        """零多项式判断。/ Zero polynomial check."""
        assert QuadraticPolynomial.zero().is_zero is True

    def test_is_zero_false_with_constant(self) -> None:
        """非零常数不是零多项式。/ Non-zero constant is not zero."""
        p = QuadraticPolynomial(constant=1.0)
        assert p.is_zero is False

    def test_is_zero_false_with_linear(self) -> None:
        """有线性项不是零多项式。/ Linear terms make it non-zero."""
        x = Symbol.create(name="x", index=0)
        p = QuadraticPolynomial(linear_terms={x: 1.0})
        assert p.is_zero is False

    def test_is_zero_false_with_quadratic(self) -> None:
        """有二次项不是零多项式。/ Quadratic terms make it non-zero."""
        x = Symbol.create(name="x", index=0)
        qm = QuadraticMonomial.create(coefficient=1.0, lhs=x, rhs=x)
        p = QuadraticPolynomial(quadratic_terms=[qm])
        assert p.is_zero is False

    def test_symbols_deduplicated(self) -> None:
        """符号去重。/ Symbols are deduplicated."""
        x = Symbol.create(name="x", index=0)
        y = Symbol.create(name="y", index=1)
        qm = QuadraticMonomial.create(coefficient=2.0, lhs=x, rhs=y)
        p = QuadraticPolynomial(
            quadratic_terms=[qm],
            linear_terms={x: 1.0, y: 3.0},
        )
        syms = p.symbols
        # x and y should appear once each
        assert len(syms) == 2

    def test_symbols_from_linear_only(self) -> None:
        """线性项符号。/ Symbols from linear terms."""
        x = Symbol.create(name="x", index=0)
        y = Symbol.create(name="y", index=1)
        p = QuadraticPolynomial(linear_terms={x: 1.0, y: 2.0})
        syms = p.symbols
        assert len(syms) == 2


class TestQuadraticPolynomialEvaluate:
    """二次多项式求值测试。/ QuadraticPolynomial evaluation tests."""

    def test_evaluate_constant_only(self) -> None:
        """常数项求值。/ Evaluate constant only."""
        p = QuadraticPolynomial(constant=5.0)
        assert p.evaluate({}) == pytest.approx(5.0)

    def test_evaluate_linear(self) -> None:
        """线性项求值。/ Evaluate linear terms."""
        x = Symbol.create(name="x", index=0)
        p = QuadraticPolynomial(linear_terms={x: 3.0}, constant=2.0)
        assert p.evaluate({x: 4.0}) == pytest.approx(14.0)

    def test_evaluate_quadratic(self) -> None:
        """二次项求值。/ Evaluate quadratic terms."""
        x = Symbol.create(name="x", index=0)
        qm = QuadraticMonomial.create(coefficient=2.0, lhs=x, rhs=x)
        p = QuadraticPolynomial(quadratic_terms=[qm])
        # 2 * x * x = 2 * 3 * 3 = 18
        assert p.evaluate({x: 3.0}) == pytest.approx(18.0)

    def test_evaluate_missing_binding_defaults_zero(self) -> None:
        """缺失绑定默认为零。/ Missing binding defaults to zero."""
        x = Symbol.create(name="x", index=0)
        p = QuadraticPolynomial(linear_terms={x: 5.0})
        assert p.evaluate({}) == pytest.approx(0.0)

    def test_evaluate_full_polynomial(self) -> None:
        """完整多项式求值。/ Evaluate full polynomial."""
        x = Symbol.create(name="x", index=0)
        y = Symbol.create(name="y", index=1)
        qm = QuadraticMonomial.create(coefficient=2.0, lhs=x, rhs=y)
        p = QuadraticPolynomial(
            quadratic_terms=[qm],
            linear_terms={x: 3.0},
            constant=1.0,
        )
        # 2*2*4 + 3*2 + 1 = 16 + 6 + 1 = 23
        assert p.evaluate({x: 2.0, y: 4.0}) == pytest.approx(23.0)


class TestQuadraticPolynomialStr:
    """二次多项式字符串表示测试。/ QuadraticPolynomial __str__ tests."""

    def test_str_empty(self) -> None:
        """零多项式字符串。/ Zero polynomial string."""
        p = QuadraticPolynomial.zero()
        assert "0" in str(p)

    def test_str_constant(self) -> None:
        """常数项字符串。/ Constant string."""
        p = QuadraticPolynomial(constant=5.0)
        result = str(p)
        assert "5" in result

    def test_str_linear_coefficient_one(self) -> None:
        """线性项系数为 1 时不显示系数。/ Linear coeff=1 omits coefficient."""
        x = Symbol.create(name="x", index=0)
        p = QuadraticPolynomial(linear_terms={x: 1.0})
        result = str(p)
        assert "x" in result

    def test_str_linear_general_coefficient(self) -> None:
        """线性项一般系数字符串。/ Linear general coefficient string."""
        x = Symbol.create(name="x", index=0)
        p = QuadraticPolynomial(linear_terms={x: 3.0})
        result = str(p)
        assert "3" in result
        assert "x" in result

    def test_frozen_dataclass(self) -> None:
        """frozen dataclass 不可变。/ Frozen dataclass is immutable."""
        p = QuadraticPolynomial(constant=1.0)
        with pytest.raises(AttributeError):
            p.constant = 2.0  # type: ignore[misc]
