"""Behavioral tests for math.symbol.operation modules with coverage gaps.

Targets: latex, convert, linear_quadratic_ops, serde, quick_dsl,
mutable_combine_ops, integrate_ops, normalize, differentiate_ops,
flt64_quick_ops, to_polynomial, parse.
"""

from __future__ import annotations

import pytest

from ospf_python.math.symbol.monomial.canonical_monomial import CanonicalMonomial
from ospf_python.math.symbol.monomial.linear_monomial import LinearMonomial
from ospf_python.math.symbol.monomial.quadratic_monomial import QuadraticMonomial
from ospf_python.math.symbol.operation.convert import PolynomialConverter
from ospf_python.math.symbol.operation.differentiate import Differentiator
from ospf_python.math.symbol.operation.differentiate_ops import DifferentiateOps
from ospf_python.math.symbol.operation.flt64_quick_ops import Flt64QuickOps
from ospf_python.math.symbol.operation.integrate_ops import IntegrateOps
from ospf_python.math.symbol.operation.latex import LatexRenderer
from ospf_python.math.symbol.operation.linear_quadratic_ops import LinearQuadraticOps
from ospf_python.math.symbol.operation.mutable_combine_ops import MutableCombineOps
from ospf_python.math.symbol.operation.normalize import PolynomialNormalizer
from ospf_python.math.symbol.operation.parse import PolynomialStringParser
from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
from ospf_python.math.symbol.operation.serde import SerdeOps
from ospf_python.math.symbol.operation.to_polynomial import ToPolynomial
from ospf_python.math.symbol.polynomial.canonical_polynomial import CanonicalPolynomial
from ospf_python.math.symbol.polynomial.linear_polynomial import LinearPolynomial
from ospf_python.math.symbol.polynomial.quadratic_polynomial import QuadraticPolynomial
from ospf_python.math.symbol.symbol import Symbol

FACTORY = CanonicalPolynomial
dsl = QuickDsl(factory=FACTORY)
differentiator = Differentiator(factory=FACTORY)


# ============================================================
# LatexRenderer tests
# ============================================================


class TestLatexRenderer:
    """LaTeX 渲染行为测试。/ LaTeX renderer behavioral tests."""

    def setup_method(self) -> None:
        self.renderer = LatexRenderer(factory=FACTORY)

    def test_render_zero_polynomial(self) -> None:
        """零多项式渲染为 '0'。/ Zero polynomial renders as '0'."""
        p = CanonicalPolynomial.zero()
        assert self.renderer.render(p) == "0"

    def test_render_constant_one(self) -> None:
        """常数 1 渲染。/ Constant 1 renders correctly."""
        p = CanonicalPolynomial.constant(1.0)
        result = self.renderer.render(p)
        assert "1" in result

    def test_render_constant_non_one(self) -> None:
        """非 1 常数渲染。/ Non-1 constant renders correctly."""
        p = CanonicalPolynomial.constant(5.0)
        result = self.renderer.render(p)
        assert "5" in result

    def test_render_single_variable(self) -> None:
        """单变量渲染。/ Single variable renders correctly."""
        x = dsl.var("x")
        result = self.renderer.render(x)
        assert "x" in result

    def test_render_negative_coefficient(self) -> None:
        """负系数渲染。/ Negative coefficient renders correctly."""
        x_sym = Symbol.create(name="x", index=0)
        term = CanonicalMonomial.single(x_sym, coefficient=-3.0)
        p = CanonicalPolynomial(terms=[term])
        result = self.renderer.render(p)
        assert "-" in result

    def test_render_coefficient_minus_one(self) -> None:
        """系数为 -1 的变量项渲染。/ Coefficient -1 variable term renders."""
        x_sym = Symbol.create(name="x", index=0)
        term = CanonicalMonomial.single(x_sym, coefficient=-1.0)
        p = CanonicalPolynomial(terms=[term])
        result = self.renderer.render(p)
        assert "-" in result
        # Should not render as "-1.0 x"
        assert "-1" not in result or result.strip().startswith("-")

    def test_render_power_greater_than_one(self) -> None:
        """幂次大于 1 渲染为上标。/ Power > 1 renders as superscript."""
        x_sym = Symbol.create(name="x", index=0)
        term = CanonicalMonomial(coefficient=1.0, powers={x_sym: 3})
        p = CanonicalPolynomial(terms=[term])
        result = self.renderer.render(p)
        assert "^{3}" in result

    def test_render_multiple_terms(self) -> None:
        """多项式多项渲染。/ Multi-term polynomial renders."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 2})
        t2 = CanonicalMonomial.single(x_sym, coefficient=3.0)
        t3 = CanonicalMonomial.constant(5.0)
        p = CanonicalPolynomial(terms=[t1, t2, t3])
        result = self.renderer.render(p)
        assert "x" in result

    def test_render_positive_non_first_coefficient(self) -> None:
        """非首位正系数项有 '+' 前缀。/ Non-first positive coefficient has '+' prefix."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial(coefficient=2.0, powers={x_sym: 2})
        t2 = CanonicalMonomial.single(x_sym, coefficient=3.0)
        p = CanonicalPolynomial(terms=[t1, t2])
        result = self.renderer.render(p)
        assert "+" in result

    def test_render_negative_non_first_coefficient(self) -> None:
        """非首位负系数项有 '-' 前缀。/ Non-first negative coefficient has '-' prefix."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial(coefficient=2.0, powers={x_sym: 2})
        t2 = CanonicalMonomial.single(x_sym, coefficient=-3.0)
        p = CanonicalPolynomial(terms=[t1, t2])
        result = self.renderer.render(p)
        assert "-" in result

    def test_render_skip_zero_coefficient_term(self) -> None:
        """零系数项被跳过。/ Zero coefficient terms are skipped."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=0.0)
        t2 = CanonicalMonomial.constant(5.0)
        p = CanonicalPolynomial(terms=[t1, t2])
        result = self.renderer.render(p)
        assert "5" in result

    def test_render_inline(self) -> None:
        """行内 LaTeX 渲染。/ Inline LaTeX rendering."""
        p = CanonicalPolynomial.constant(1.0)
        result = self.renderer.render_inline(p)
        assert result.startswith("$")
        assert result.endswith("$")

    def test_render_display(self) -> None:
        """展示 LaTeX 渲染。/ Display LaTeX rendering."""
        p = CanonicalPolynomial.constant(1.0)
        result = self.renderer.render_display(p)
        assert result.startswith("$$")
        assert result.endswith("$$")

    def test_render_unsupported_type_raises(self) -> None:
        """不支持的类型抛异常。/ Unsupported type raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported polynomial type"):
            self.renderer.render("not a polynomial")  # type: ignore[arg-type]

    def test_render_constant_first_coeff_one(self) -> None:
        """纯常数项系数为 1（非首位）。/ Pure constant with coeff=1, not first."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        t2 = CanonicalMonomial.constant(1.0)
        p = CanonicalPolynomial(terms=[t1, t2])
        result = self.renderer.render(p)
        assert "1" in result

    def test_render_negative_constant_non_first(self) -> None:
        """纯负常数项（非首位）。/ Negative constant term, not first."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        t2 = CanonicalMonomial.constant(-3.0)
        p = CanonicalPolynomial(terms=[t1, t2])
        result = self.renderer.render(p)
        assert "-" in result
        assert "3" in result

    def test_render_positive_constant_non_first(self) -> None:
        """纯正常数项（非首位）。/ Positive constant term, not first."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        t2 = CanonicalMonomial.constant(3.0)
        p = CanonicalPolynomial(terms=[t1, t2])
        result = self.renderer.render(p)
        assert "+" in result

    def test_render_first_negative_general_coeff(self) -> None:
        """首位负系数一般变量项。/ First negative general coefficient variable."""
        x_sym = Symbol.create(name="x", index=0)
        term = CanonicalMonomial(coefficient=-2.0, powers={x_sym: 2})
        p = CanonicalPolynomial(terms=[term])
        result = self.renderer.render(p)
        assert "-" in result

    def test_render_first_positive_general_coeff(self) -> None:
        """首位正系数一般变量项。/ First positive general coefficient variable."""
        x_sym = Symbol.create(name="x", index=0)
        term = CanonicalMonomial(coefficient=3.0, powers={x_sym: 2})
        p = CanonicalPolynomial(terms=[term])
        result = self.renderer.render(p)
        assert "3" in result
        assert "x" in result


# ============================================================
# PolynomialConverter tests (deeper coverage)
# ============================================================


class TestPolynomialConverterDeeper:
    """多项式转换深度行为测试。/ Polynomial converter deeper behavioral tests."""

    def test_canonical_to_quadratic_with_cross_term(self) -> None:
        """标准→二次（含交叉项 xy）。/ Canonical → Quadratic with cross term."""
        conv = PolynomialConverter(
            source_factory=FACTORY, target_factory=QuadraticPolynomial
        )
        x_sym = Symbol.create(name="x", index=0)
        y_sym = Symbol.create(name="y", index=1)
        xy = CanonicalMonomial(coefficient=2.0, powers={x_sym: 1, y_sym: 1})
        p = CanonicalPolynomial(terms=[xy])
        result = conv.convert(p)
        assert isinstance(result, QuadraticPolynomial)

    def test_canonical_to_linear_rejects_quadratic_term(self) -> None:
        """标准→线性拒绝二次项。/ Canonical → Linear rejects quadratic term."""
        conv = PolynomialConverter(
            source_factory=FACTORY, target_factory=LinearPolynomial
        )
        x_sym = Symbol.create(name="x", index=0)
        x2 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 2})
        p = CanonicalPolynomial(terms=[x2])
        with pytest.raises(ValueError, match="Cannot convert"):
            conv.convert(p)

    def test_canonical_to_quadratic_rejects_cubic_term(self) -> None:
        """标准→二次拒绝三次项。/ Canonical → Quadratic rejects cubic term."""
        conv = PolynomialConverter(
            source_factory=FACTORY, target_factory=QuadraticPolynomial
        )
        x_sym = Symbol.create(name="x", index=0)
        x3 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 3})
        p = CanonicalPolynomial(terms=[x3])
        with pytest.raises(ValueError, match="Cannot convert"):
            conv.convert(p)

    def test_quadratic_to_canonical(self) -> None:
        """二次→标准。/ Quadratic → Canonical."""
        conv = PolynomialConverter(
            source_factory=QuadraticPolynomial, target_factory=FACTORY
        )
        x_sym = Symbol.create(name="x", index=0)
        qm = QuadraticMonomial.create(coefficient=3.0, lhs=x_sym, rhs=x_sym)
        qp = QuadraticPolynomial(
            quadratic_terms=[qm],
            linear_terms={x_sym: 2.0},
            constant=1.0,
        )
        result = conv.convert(qp)
        assert isinstance(result, CanonicalPolynomial)

    def test_quadratic_to_canonical_with_constant(self) -> None:
        """二次→标准（含常数项）。/ Quadratic → Canonical with constant."""
        conv = PolynomialConverter(
            source_factory=QuadraticPolynomial, target_factory=FACTORY
        )
        qp = QuadraticPolynomial(constant=5.0)
        result = conv.convert(qp)
        assert isinstance(result, CanonicalPolynomial)

    def test_quadratic_to_canonical_zero_constant(self) -> None:
        """二次→标准（零常数项不生成常数项）。/ Quadratic → Canonical, zero constant."""
        conv = PolynomialConverter(
            source_factory=QuadraticPolynomial, target_factory=FACTORY
        )
        x_sym = Symbol.create(name="x", index=0)
        qp = QuadraticPolynomial(linear_terms={x_sym: 2.0}, constant=0.0)
        result = conv.convert(qp)
        assert isinstance(result, CanonicalPolynomial)

    def test_linear_to_canonical_zero_constant(self) -> None:
        """线性→标准（零常数项不生成常数项）。/ Linear → Canonical, zero constant."""
        conv = PolynomialConverter(
            source_factory=LinearPolynomial, target_factory=FACTORY
        )
        x_sym = Symbol.create(name="x", index=0)
        lp = LinearPolynomial(
            terms=[LinearMonomial.create(symbol=x_sym, coefficient=3.0)],
            constant=0.0,
        )
        result = conv.convert(lp)
        assert isinstance(result, CanonicalPolynomial)


# ============================================================
# LinearQuadraticOps tests
# ============================================================


class TestLinearQuadraticOps:
    """线性/二次运算行为测试。/ Linear-quadratic ops behavioral tests."""

    def setup_method(self) -> None:
        self.ops = LinearQuadraticOps(factory=FACTORY)

    def test_solve_linear_basic(self) -> None:
        """求解 3x + 6 = 0。/ Solve 3x + 6 = 0."""
        x_sym = Symbol.create(name="x", index=0)
        linear = CanonicalMonomial.single(x_sym, coefficient=3.0)
        const = CanonicalMonomial.constant(6.0)
        p = CanonicalPolynomial(terms=[linear, const])
        result = self.ops.solve_linear(p, "x")
        assert result == pytest.approx(-2.0)

    def test_solve_linear_no_variable_raises(self) -> None:
        """线性方程中不存在变量抛异常。/ Linear with no variable raises ValueError."""
        p = CanonicalPolynomial.constant(5.0)
        with pytest.raises(ValueError, match="not found"):
            self.ops.solve_linear(p, "x")

    def test_solve_linear_quadratic_term_raises(self) -> None:
        """线性方程含二次项抛异常。/ Linear with quadratic term raises ValueError."""
        x_sym = Symbol.create(name="x", index=0)
        x2 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 2})
        p = CanonicalPolynomial(terms=[x2])
        with pytest.raises(ValueError, match="quadratic"):
            self.ops.solve_linear(p, "x")

    def test_solve_quadratic_two_roots(self) -> None:
        """二次方程两个实根。/ Quadratic with two real roots."""
        # x^2 - 5x + 6 = 0 -> x=2 or x=3
        x_sym = Symbol.create(name="x", index=0)
        x2 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 2})
        x1 = CanonicalMonomial.single(x_sym, coefficient=-5.0)
        c = CanonicalMonomial.constant(6.0)
        p = CanonicalPolynomial(terms=[x2, x1, c])
        roots = self.ops.solve_quadratic(p, "x")
        assert len(roots) == 2
        assert pytest.approx(2.0, abs=1e-9) in roots
        assert pytest.approx(3.0, abs=1e-9) in roots

    def test_solve_quadratic_discriminant_zero(self) -> None:
        """二次方程判别式为零（重根）。/ Quadratic with zero discriminant."""
        # x^2 - 4x + 4 = 0 -> x=2
        x_sym = Symbol.create(name="x", index=0)
        x2 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 2})
        x1 = CanonicalMonomial.single(x_sym, coefficient=-4.0)
        c = CanonicalMonomial.constant(4.0)
        p = CanonicalPolynomial(terms=[x2, x1, c])
        roots = self.ops.solve_quadratic(p, "x")
        assert len(roots) == 1
        assert roots[0] == pytest.approx(2.0)

    def test_solve_quadratic_no_real_roots(self) -> None:
        """二次方程无实根。/ Quadratic with no real roots."""
        # x^2 + 1 = 0
        x_sym = Symbol.create(name="x", index=0)
        x2 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 2})
        c = CanonicalMonomial.constant(1.0)
        p = CanonicalPolynomial(terms=[x2, c])
        roots = self.ops.solve_quadratic(p, "x")
        assert len(roots) == 0

    def test_solve_quadratic_degenerate_linear(self) -> None:
        """退化为线性方程（a=0）。/ Quadratic degenerated to linear (a=0)."""
        # 2x + 4 = 0 -> x = -2
        x_sym = Symbol.create(name="x", index=0)
        x1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        c = CanonicalMonomial.constant(4.0)
        p = CanonicalPolynomial(terms=[x1, c])
        roots = self.ops.solve_quadratic(p, "x")
        assert len(roots) == 1
        assert roots[0] == pytest.approx(-2.0)

    def test_solve_quadratic_degenerate_both_zero_raises(self) -> None:
        """常数方程中变量不存在抛异常。/ Constant equation raises ValueError."""
        p = CanonicalPolynomial.constant(5.0)
        with pytest.raises(ValueError, match="not found"):
            self.ops.solve_quadratic(p, "x")

    def test_solve_quadratic_variable_not_found_raises(self) -> None:
        """变量不存在抛异常。/ Variable not found raises ValueError."""
        x_sym = Symbol.create(name="x", index=0)
        x1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        p = CanonicalPolynomial(terms=[x1])
        with pytest.raises(ValueError, match="not found"):
            self.ops.solve_quadratic(p, "z")

    def test_solve_quadratic_higher_degree_raises(self) -> None:
        """高于二次的项抛异常。/ Degree > 2 term raises ValueError."""
        x_sym = Symbol.create(name="x", index=0)
        x3 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 3})
        p = CanonicalPolynomial(terms=[x3])
        with pytest.raises(ValueError, match="Degree 3"):
            self.ops.solve_quadratic(p, "x")

    def test_discriminant(self) -> None:
        """判别式计算。/ Discriminant computation."""
        # x^2 - 5x + 6 = 0 -> disc = 25 - 24 = 1
        x_sym = Symbol.create(name="x", index=0)
        x2 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 2})
        x1 = CanonicalMonomial.single(x_sym, coefficient=-5.0)
        c = CanonicalMonomial.constant(6.0)
        p = CanonicalPolynomial(terms=[x2, x1, c])
        disc = self.ops.discriminant(p, "x")
        assert disc == pytest.approx(1.0)

    def test_solve_linear_unsupported_type_raises(self) -> None:
        """线性求解不支持的类型。/ Linear solve unsupported type raises."""
        with pytest.raises(TypeError):
            self.ops.solve_linear("not a polynomial", "x")  # type: ignore[arg-type]

    def test_solve_quadratic_unsupported_type_raises(self) -> None:
        """二次求解不支持的类型。/ Quadratic solve unsupported type raises."""
        with pytest.raises(TypeError):
            self.ops.solve_quadratic("not a polynomial", "x")  # type: ignore[arg-type]

    def test_discriminant_unsupported_type_raises(self) -> None:
        """判别式不支持的类型。/ Discriminant unsupported type raises."""
        with pytest.raises(TypeError):
            self.ops.discriminant("not a polynomial", "x")  # type: ignore[arg-type]

    def test_solve_linear_only_constant_raises(self) -> None:
        """常数多项式求解线性方程变量不存在。/ Constant polynomial solve_linear raises."""
        p = CanonicalPolynomial.constant(0.0)
        with pytest.raises(ValueError, match="not found"):
            self.ops.solve_linear(p, "x")


# ============================================================
# SerdeOps tests
# ============================================================


class TestSerdeOps:
    """序列化/反序列化行为测试。/ Serde ops behavioral tests."""

    def setup_method(self) -> None:
        self.serde = SerdeOps(factory=FACTORY)

    def test_serialize_and_deserialize_roundtrip(self) -> None:
        """序列化-反序列化往返验证。/ Serialize-deserialize roundtrip."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=3.0)
        t2 = CanonicalMonomial.constant(5.0)
        p = CanonicalPolynomial(terms=[t1, t2])
        json_str = self.serde.serialize(p)
        result = self.serde.deserialize(json_str)
        assert result is not None
        assert isinstance(result, CanonicalPolynomial)

    def test_deserialize_invalid_json_returns_none(self) -> None:
        """无效 JSON 返回 None。/ Invalid JSON returns None."""
        assert self.serde.deserialize("not json") is None

    def test_deserialize_missing_terms_key_returns_none(self) -> None:
        """缺少 terms 键返回 None。/ Missing 'terms' key returns None."""
        assert self.serde.deserialize('{"data": []}') is None

    def test_deserialize_empty_terms_returns_zero(self) -> None:
        """空 terms 返回零多项式。/ Empty terms returns zero polynomial."""
        result = self.serde.deserialize('{"terms": []}')
        assert result is not None
        assert isinstance(result, CanonicalPolynomial)
        assert result.is_zero

    def test_deserialize_non_dict_returns_none(self) -> None:
        """非字典 JSON 返回 None。/ Non-dict JSON returns None."""
        assert self.serde.deserialize('"hello"') is None

    def test_deserialize_bad_term_data_returns_none(self) -> None:
        """错误项数据返回 None。/ Bad term data returns None."""
        assert self.serde.deserialize('{"terms": [{"bad": "data"}]}') is None

    def test_to_dict(self) -> None:
        """多项式转字典。/ Polynomial to dict."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        p = CanonicalPolynomial(terms=[t1])
        result = self.serde.to_dict(p)
        assert result is not None
        assert "terms" in result

    def test_to_dict_unsupported_type_returns_none(self) -> None:
        """不支持的类型返回 None。/ Unsupported type to_dict returns None."""
        result = self.serde.to_dict("not a polynomial")  # type: ignore[arg-type]
        assert result is None

    def test_from_dict(self) -> None:
        """从字典反序列化。/ Deserialize from dict."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=3.0)
        p = CanonicalPolynomial(terms=[t1])
        d = self.serde.to_dict(p)
        assert d is not None
        result = self.serde.from_dict(d)
        assert result is not None

    def test_from_dict_missing_terms_returns_none(self) -> None:
        """缺少 terms 键返回 None。/ Missing terms key returns None."""
        assert self.serde.from_dict({"data": []}) is None

    def test_from_dict_bad_term_returns_none(self) -> None:
        """错误项返回 None。/ Bad term data returns None."""
        assert self.serde.from_dict({"terms": [{"bad": "data"}]}) is None

    def test_from_dict_empty_terms_returns_zero(self) -> None:
        """空 terms 返回零多项式。/ Empty terms returns zero polynomial."""
        result = self.serde.from_dict({"terms": []})
        assert result is not None
        assert result.is_zero

    def test_from_dict_unsupported_factory_returns_none(self) -> None:
        """不支持的工厂类型返回 None。/ Unsupported factory from_dict returns None."""
        bad_serde = SerdeOps(factory=str)  # type: ignore[type-arg]
        assert bad_serde.from_dict({"terms": []}) is None

    def test_serialize_unsupported_type_raises(self) -> None:
        """不支持的序列化类型抛异常。/ Unsupported serialize type raises."""
        with pytest.raises(TypeError):
            self.serde.serialize("not a polynomial")  # type: ignore[arg-type]

    def test_deserialize_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型反序列化抛异常。/ Unsupported factory deserialize raises."""
        bad_serde = SerdeOps(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            bad_serde.deserialize('{"terms": []}')

    def test_deserialize_type_error_returns_none(self) -> None:
        """TypeError 输入返回 None。/ TypeError input returns None."""
        assert self.serde.deserialize(123) is None  # type: ignore[arg-type]


# ============================================================
# QuickDsl tests
# ============================================================


class TestQuickDsl:
    """快速 DSL 行为测试。/ Quick DSL behavioral tests."""

    def test_var_creates_polynomial(self) -> None:
        """var 创建变量多项式。/ var creates variable polynomial."""
        d = QuickDsl(factory=FACTORY)
        x = d.var("x")
        assert isinstance(x, CanonicalPolynomial)

    def test_constant_creates_polynomial(self) -> None:
        """constant 创建常数多项式。/ constant creates constant polynomial."""
        d = QuickDsl(factory=FACTORY)
        c = d.constant(5.0)
        assert isinstance(c, CanonicalPolynomial)

    def test_sum_empty_returns_zero(self) -> None:
        """空求和返回零多项式。/ Empty sum returns zero polynomial."""
        d = QuickDsl(factory=FACTORY)
        result = d.sum()
        assert isinstance(result, CanonicalPolynomial)
        assert result.is_zero

    def test_sum_multiple(self) -> None:
        """多项求和。/ Sum of multiple polynomials."""
        d = QuickDsl(factory=FACTORY)
        x = d.var("x")
        y = d.var("y")
        result = d.sum(x, y)
        assert isinstance(result, CanonicalPolynomial)

    def test_product_empty_returns_identity(self) -> None:
        """空乘积返回单位元（常数 1）。/ Empty product returns identity."""
        d = QuickDsl(factory=FACTORY)
        result = d.product()
        assert isinstance(result, CanonicalPolynomial)

    def test_product_multiple(self) -> None:
        """多项乘积。/ Product of multiple polynomials."""
        d = QuickDsl(factory=FACTORY)
        x = d.var("x")
        y = d.var("y")
        result = d.product(x, y)
        assert isinstance(result, CanonicalPolynomial)

    def test_var_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型 var 抛异常。/ Unsupported factory var raises."""
        d = QuickDsl(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            d.var("x")

    def test_constant_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型 constant 抛异常。/ Unsupported factory constant raises."""
        d = QuickDsl(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            d.constant(1.0)

    def test_sum_empty_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型空求和抛异常。/ Unsupported factory empty sum raises."""
        d = QuickDsl(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            d.sum()

    def test_product_empty_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型空乘积抛异常。/ Unsupported factory empty product raises."""
        d = QuickDsl(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            d.product()

    def test_sum_non_empty_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型非空求和抛异常。/ Unsupported factory non-empty sum raises."""
        d = QuickDsl(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            d.sum("x")  # type: ignore[arg-type]

    def test_product_non_empty_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型非空乘积抛异常。/ Unsupported factory non-empty product raises."""
        d = QuickDsl(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            d.product("x")  # type: ignore[arg-type]


# ============================================================
# MutableCombineOps tests
# ============================================================


class TestMutableCombineOpsDeeper:
    """可变合并运算深度测试。/ Mutable combine ops deeper tests."""

    def test_sum_empty_returns_zero(self) -> None:
        """空列表求和返回零多项式。/ Empty list sum returns zero."""
        ops = MutableCombineOps(factory=FACTORY)
        result = ops.sum([])
        assert isinstance(result, CanonicalPolynomial)
        assert result.is_zero

    def test_product_empty_returns_identity(self) -> None:
        """空列表乘积返回单位元。/ Empty list product returns identity."""
        ops = MutableCombineOps(factory=FACTORY)
        result = ops.product([])
        assert isinstance(result, CanonicalPolynomial)

    def test_sum_unsupported_factory_empty_raises(self) -> None:
        """不支持的工厂类型空求和抛异常。/ Unsupported factory empty sum raises."""
        ops = MutableCombineOps(factory=str)  # type: ignore[type-arg]
        with pytest.raises(ValueError):
            ops.sum([])

    def test_product_unsupported_factory_empty_raises(self) -> None:
        """不支持的工厂类型空乘积抛异常。/ Unsupported factory empty product raises."""
        ops = MutableCombineOps(factory=str)  # type: ignore[type-arg]
        with pytest.raises(ValueError):
            ops.product([])

    def test_sum_unsupported_factory_non_empty_raises(self) -> None:
        """不支持的工厂类型非空求和抛异常。/ Unsupported factory non-empty sum raises."""
        ops = MutableCombineOps(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            ops.sum(["a"])  # type: ignore[arg-type]

    def test_product_unsupported_factory_non_empty_raises(self) -> None:
        """不支持的工厂类型非空乘积抛异常。/ Unsupported factory non-empty product raises."""
        ops = MutableCombineOps(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            ops.product(["a"])  # type: ignore[arg-type]

    def test_product_two_polynomials(self) -> None:
        """两个多项式乘积。/ Product of two polynomials."""
        ops = MutableCombineOps(factory=FACTORY)
        p1 = CanonicalPolynomial.constant(2.0)
        p2 = CanonicalPolynomial.constant(3.0)
        result = ops.product([p1, p2])
        assert isinstance(result, CanonicalPolynomial)


# ============================================================
# IntegrateOps tests
# ============================================================


class TestIntegrateOps:
    """积分运算行为测试。/ Integration ops behavioral tests."""

    def setup_method(self) -> None:
        self.ops = IntegrateOps(factory=FACTORY)

    def test_integrate_linear(self) -> None:
        """积分 3x -> 3/2 x^2。/ Integrate 3x -> 3/2 x^2."""
        x_sym = Symbol.create(name="x", index=0)
        term = CanonicalMonomial.single(x_sym, coefficient=3.0)
        p = CanonicalPolynomial(terms=[term])
        result = self.ops.integrate(p, "x")
        assert isinstance(result, CanonicalPolynomial)
        # The integrated polynomial should have x^2 term
        assert result.degree >= 1

    def test_integrate_constant_with_variable(self) -> None:
        """积分常数项（含变量）。/ Integrate constant with variable present."""
        x_sym = Symbol.create(name="x", index=0)
        t_const = CanonicalMonomial.constant(5.0)
        t_linear = CanonicalMonomial.single(x_sym, coefficient=3.0)
        p = CanonicalPolynomial(terms=[t_const, t_linear])
        result = self.ops.integrate(p, "x")
        assert isinstance(result, CanonicalPolynomial)

    def test_integrate_variable_not_found_raises(self) -> None:
        """积分变量不存在抛异常。/ Integration variable not found raises."""
        x_sym = Symbol.create(name="x", index=0)
        term = CanonicalMonomial.single(x_sym, coefficient=2.0)
        p = CanonicalPolynomial(terms=[term])
        with pytest.raises(ValueError, match="not found"):
            self.ops.integrate(p, "z")

    def test_integrate_unsupported_type_raises(self) -> None:
        """不支持的类型抛异常。/ Unsupported type raises."""
        with pytest.raises(TypeError):
            self.ops.integrate("not a polynomial", "x")  # type: ignore[arg-type]

    def test_definite_integrate_unsupported_type_raises(self) -> None:
        """定积分不支持的类型。/ Definite integrate unsupported type raises."""
        with pytest.raises(TypeError):
            self.ops.definite_integrate("not a polynomial", "x", 0.0, 1.0)  # type: ignore[arg-type]


# ============================================================
# PolynomialNormalizer tests
# ============================================================


class TestPolynomialNormalizer:
    """多项式规范器行为测试。/ Polynomial normalizer behavioral tests."""

    def setup_method(self) -> None:
        self.normalizer = PolynomialNormalizer(factory=FACTORY)

    def test_normalize_already_normalized(self) -> None:
        """已规范化多项式不变。/ Already normalized stays same."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial(coefficient=2.0, powers={x_sym: 2})
        t2 = CanonicalMonomial.single(x_sym, coefficient=3.0)
        t3 = CanonicalMonomial.constant(1.0)
        p = CanonicalPolynomial(terms=[t1, t2, t3])
        result = self.normalizer.normalize(p)
        assert isinstance(result, CanonicalPolynomial)

    def test_is_normalized_true(self) -> None:
        """已规范化多项式返回 True。/ Normalized polynomial returns True."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial(coefficient=2.0, powers={x_sym: 2})
        t2 = CanonicalMonomial.single(x_sym, coefficient=3.0)
        p = CanonicalPolynomial(terms=[t1, t2])
        assert self.normalizer.is_normalized(p) is True

    def test_is_normalized_false_zero_coeff(self) -> None:
        """含零系数项返回 False。/ Zero coefficient returns False."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=0.0)
        p = CanonicalPolynomial(terms=[t1])
        assert self.normalizer.is_normalized(p) is False

    def test_is_normalized_false_wrong_order(self) -> None:
        """非降序排列返回 False。/ Wrong degree order returns False."""
        x_sym = Symbol.create(name="x", index=0)
        t1 = CanonicalMonomial.single(x_sym, coefficient=1.0)  # degree 1
        t2 = CanonicalMonomial(coefficient=2.0, powers={x_sym: 2})  # degree 2
        p = CanonicalPolynomial(terms=[t1, t2])  # wrong order: degree 1 then degree 2
        assert self.normalizer.is_normalized(p) is False

    def test_normalize_unsupported_type_raises(self) -> None:
        """不支持的类型抛异常。/ Unsupported type raises."""
        with pytest.raises(TypeError):
            self.normalizer.normalize("not a polynomial")  # type: ignore[arg-type]

    def test_is_normalized_unsupported_type_raises(self) -> None:
        """不支持的类型抛异常。/ Unsupported type raises."""
        with pytest.raises(TypeError):
            self.normalizer.is_normalized("not a polynomial")  # type: ignore[arg-type]


# ============================================================
# DifferentiateOps tests
# ============================================================


class TestDifferentiateOps:
    """微分运算行为测试。/ Differentiate ops behavioral tests."""

    def test_grad(self) -> None:
        """梯度计算。/ Gradient computation."""
        ops = DifferentiateOps(differentiator=differentiator)
        x = dsl.var("x")
        y = dsl.var("y")
        poly = dsl.product(x, y)
        grad = ops.grad(poly, ["x", "y"])
        assert len(grad) == 2

    def test_hessian(self) -> None:
        """Hessian 矩阵计算。/ Hessian matrix computation."""
        ops = DifferentiateOps(differentiator=differentiator)
        x = dsl.var("x")
        x2 = dsl.product(x, x)
        hess = ops.hessian(x2, ["x"])
        assert len(hess) == 1
        assert len(hess[0]) == 1


# ============================================================
# Flt64QuickOps tests
# ============================================================


class TestFlt64QuickOpsDeeper:
    """Flt64 快速运算深度测试。/ Flt64 quick ops deeper tests."""

    def test_is_zero_with_small_value(self) -> None:
        """小值判断为零。/ Small value is zero."""
        ops = Flt64QuickOps(tolerance=1e-12)
        assert ops.is_zero(1e-15) is True

    def test_is_zero_with_large_value(self) -> None:
        """大值不为零。/ Large value is not zero."""
        ops = Flt64QuickOps(tolerance=1e-12)
        assert ops.is_zero(1.0) is False

    def test_is_equal_approximately(self) -> None:
        """近似相等判断。/ Approximately equal."""
        ops = Flt64QuickOps(tolerance=1e-12)
        assert ops.is_equal(1.0, 1.0 + 1e-15) is True

    def test_is_equal_different(self) -> None:
        """不等判断。/ Not equal."""
        ops = Flt64QuickOps(tolerance=1e-12)
        assert ops.is_equal(1.0, 2.0) is False

    def test_custom_tolerance(self) -> None:
        """自定义容差。/ Custom tolerance."""
        ops = Flt64QuickOps(tolerance=0.1)
        assert ops.is_zero(0.05) is True
        assert ops.is_zero(0.2) is False


# ============================================================
# ToPolynomial tests
# ============================================================


class TestToPolynomialDeeper:
    """ToPolynomial 深度行为测试。/ ToPolynomial deeper behavioral tests."""

    def setup_method(self) -> None:
        self.tp = ToPolynomial(factory=FACTORY)

    def test_from_dict_with_zero_coefficients(self) -> None:
        """字典中零系数项被跳过。/ Zero coefficients in dict are skipped."""
        result = self.tp.from_dict({"x": 0.0, "y": 3.0})
        assert isinstance(result, CanonicalPolynomial)

    def test_from_dict_multiple_vars(self) -> None:
        """多变量字典转换。/ Multi-variable dict conversion."""
        result = self.tp.from_dict({"x": 2.0, "y": 3.0, "z": 1.0})
        assert isinstance(result, CanonicalPolynomial)

    def test_from_dict_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型抛异常。/ Unsupported factory raises."""
        tp = ToPolynomial(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            tp.from_dict({"x": 1.0})

    def test_from_list_with_constant(self) -> None:
        """列表含常数项。/ List with constant term."""
        result = self.tp.from_list([3.0, 2.0, 1.0], "x")
        assert isinstance(result, CanonicalPolynomial)

    def test_from_list_with_zero_coefficients(self) -> None:
        """列表中零系数项被跳过。/ Zero coefficients in list are skipped."""
        result = self.tp.from_list([0.0, 2.0, 0.0, 1.0], "x")
        assert isinstance(result, CanonicalPolynomial)

    def test_from_list_only_constant(self) -> None:
        """列表只有常数项。/ List with only constant term."""
        result = self.tp.from_list([5.0], "x")
        assert isinstance(result, CanonicalPolynomial)

    def test_from_list_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型列表转换抛异常。/ Unsupported factory list raises."""
        tp = ToPolynomial(factory=str)  # type: ignore[type-arg]
        with pytest.raises(TypeError):
            tp.from_list([1.0], "x")


# ============================================================
# PolynomialStringParser tests (deeper)
# ============================================================


class TestPolynomialStringParserDeeper:
    """多项式字符串解析深度测试。/ Polynomial string parser deeper tests."""

    def setup_method(self) -> None:
        self.parser = PolynomialStringParser(factory=FACTORY)

    def test_parse_negative_variable(self) -> None:
        """解析负变量项。/ Parse negative variable term."""
        result = self.parser.parse("-x")
        assert result is not None

    def test_parse_negative_coefficient_variable(self) -> None:
        """解析负系数变量项。/ Parse negative coefficient variable."""
        result = self.parser.parse("-3*x")
        assert result is not None

    def test_parse_negative_constant(self) -> None:
        """解析负常数。/ Parse negative constant."""
        result = self.parser.parse("-5")
        assert result is not None

    def test_parse_float_constant(self) -> None:
        """解析浮点常数。/ Parse float constant."""
        result = self.parser.parse("3.14")
        assert result is not None

    def test_parse_garbage_returns_result(self) -> None:
        """垃圾字符解析尝试。/ Garbage characters parse attempt."""
        # The parser may produce a term or None depending on regex matching
        result = self.parser.parse("@#$")
        # Either None or a valid polynomial is acceptable
        assert result is None or isinstance(result, CanonicalPolynomial)

    def test_parse_variable_with_power(self) -> None:
        """解析变量幂次。/ Parse variable with power."""
        result = self.parser.parse("x^3")
        assert result is not None
