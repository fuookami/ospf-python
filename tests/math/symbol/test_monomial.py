"""单项式测试。

Monomial tests.

测试 CanonicalMonomial、LinearMonomial、QuadraticMonomial
的创建、乘法、次数等操作。
Tests CanonicalMonomial, LinearMonomial, QuadraticMonomial
creation, multiplication, degree, and other operations.
"""

from __future__ import annotations

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.monomial.linear_monomial import (
    LinearMonomial,
)
from ospf_python.math.symbol.monomial.quadratic_monomial import (
    QuadraticMonomial,
)
from ospf_python.math.symbol.monomial.quick_ops import (
    divide_monomials,
    mul_monomials,
)
from ospf_python.math.symbol.symbol import Symbol

# ── CanonicalMonomial ──────────────────────────────────────────


class TestCanonicalMonomialCreation:
    """标准单项式创建测试。"""

    def test_constant(self) -> None:
        """常数单项式。/ Constant monomial."""
        m = CanonicalMonomial.constant(5.0)
        assert m.coefficient == 5.0
        assert m.is_constant

    def test_single_symbol(self) -> None:
        """单符号单项式。/ Single-symbol monomial."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x)
        assert m.coefficient == 1.0
        assert x in m.powers
        assert m.powers[x] == 1

    def test_single_with_coefficient(self) -> None:
        """带系数的单符号单项式。/ Single-symbol with coefficient."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x, coefficient=3.0)
        assert m.coefficient == 3.0

    def test_single_with_power(self) -> None:
        """带幂次的单符号单项式。/ Single-symbol with power."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x, power=2)
        assert m.powers[x] == 2


class TestCanonicalMonomialDegree:
    """标准单项式次数测试。"""

    def test_constant_degree_zero(self) -> None:
        """常数次数为 0。/ Constant degree is 0."""
        m = CanonicalMonomial.constant(1.0)
        assert m.degree == 0

    def test_linear_degree(self) -> None:
        """线性次数为 1。/ Linear degree is 1."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x)
        assert m.degree == 1

    def test_quadratic_degree(self) -> None:
        """二次次数为 2。/ Quadratic degree is 2."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x, power=2)
        assert m.degree == 2

    def test_multi_symbol_degree(self) -> None:
        """多符号次数之和。/ Multi-symbol degree sum."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = CanonicalMonomial(coefficient=1.0, powers={x: 2, y: 3})
        assert m.degree == 5


class TestCanonicalMonomialEvaluate:
    """标准单项式求值测试。"""

    def test_constant_evaluate(self) -> None:
        """常数求值。/ Constant evaluation."""
        m = CanonicalMonomial.constant(7.0)
        assert m.evaluate({}) == 7.0

    def test_linear_evaluate(self) -> None:
        """线性求值。/ Linear evaluation."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x, coefficient=3.0)
        assert m.evaluate({x: 2.0}) == 6.0

    def test_power_evaluate(self) -> None:
        """幂次求值。/ Power evaluation."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x, power=2)
        assert m.evaluate({x: 3.0}) == 9.0

    def test_missing_binding_zero(self) -> None:
        """缺失绑定默认为 0。/ Missing binding defaults to 0."""
        x = Symbol.create("x")
        m = CanonicalMonomial.single(x)
        assert m.evaluate({}) == 0.0


class TestCanonicalMonomialMultiplication:
    """标准单项式乘法测试。"""

    def test_multiply_same_symbol(self) -> None:
        """同符号乘法。/ Same symbol multiplication."""
        x = Symbol.create("x")
        a = CanonicalMonomial.single(x, power=2)
        b = CanonicalMonomial.single(x, power=3)
        result = a * b
        assert result.powers[x] == 5

    def test_multiply_different_symbols(self) -> None:
        """不同符号乘法。/ Different symbol multiplication."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        a = CanonicalMonomial.single(x)
        b = CanonicalMonomial.single(y)
        result = a * b
        assert result.powers[x] == 1
        assert result.powers[y] == 1

    def test_multiply_constants(self) -> None:
        """常数乘法。/ Constant multiplication."""
        a = CanonicalMonomial.constant(3.0)
        b = CanonicalMonomial.constant(4.0)
        result = a * b
        assert result.coefficient == 12.0
        assert result.is_constant


# ── LinearMonomial ─────────────────────────────────────────────


class TestLinearMonomial:
    """线性单项式测试。"""

    def test_create_default_coefficient(self) -> None:
        """默认系数为 1。/ Default coefficient is 1."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x)
        assert m.coefficient == 1.0
        assert m.symbol == x

    def test_create_with_coefficient(self) -> None:
        """指定系数创建。/ Create with coefficient."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x, coefficient=2.5)
        assert m.coefficient == 2.5

    def test_degree_always_one(self) -> None:
        """次数始终为 1。/ Degree is always 1."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x)
        assert m.degree == 1

    def test_name_and_index(self) -> None:
        """名称和索引。/ Name and index."""
        x = Symbol.create("x", index=2)
        m = LinearMonomial.create(x)
        assert m.name == "x"
        assert m.index == 2

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
        assert neg.symbol == x

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

    def test_str_negative_coefficient(self) -> None:
        """负系数的字符串。/ String with negative coefficient."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x, coefficient=-1.0)
        assert str(m) == "-x"

    def test_str_general_coefficient(self) -> None:
        """一般系数的字符串。/ String with general coefficient."""
        x = Symbol.create("x")
        m = LinearMonomial.create(x, coefficient=2.5)
        s = str(m)
        assert "2.5" in s
        assert "x" in s


# ── QuadraticMonomial ──────────────────────────────────────────


class TestQuadraticMonomial:
    """二次单项式测试。"""

    def test_create(self) -> None:
        """创建二次单项式。/ Create quadratic monomial."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        assert m.coefficient == 1.0
        assert m.lhs == x
        assert m.rhs == y

    def test_create_with_coefficient(self) -> None:
        """带系数创建。/ Create with coefficient."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=2.5, lhs=x, rhs=y)
        assert m.coefficient == 2.5

    def test_degree_always_two(self) -> None:
        """次数始终为 2。/ Degree is always 2."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        assert m.degree == 2

    def test_is_square_true(self) -> None:
        """平方项。/ Square term."""
        x = Symbol.create("x")
        m = QuadraticMonomial.create(lhs=x, rhs=x)
        assert m.is_square

    def test_is_square_false(self) -> None:
        """非平方项。/ Not square term."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        assert not m.is_square

    def test_symbols_deduplicated(self) -> None:
        """符号去重。/ Symbols deduplicated."""
        x = Symbol.create("x")
        m = QuadraticMonomial.create(lhs=x, rhs=x)
        assert m.symbols == [x]

    def test_evaluate(self) -> None:
        """求值。/ Evaluate."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=2.0, lhs=x, rhs=y)
        assert m.evaluate(3.0, 4.0) == 24.0

    def test_negate(self) -> None:
        """取反。/ Negate."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=3.0, lhs=x, rhs=y)
        neg = m.negate()
        assert neg.coefficient == -3.0

    def test_scale(self) -> None:
        """缩放。/ Scale."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=2.0, lhs=x, rhs=y)
        scaled = m.scale(3.0)
        assert scaled.coefficient == 6.0

    def test_str_unit_coefficient(self) -> None:
        """系数为 1 时的字符串。/ String when coefficient is 1."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(lhs=x, rhs=y)
        s = str(m)
        assert "x" in s
        assert "y" in s

    def test_str_negative_coefficient(self) -> None:
        """负系数的字符串。/ String with negative coefficient."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        m = QuadraticMonomial.create(coefficient=-1.0, lhs=x, rhs=y)
        s = str(m)
        assert s.startswith("-")


# ── Quick operations ───────────────────────────────────────────


class TestQuickOps:
    """单项式快速运算测试。"""

    def test_mul_monomials(self) -> None:
        """单项式乘法。/ Monomial multiplication."""
        x = Symbol.create("x")
        y = Symbol.create("y")
        a = CanonicalMonomial.single(x, coefficient=2.0)
        b = CanonicalMonomial.single(y, coefficient=3.0)
        result = mul_monomials(a, b)
        assert result.coefficient == 6.0
        assert result.powers[x] == 1
        assert result.powers[y] == 1

    def test_divide_monomials(self) -> None:
        """单项式除法。/ Monomial division."""
        x = Symbol.create("x")
        a = CanonicalMonomial(coefficient=6.0, powers={x: 3})
        b = CanonicalMonomial(coefficient=2.0, powers={x: 1})
        result = divide_monomials(a, b)
        assert result.coefficient == 3.0
        assert result.powers[x] == 2

    def test_divide_same_power(self) -> None:
        """相同幂次除法消去。/ Same power division cancels."""
        x = Symbol.create("x")
        a = CanonicalMonomial(coefficient=4.0, powers={x: 2})
        b = CanonicalMonomial(coefficient=2.0, powers={x: 2})
        result = divide_monomials(a, b)
        assert result.coefficient == 2.0
        assert x not in result.powers
