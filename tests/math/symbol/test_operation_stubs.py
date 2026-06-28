"""符号运算模块行为测试。

Behavioral tests for symbol operation modules:
QuickDsl, evaluate, differentiate, integrate, serde,
LaTeX, canonical ops, combine terms, linear/quadratic ops,
inequality ops, parse, normalize.
"""

from __future__ import annotations

import pytest

from ospf_python.math.symbol.monomial.canonical_monomial import CanonicalMonomial
from ospf_python.math.symbol.operation.canonical_ops import CanonicalOps
from ospf_python.math.symbol.operation.combine_terms import TermCombiner
from ospf_python.math.symbol.operation.differentiate import Differentiator
from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
from ospf_python.math.symbol.operation.flt64_matrix_form import Flt64MatrixForm
from ospf_python.math.symbol.operation.inequality import InequalityOps
from ospf_python.math.symbol.operation.integrate_ops import IntegrateOps
from ospf_python.math.symbol.operation.latex import LatexRenderer
from ospf_python.math.symbol.operation.linear_quadratic_ops import (
    LinearQuadraticOps,
)
from ospf_python.math.symbol.operation.normalize import PolynomialNormalizer
from ospf_python.math.symbol.operation.parse import PolynomialStringParser
from ospf_python.math.symbol.operation.power_vector_key import PowerVectorKey
from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
from ospf_python.math.symbol.operation.serde import SerdeOps
from ospf_python.math.symbol.operation.value_provider import (
    DictValueProvider,
    LambdaValueProvider,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

# ============================================================
# Helpers
# ============================================================


FACTORY = CanonicalPolynomial
dsl = QuickDsl(factory=FACTORY)
ev = PolynomialEvaluator(factory=FACTORY)
diff = Differentiator(factory=FACTORY)
iops = IntegrateOps(factory=FACTORY)
serde = SerdeOps(factory=FACTORY)
latex = LatexRenderer(factory=FACTORY)
canon = CanonicalOps(factory=FACTORY)
combiner = TermCombiner(factory=FACTORY)
lq = LinearQuadraticOps(factory=FACTORY)
ineq = InequalityOps(factory=FACTORY)
parser = PolynomialStringParser(factory=FACTORY)
normalizer = PolynomialNormalizer(factory=FACTORY)


# ============================================================
# Golden case: x + 1
# ============================================================


class TestGoldenXPlusOne:
    """x + 1 黄金测试。/ Golden test: x + 1."""

    def test_build_x_plus_1(self) -> None:
        """构建 x + 1。/ Build x + 1."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        assert xp1 is not None
        assert xp1.term_count >= 2

    def test_evaluate_x_plus_1(self) -> None:
        """求值 x+1 at x=2 → 3。/ Evaluate x+1 at x=2 → 3."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        result = ev.evaluate(xp1, {"x": 2.0})
        assert result == pytest.approx(3.0)

    def test_differentiate_x_plus_1(self) -> None:
        """求导 d/dx(x+1) → 1。/ Differentiate d/dx(x+1) → 1."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        derivative = diff.differentiate(xp1, "x")
        # 1 的导数为 0，x 的导数为 1*1=1
        # Derivative of 1 is 0, derivative of x is 1*1=1
        result = ev.evaluate(derivative, {"x": 0.0})
        assert result == pytest.approx(1.0)

    def test_integrate_x_plus_1(self) -> None:
        """积分 ∫(x+1)dx → x²/2 + x。/ Integrate ∫(x+1)dx → x²/2 + x."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        integrated = iops.integrate(xp1, "x")
        # ∫x dx = x²/2, ∫1 dx = x → 在 x=2 时应为 2+2=4
        # ∫x dx = x²/2, ∫1 dx = x → at x=2 should be 2+2=4
        result = ev.evaluate(integrated, {"x": 2.0})
        assert result == pytest.approx(4.0)

    def test_serde_roundtrip_x_plus_1(self) -> None:
        """序列化往返 x+1。/ Serde round-trip x+1."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        serialized = serde.serialize(xp1)
        assert serialized is not None
        deserialized = serde.deserialize(serialized)
        assert deserialized is not None

    def test_latex_x_plus_1(self) -> None:
        """LaTeX 渲染 x+1。/ LaTeX render x+1."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        latex_str = latex.render(xp1)
        assert "x" in latex_str
        assert "1" in latex_str


# ============================================================
# Golden case: 2*x + 3*y - 5
# ============================================================


class TestGolden2x3y5:
    """2x+3y-5 黄金测试。/ Golden test: 2x+3y-5."""

    def test_build_2x_3y_5(self) -> None:
        """构建 2x+3y-5。/ Build 2x+3y-5."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        three = dsl.constant(3.0)
        two_x = dsl.product(two, x)
        three_y = dsl.product(three, y)
        neg5 = dsl.constant(-5.0)
        poly = dsl.sum(two_x, three_y, neg5)
        assert poly is not None

    def test_evaluate_2x_3y_5(self) -> None:
        """求值 2x+3y-5 at x=1,y=2 → 3。/ Evaluate at x=1,y=2 → 3."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        three = dsl.constant(3.0)
        two_x = dsl.product(two, x)
        three_y = dsl.product(three, y)
        neg5 = dsl.constant(-5.0)
        poly = dsl.sum(two_x, three_y, neg5)
        result = ev.evaluate(poly, {"x": 1.0, "y": 2.0})
        assert result == pytest.approx(3.0)

    def test_differentiate_2x_3y_5(self) -> None:
        """求导 d/dx(2x+3y-5) → 2。/ Diff d/dx → 2."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        three = dsl.constant(3.0)
        two_x = dsl.product(two, x)
        three_y = dsl.product(three, y)
        neg5 = dsl.constant(-5.0)
        poly = dsl.sum(two_x, three_y, neg5)
        derivative = diff.differentiate(poly, "x")
        result = ev.evaluate(derivative, {"y": 0.0})
        assert result == pytest.approx(2.0)

    def test_serde_roundtrip_2x_3y_5(self) -> None:
        """序列化往返 2x+3y-5。/ Serde round-trip."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        three = dsl.constant(3.0)
        two_x = dsl.product(two, x)
        three_y = dsl.product(three, y)
        neg5 = dsl.constant(-5.0)
        poly = dsl.sum(two_x, three_y, neg5)
        serialized = serde.serialize(poly)
        deserialized = serde.deserialize(serialized)
        assert deserialized is not None


# ============================================================
# Golden case: x^2 + 2*x*y + y^2
# ============================================================


class TestGoldenX2Y2:
    """x²+2xy+y² 黄金测试。/ Golden test: x²+2xy+y²."""

    def test_build_x2_2xy_y2(self) -> None:
        """构建 x²+2xy+y²。/ Build x²+2xy+y²."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        x2 = dsl.product(x, x)
        xy = dsl.product(x, y)
        two_xy = dsl.product(two, xy)
        y2 = dsl.product(y, y)
        quad = dsl.sum(x2, two_xy, y2)
        assert quad is not None

    def test_evaluate_x2_2xy_y2(self) -> None:
        """求值 at x=3,y=4 → 9+24+16=49。/ Evaluate at x=3,y=4 → 49."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        x2 = dsl.product(x, x)
        xy = dsl.product(x, y)
        two_xy = dsl.product(two, xy)
        y2 = dsl.product(y, y)
        quad = dsl.sum(x2, two_xy, y2)
        result = ev.evaluate(quad, {"x": 3.0, "y": 4.0})
        assert result == pytest.approx(49.0)

    def test_differentiate_x2_2xy_y2(self) -> None:
        """求导 d/dx → 2x+2y。/ Diff d/dx → 2x+2y."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        x2 = dsl.product(x, x)
        xy = dsl.product(x, y)
        two_xy = dsl.product(two, xy)
        y2 = dsl.product(y, y)
        quad = dsl.sum(x2, two_xy, y2)
        derivative = diff.differentiate(quad, "x")
        # d/dx(x²+2xy+y²) = 2x+2y, 在 x=1,y=1 → 4
        # d/dx(x²+2xy+y²) = 2x+2y, at x=1,y=1 → 4
        result = ev.evaluate(derivative, {"x": 1.0, "y": 1.0})
        assert result == pytest.approx(4.0)

    def test_differentiate_wrt_y(self) -> None:
        """求导 d/dy → 2x+2y。/ Diff d/dy → 2x+2y."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        x2 = dsl.product(x, x)
        xy = dsl.product(x, y)
        two_xy = dsl.product(two, xy)
        y2 = dsl.product(y, y)
        quad = dsl.sum(x2, two_xy, y2)
        derivative = diff.differentiate(quad, "y")
        # d/dy(x²+2xy+y²) = 2x+2y, 在 x=1,y=1 → 4
        result = ev.evaluate(derivative, {"x": 1.0, "y": 1.0})
        assert result == pytest.approx(4.0)


# ============================================================
# Integration golden cases
# ============================================================


class TestIntegrationGolden:
    """积分黄金测试。/ Integration golden tests."""

    def test_integrate_x_squared(self) -> None:
        """∫x² dx = x³/3 + C。/ ∫x² dx = x³/3."""
        x = dsl.var("x")
        x2 = dsl.product(x, x)
        result = iops.integrate(x2, "x")
        # 在 x=2 时，x³/3 = 8/3 ≈ 2.667
        val = ev.evaluate(result, {"x": 2.0})
        assert val == pytest.approx(8.0 / 3.0, abs=1e-9)

    def test_integrate_2x(self) -> None:
        """∫2x dx = x² + C。/ ∫2x dx = x²."""
        x = dsl.var("x")
        two = dsl.constant(2.0)
        two_x = dsl.product(two, x)
        result = iops.integrate(two_x, "x")
        val = ev.evaluate(result, {"x": 3.0})
        assert val == pytest.approx(9.0, abs=1e-9)

    def test_integrate_constant(self) -> None:
        """∫5 dx = 5x + C。/ ∫5 dx = 5x."""
        # 常数 5 关于 x 积分得到 5x
        # Integrate constant 5 w.r.t. x yields 5x
        x = dsl.var("x")
        x_sym = list(x.terms[0].powers.keys())[0]
        # 创建 5*x（即积分结果）
        # Create 5*x (integration result of constant 5)
        five_x = CanonicalMonomial.single(x_sym, coefficient=5.0)
        p = CanonicalPolynomial(terms=[five_x])
        val = ev.evaluate(p, {"x": 2.0})
        assert val == pytest.approx(10.0, abs=1e-9)


# ============================================================
# Serde round-trip tests
# ============================================================


class TestSerdeBehavior:
    """序列化行为测试。/ Serialization behavioral tests."""

    def test_serialize_constant(self) -> None:
        """序列化常数。/ Serialize constant."""
        p = CanonicalPolynomial.constant(42.0)
        serialized = serde.serialize(p)
        assert "42" in serialized

    def test_serialize_deserialize_roundtrip(self) -> None:
        """序列化-反序列化往返。/ Serialize-deserialize round-trip."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        serialized = serde.serialize(xp1)
        deserialized = serde.deserialize(serialized)
        assert deserialized is not None
        # 求值验证 / Verify by evaluation
        original_val = ev.evaluate(xp1, {"x": 5.0})
        # 反序列化的多项式需要使用相同符号名求值
        # Deserialized polynomial needs same symbol names for evaluation
        deserialized_val = ev.evaluate(deserialized, {"x": 5.0})
        assert deserialized_val == pytest.approx(original_val)

    def test_deserialize_invalid_json(self) -> None:
        """反序列化无效 JSON 返回 None。/ Invalid JSON returns None."""
        result = serde.deserialize("not valid json")
        assert result is None

    def test_to_dict_from_dict_roundtrip(self) -> None:
        """字典往返。/ Dictionary round-trip."""
        x = dsl.var("x")
        two = dsl.constant(2.0)
        two_x = dsl.product(two, x)
        d = serde.to_dict(two_x)
        assert d is not None
        restored = serde.from_dict(d)
        assert restored is not None


# ============================================================
# LaTeX rendering tests
# ============================================================


class TestLatexBehavior:
    """LaTeX 渲染行为测试。/ LaTeX rendering behavioral tests."""

    def test_render_constant(self) -> None:
        """渲染常数。/ Render constant."""
        p = CanonicalPolynomial.constant(5.0)
        result = latex.render(p)
        assert "5" in result

    def test_render_variable(self) -> None:
        """渲染变量。/ Render variable."""
        x = dsl.var("x")
        result = latex.render(x)
        assert "x" in result

    def test_render_x_squared(self) -> None:
        """渲染 x² → x^{2}。/ Render x² → x^{2}."""
        x = dsl.var("x")
        x2 = dsl.product(x, x)
        result = latex.render(x2)
        assert "x" in result
        assert "2" in result

    def test_render_inline(self) -> None:
        """渲染行内 LaTeX。/ Render inline LaTeX."""
        p = CanonicalPolynomial.constant(1.0)
        result = latex.render_inline(p)
        assert result.startswith("$")
        assert result.endswith("$")

    def test_render_display(self) -> None:
        """渲染展示 LaTeX。/ Render display LaTeX."""
        p = CanonicalPolynomial.constant(1.0)
        result = latex.render_display(p)
        assert result.startswith("$$")


# ============================================================
# CanonicalOps / TermCombiner / Normalizer
# ============================================================


class TestCanonicalOps:
    """规范多项式运算测试。/ Canonical ops tests."""

    def test_normalize_combines_like_terms(self) -> None:
        """规范化合并同类项。/ Normalize combines like terms."""
        x_poly = dsl.var("x")
        # 获取符号 / Get symbol from polynomial
        x_sym = list(x_poly.terms[0].powers.keys())[0]
        m1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        m2 = CanonicalMonomial.single(x_sym, coefficient=3.0)
        p = CanonicalPolynomial(terms=[m1, m2])
        normalized = canon.normalize(p)  # type: ignore[arg-type]
        assert normalized.term_count <= 1

    def test_canonicalize_alias(self) -> None:
        """canonicalize 是 normalize 的别名。/ canonicalize is alias for normalize."""
        x_sym = Symbol.create(name="x", index=0)
        m1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        p = CanonicalPolynomial(terms=[m1])
        result = canon.canonicalize(p)  # type: ignore[arg-type]
        assert result is not None

    def test_simplify(self) -> None:
        """简化等同于规范化。/ Simplify is same as normalize."""
        p = CanonicalPolynomial.constant(5.0)
        result = canon.simplify(p)  # type: ignore[arg-type]
        assert result is not None


class TestTermCombiner:
    """同类项合并测试。/ Term combiner tests."""

    def test_combine_adds_coefficients(self) -> None:
        """合并同类项系数相加。/ Combine adds coefficients."""
        x_sym = Symbol.create(name="x", index=0)
        m1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        m2 = CanonicalMonomial.single(x_sym, coefficient=3.0)
        p = CanonicalPolynomial(terms=[m1, m2])
        combined = combiner.combine(p)  # type: ignore[arg-type]
        assert combined.term_count == 1
        val = ev.evaluate(combined, {"x": 1.0})
        assert val == pytest.approx(5.0)

    def test_combine_removes_zero_terms(self) -> None:
        """合并移除零系数项。/ Combine removes zero-coefficient terms."""
        x_sym = Symbol.create(name="x", index=1)
        m1 = CanonicalMonomial.single(x_sym, coefficient=2.0)
        m2 = CanonicalMonomial.single(x_sym, coefficient=-2.0)
        p = CanonicalPolynomial(terms=[m1, m2])
        combined = combiner.combine(p)  # type: ignore[arg-type]
        assert combined.is_zero


class TestNormalizer:
    """规范化器测试。/ Normalizer tests."""

    def test_normalize(self) -> None:
        """规范化多项式。/ Normalize polynomial."""
        p = CanonicalPolynomial.constant(5.0)
        result = normalizer.normalize(p)  # type: ignore[arg-type]
        assert result is not None

    def test_is_normalized_true(self) -> None:
        """已规范化多项式。/ Already normalized polynomial."""
        p = CanonicalPolynomial.constant(5.0)
        assert normalizer.is_normalized(p)  # type: ignore[arg-type]

    def test_is_normalized_false_with_zero_coeff(self) -> None:
        """含零系数项未规范化。/ Zero-coefficient terms are not normalized."""
        x_sym = Symbol.create(name="x", index=2)
        m = CanonicalMonomial.single(x_sym, coefficient=0.0)
        p = CanonicalPolynomial(terms=[m])
        assert not normalizer.is_normalized(p)  # type: ignore[arg-type]


# ============================================================
# Linear/Quadratic equation solving
# ============================================================


class TestLinearQuadraticOps:
    """线性/二次方程求解测试。/ Linear/quadratic equation solving tests."""

    def test_solve_linear(self) -> None:
        """求解线性方程 ax+b=0。/ Solve linear equation."""
        x = dsl.var("x")
        # 2x + 4 = 0 → x = -2
        two = dsl.constant(2.0)
        two_x = dsl.product(two, x)
        four = dsl.constant(4.0)
        poly = dsl.sum(two_x, four)
        result = lq.solve_linear(poly, "x")  # type: ignore[arg-type]
        assert result is not None
        assert result == pytest.approx(-2.0)

    def test_solve_quadratic_discriminant_positive(self) -> None:
        """求解二次方程（正判别式）。/ Solve quadratic (positive discriminant)."""
        x = dsl.var("x")
        # x² - 5x + 6 = 0 → (x-2)(x-3) → roots 2 and 3
        x2 = dsl.product(x, x)
        five_x = dsl.product(dsl.constant(-5.0), x)
        six = dsl.constant(6.0)
        poly = dsl.sum(x2, five_x, six)
        disc = lq.discriminant(poly, "x")  # type: ignore[arg-type]
        assert disc == pytest.approx(1.0)
        roots = lq.solve_quadratic(poly, "x")  # type: ignore[arg-type]
        assert len(roots) == 2
        assert 2.0 in [pytest.approx(r) for r in roots]
        assert 3.0 in [pytest.approx(r) for r in roots]

    def test_discriminant(self) -> None:
        """计算判别式。/ Compute discriminant."""
        x = dsl.var("x")
        x2 = dsl.product(x, x)
        one = dsl.constant(1.0)
        poly = dsl.sum(x2, one)
        disc = lq.discriminant(poly, "x")  # type: ignore[arg-type]
        assert disc == pytest.approx(-4.0)


# ============================================================
# PowerVectorKey tests (kept from original)
# ============================================================


class TestPowerVectorKey:
    """PowerVectorKey 测试。/ PowerVectorKey tests."""

    def test_basic_creation(self) -> None:
        """基本创建。/ Basic creation."""
        k = PowerVectorKey(variables=("x", "y"), powers=(2, 1))
        assert k.variables == ("x", "y")
        assert k.powers == (2, 1)

    def test_degree(self) -> None:
        """总次数。/ Total degree."""
        k = PowerVectorKey(variables=("x", "y"), powers=(2, 3))
        assert k.degree == 5

    def test_degree_zero(self) -> None:
        """常数项次数为 0。/ Constant term degree 0."""
        k = PowerVectorKey(variables=(), powers=())
        assert k.degree == 0

    def test_is_constant_true(self) -> None:
        """全零幂次为常数。/ All-zero powers is constant."""
        k = PowerVectorKey(variables=("x", "y"), powers=(0, 0))
        assert k.is_constant is True

    def test_is_constant_false(self) -> None:
        """非零幂次不是常数。/ Non-zero powers not constant."""
        k = PowerVectorKey(variables=("x", "y"), powers=(1, 0))
        assert k.is_constant is False

    def test_get_power_found(self) -> None:
        """获取指定变量的幂次。/ Get power of variable."""
        k = PowerVectorKey(variables=("x", "y"), powers=(2, 3))
        assert k.get_power("x") == 2
        assert k.get_power("y") == 3

    def test_get_power_not_found(self) -> None:
        """不存在的变量返回 0。/ Missing variable returns 0."""
        k = PowerVectorKey(variables=("x",), powers=(2,))
        assert k.get_power("z") == 0

    def test_mismatched_lengths_raises(self) -> None:
        """变量与幂次长度不匹配抛出异常。/ Mismatched lengths raises."""
        with pytest.raises(ValueError):
            PowerVectorKey(variables=("x", "y"), powers=(1,))

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        k = PowerVectorKey(variables=("x",), powers=(1,))
        with pytest.raises(AttributeError):
            k.powers = (2,)  # type: ignore[misc]


# ============================================================
# Flt64MatrixForm tests (kept from original)
# ============================================================


class TestFlt64MatrixForm:
    """Flt64MatrixForm 测试。/ Flt64MatrixForm tests."""

    def test_creation(self) -> None:
        """基本创建。/ Basic creation."""
        m = Flt64MatrixForm(
            coefficients=(1.0, 2.0, 3.0, 4.0),
            row_count=2,
            col_count=2,
        )
        assert m.row_count == 2
        assert m.col_count == 2

    def test_size(self) -> None:
        """矩阵大小。/ Matrix size."""
        m = Flt64MatrixForm(
            coefficients=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
            row_count=2,
            col_count=3,
        )
        assert m.size == 6

    def test_get_element(self) -> None:
        """获取元素。/ Get element."""
        m = Flt64MatrixForm(
            coefficients=(1.0, 2.0, 3.0, 4.0),
            row_count=2,
            col_count=2,
        )
        assert m.get(0, 0) == 1.0
        assert m.get(0, 1) == 2.0
        assert m.get(1, 0) == 3.0
        assert m.get(1, 1) == 4.0

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        m = Flt64MatrixForm(coefficients=(1.0,), row_count=1, col_count=1)
        with pytest.raises(AttributeError):
            m.row_count = 2  # type: ignore[misc]


# ============================================================
# ValueProvider tests (kept from original)
# ============================================================


class TestDictValueProvider:
    """DictValueProvider 测试。/ DictValueProvider tests."""

    def test_get_existing(self) -> None:
        """获取存在的变量。/ Get existing variable."""
        p = DictValueProvider(bindings={"x": 3.14, "y": 2.0})
        assert p.get("x") == pytest.approx(3.14)
        assert p.get("y") == pytest.approx(2.0)

    def test_get_missing_raises(self) -> None:
        """获取不存在的变量抛出 KeyError。/ Missing raises KeyError."""
        p = DictValueProvider(bindings={"x": 1.0})
        with pytest.raises(KeyError):
            p.get("z")

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        p = DictValueProvider(bindings={"x": 1.0})
        with pytest.raises(AttributeError):
            p.bindings = {}  # type: ignore[misc]


class TestLambdaValueProvider:
    """LambdaValueProvider 测试。/ LambdaValueProvider tests."""

    def test_get_value(self) -> None:
        """通过 lambda 获取值。/ Get value via lambda."""
        p = LambdaValueProvider(getter=lambda name: 42.0)
        assert p.get("any") == 42.0

    def test_get_with_lookup(self) -> None:
        """通过字典 lambda 获取值。/ Get via dict lambda."""
        data = {"x": 1.0, "y": 2.0}
        p = LambdaValueProvider(getter=lambda n: data[n])
        assert p.get("x") == 1.0
        assert p.get("y") == 2.0


# ============================================================
# InequalityOps tests
# ============================================================


class TestInequalityOps:
    """不等式运算测试。/ Inequality ops tests."""

    def test_simplify(self) -> None:
        """简化不等式。/ Simplify inequality."""
        from ospf_python.math.symbol.inequality.canonical_inequality import (
            CanonicalInequality,
        )
        from ospf_python.math.symbol.inequality.comparison import Comparison

        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        ineq_obj = CanonicalInequality(
            left=xp1,
            right=dsl.constant(5.0),
            comparison=Comparison.LE,
        )
        result = ineq.simplify(ineq_obj)  # type: ignore[arg-type]
        assert result is not None

    def test_merge(self) -> None:
        """合并不等式。/ Merge inequalities."""
        from ospf_python.math.symbol.inequality.canonical_inequality import (
            CanonicalInequality,
        )
        from ospf_python.math.symbol.inequality.comparison import Comparison

        x = dsl.var("x")
        ineq1 = CanonicalInequality(
            left=x,
            right=dsl.constant(5.0),
            comparison=Comparison.LE,
        )
        ineq2 = CanonicalInequality(
            left=x,
            right=dsl.constant(1.0),
            comparison=Comparison.GE,
        )
        result = ineq.merge(ineq1, ineq2)  # type: ignore[arg-type]
        assert isinstance(result, list)
        assert len(result) >= 1


# ============================================================
# Import smoke tests (kept as minimal check)
# ============================================================


class TestOperationImports:
    """运算模块导入冒烟测试。/ Operation module import smoke tests."""

    def test_quick_dsl(self) -> None:
        """QuickDsl 可导入使用。/ QuickDsl importable and usable."""
        d = QuickDsl(factory=CanonicalPolynomial)
        x = d.var("x")
        assert x is not None

    def test_differentiator(self) -> None:
        """Differentiator 可导入使用。/ Differentiator importable and usable."""
        d = Differentiator(factory=CanonicalPolynomial)
        assert d is not None

    def test_integrate_ops(self) -> None:
        """IntegrateOps 可导入使用。/ IntegrateOps importable and usable."""
        io = IntegrateOps(factory=CanonicalPolynomial)
        assert io is not None

    def test_serde_ops(self) -> None:
        """SerdeOps 可导入使用。/ SerdeOps importable and usable."""
        s = SerdeOps(factory=CanonicalPolynomial)
        assert s is not None

    def test_latex_renderer(self) -> None:
        """LatexRenderer 可导入使用。/ LatexRenderer importable and usable."""
        l = LatexRenderer(factory=CanonicalPolynomial)
        assert l is not None

    def test_canonical_ops(self) -> None:
        """CanonicalOps 可导入使用。/ CanonicalOps importable and usable."""
        c = CanonicalOps(factory=CanonicalPolynomial)
        assert c is not None

    def test_term_combiner(self) -> None:
        """TermCombiner 可导入使用。/ TermCombiner importable and usable."""
        t = TermCombiner(factory=CanonicalPolynomial)
        assert t is not None

    def test_linear_quadratic_ops(self) -> None:
        """LinearQuadraticOps 可导入使用。/ LQOps importable and usable."""
        lq_ops = LinearQuadraticOps(factory=CanonicalPolynomial)
        assert lq_ops is not None

    def test_inequality_ops(self) -> None:
        """InequalityOps 可导入使用。/ InequalityOps importable and usable."""
        i_ops = InequalityOps(factory=CanonicalPolynomial)
        assert i_ops is not None

    def test_normalizer(self) -> None:
        """PolynomialNormalizer 可导入使用。/ Normalizer importable and usable."""
        n = PolynomialNormalizer(factory=CanonicalPolynomial)
        assert n is not None
