"""Math symbol operation module coverage tests.

Tests for compile, convert, factorization, number_parser,
quick_ops, flt64_quick_ops, flt64_quick_dsl, to_polynomial,
matrix_form, inequality_dsl, latex_ops, compile_ops,
convert_ops, differentiate_ops, mutable_combine_ops.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from ospf_python.math.symbol.monomial.canonical_monomial import CanonicalMonomial
from ospf_python.math.symbol.monomial.linear_monomial import LinearMonomial
from ospf_python.math.symbol.operation.compile import (
    PolynomialCompiler,
)
from ospf_python.math.symbol.operation.convert import PolynomialConverter
from ospf_python.math.symbol.operation.differentiate import Differentiator
from ospf_python.math.symbol.operation.factorization import (
    Factor,
    Factorization,
    PolynomialFactorizer,
)
from ospf_python.math.symbol.operation.flt64_matrix_form import Flt64MatrixForm
from ospf_python.math.symbol.operation.flt64_quick_dsl import Flt64QuickDsl
from ospf_python.math.symbol.operation.flt64_quick_ops import Flt64QuickOps
from ospf_python.math.symbol.operation.inequality_dsl import InequalityDsl
from ospf_python.math.symbol.operation.latex import LatexRenderer
from ospf_python.math.symbol.operation.latex_ops import LatexOps
from ospf_python.math.symbol.operation.matrix_form import MatrixForm
from ospf_python.math.symbol.operation.mutable_combine_ops import MutableCombineOps
from ospf_python.math.symbol.operation.number_parser import NumberParser
from ospf_python.math.symbol.operation.parse import PolynomialStringParser
from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
from ospf_python.math.symbol.operation.quick_ops import QuickOps
from ospf_python.math.symbol.operation.to_polynomial import ToPolynomial
from ospf_python.math.symbol.polynomial.canonical_polynomial import CanonicalPolynomial
from ospf_python.math.symbol.polynomial.linear_polynomial import LinearPolynomial
from ospf_python.math.symbol.polynomial.quadratic_polynomial import QuadraticPolynomial
from ospf_python.math.symbol.symbol import Symbol

FACTORY = CanonicalPolynomial
dsl = QuickDsl(factory=FACTORY)
f64_dsl = Flt64QuickDsl()
compiler = PolynomialCompiler(factory=FACTORY)
converter = PolynomialConverter(source_factory=FACTORY, target_factory=LinearPolynomial)
factorizer = PolynomialFactorizer(factory=FACTORY)
differentiator = Differentiator(factory=FACTORY)
to_poly = ToPolynomial(factory=FACTORY)
quick_ops = QuickOps(factory=FACTORY)
flt64_ops = Flt64QuickOps()
ineq_dsl = InequalityDsl(factory=FACTORY)
latex_renderer = LatexRenderer(factory=FACTORY)
latex_ops_obj = LatexOps(renderer=latex_renderer)
mutable_combiner = MutableCombineOps(factory=FACTORY)


# ============================================================
# PolynomialCompiler tests
# ============================================================


class TestPolynomialCompiler:
    """多项式编译器测试。/ Polynomial compiler tests."""

    def test_compile_x_plus_1(self) -> None:
        """编译 x+1。/ Compile x+1."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        compiled = compiler.compile(xp1)
        result = compiled.evaluate({"x": 2.0})
        assert result == pytest.approx(3.0)

    def test_compile_x_squared(self) -> None:
        """编译 x²。/ Compile x²."""
        x = dsl.var("x")
        x2 = dsl.product(x, x)
        compiled = compiler.compile(x2)
        result = compiled.evaluate({"x": 3.0})
        assert result == pytest.approx(9.0)

    def test_compile_preserves_source(self) -> None:
        """编译保留源多项式。/ Compile preserves source polynomial."""
        p = CanonicalPolynomial.constant(42.0)
        compiled = compiler.compile(p)
        assert compiled.source is p

    def test_compile_unsupported_type_raises(self) -> None:
        """编译不支持的类型抛异常。/ Compile unsupported type raises."""
        with pytest.raises(TypeError):
            compiler.compile("not a polynomial")  # type: ignore[arg-type]

    def test_compiled_polynomial_evaluate_multi_var(self) -> None:
        """编译多变量多项式。/ Compile multi-variable polynomial."""
        x = dsl.var("x")
        y = dsl.var("y")
        two = dsl.constant(2.0)
        three = dsl.constant(3.0)
        two_x = dsl.product(two, x)
        three_y = dsl.product(three, y)
        poly = dsl.sum(two_x, three_y)
        compiled = compiler.compile(poly)
        result = compiled.evaluate({"x": 1.0, "y": 2.0})
        assert result == pytest.approx(8.0)


# ============================================================
# PolynomialConverter tests
# ============================================================


class TestPolynomialConverter:
    """多项式类型转换测试。/ Polynomial converter tests."""

    def test_convert_canonical_to_linear(self) -> None:
        """标准→线性。/ Canonical → Linear."""
        x_sym = Symbol.create(name="x", index=0)
        m = CanonicalMonomial.single(x_sym, coefficient=3.0)
        p = CanonicalPolynomial(terms=[m])
        result = converter.convert(p)
        assert result is not None

    def test_convert_constant(self) -> None:
        """常数转换。/ Constant conversion."""
        p = CanonicalPolynomial.constant(7.0)
        result = converter.convert(p)
        assert result is not None


# ============================================================
# NumberParser tests
# ============================================================


class TestNumberParser:
    """数值解析器测试。/ Number parser tests."""

    def test_parse_integer(self) -> None:
        """解析整数。/ Parse integer."""
        assert NumberParser(input="42").parse() == 42

    def test_parse_negative_integer(self) -> None:
        """解析负整数。/ Parse negative integer."""
        assert NumberParser(input="-5").parse() == -5

    def test_parse_float(self) -> None:
        """解析浮点数。/ Parse float."""
        assert NumberParser(input="3.14").parse() == pytest.approx(3.14)

    def test_parse_scientific(self) -> None:
        """解析科学记数法。/ Parse scientific notation."""
        assert NumberParser(input="1e3").parse() == pytest.approx(1000.0)

    def test_parse_fraction(self) -> None:
        """解析分数。/ Parse fraction."""
        result = NumberParser(input="3/4").parse()
        assert result == Fraction(3, 4)

    def test_parse_empty_returns_none(self) -> None:
        """空字符串返回 None。/ Empty string returns None."""
        assert NumberParser(input="").parse() is None

    def test_parse_whitespace_returns_none(self) -> None:
        """空白字符串返回 None。/ Whitespace returns None."""
        assert NumberParser(input="   ").parse() is None

    def test_parse_invalid_returns_none(self) -> None:
        """无效字符串返回 None。/ Invalid string returns None."""
        assert NumberParser(input="abc").parse() is None

    def test_parse_zero_division_fraction(self) -> None:
        """分母为零的分数返回 None。/ Zero denominator returns None."""
        assert NumberParser(input="1/0").parse() is None


# ============================================================
# Factorization tests
# ============================================================


class TestFactorization:
    """因式分解测试。/ Factorization tests."""

    def test_factor_creation(self) -> None:
        """因子创建。/ Factor creation."""
        p = CanonicalPolynomial.constant(5.0)
        f = Factor(expression=p, multiplicity=2)
        assert f.expression is p
        assert f.multiplicity == 2

    def test_factorization_creation(self) -> None:
        """因式分解结果创建。/ Factorization result creation."""
        p = CanonicalPolynomial.constant(6.0)
        fact = Factorization(factors=(Factor(expression=p, multiplicity=1),))
        assert len(fact.factors) == 1

    def test_factorizer_basic(self) -> None:
        """基础因式分解。/ Basic factorization."""
        p = CanonicalPolynomial.constant(12.0)
        result = factorizer.factorize(p)
        assert len(result.factors) >= 1

    def test_factorizer_returns_self_for_constant(self) -> None:
        """常数因式分解返回自身。/ Constant factorization returns self."""
        p = CanonicalPolynomial.constant(5.0)
        result = factorizer.factorize(p)
        assert result.factors[0].multiplicity == 1


# ============================================================
# ToPolynomial tests
# ============================================================


class TestToPolynomial:
    """转换为多项式测试。/ ToPolynomial tests."""

    def test_from_dict(self) -> None:
        """从字典转换。/ Convert from dict."""
        data = {"terms": [{"coefficient": 2.0, "powers": {"x": 1}}]}
        result = to_poly.from_dict(data)
        assert result is not None

    def test_from_list(self) -> None:
        """从列表转换。/ Convert from list."""
        data = [{"coefficient": 1.0, "powers": {}}]
        result = to_poly.from_list(data, variable="x")
        assert result is not None


# ============================================================
# QuickOps / Flt64QuickOps tests
# ============================================================


class TestQuickOps:
    """快速运算测试。/ Quick ops tests."""

    def test_quick_ops_simplify(self) -> None:
        """QuickOps.simplify。/ QuickOps simplify."""
        x = dsl.var("x")
        result = quick_ops.simplify(x)
        assert result is not None

    def test_quick_ops_collect(self) -> None:
        """QuickOps.collect。/ QuickOps collect."""
        x = dsl.var("x")
        result = quick_ops.collect(x, "x")
        assert result is not None

    def test_quick_ops_expand(self) -> None:
        """QuickOps.expand。/ QuickOps expand."""
        x = dsl.var("x")
        result = quick_ops.expand(x)
        assert result is not None


class TestFlt64QuickDsl:
    """Flt64 快速 DSL 测试。/ Flt64 quick DSL tests."""

    def test_flt64_var(self) -> None:
        """Flt64QuickDsl.var。/ Flt64 var."""
        x = f64_dsl.var("x")
        assert x is not None

    def test_flt64_constant(self) -> None:
        """Flt64QuickDsl.constant。/ Flt64 constant."""
        c = f64_dsl.constant(3.14)
        assert c is not None

    def test_flt64_namespace(self) -> None:
        """Flt64QuickDsl.namespace。/ Flt64 namespace."""
        dsl_ns = Flt64QuickDsl(namespace="test")
        assert dsl_ns.namespace == "test"


class TestFlt64QuickOps:
    """Flt64 快速运算测试。/ Flt64 quick ops tests."""

    def test_flt64_quick_ops_creation(self) -> None:
        """Flt64QuickOps 创建。/ Flt64QuickOps creation."""
        ops = Flt64QuickOps(tolerance=1e-9)
        assert ops is not None


# ============================================================
# MatrixForm / Flt64MatrixForm tests
# ============================================================


class TestMatrixForm:
    """矩阵形式测试。/ Matrix form tests."""

    def test_matrix_form_creation(self) -> None:
        """矩阵形式创建。/ Matrix form creation."""
        x = dsl.var("x")
        mf = MatrixForm(source=x, row_labels=("r1",), col_labels=("x",))
        assert mf is not None

    def test_matrix_form_rows_cols(self) -> None:
        """矩阵行列。/ Matrix rows and cols."""
        x = dsl.var("x")
        mf = MatrixForm(source=x, row_labels=("r1", "r2"), col_labels=("x",))
        assert mf.rows is not None
        assert mf.cols is not None

    def test_flt64_matrix_form(self) -> None:
        """Flt64 矩阵形式。/ Flt64 matrix form."""
        mf = Flt64MatrixForm(coefficients=(1.0, 2.0, 3.0, 4.0), row_count=2, col_count=2)
        assert mf.row_count == 2
        assert mf.col_count == 2
        assert mf.get(0, 0) == 1.0
        assert mf.get(1, 1) == 4.0


# ============================================================
# InequalityDsl tests
# ============================================================


class TestInequalityDsl:
    """不等式 DSL 测试。/ Inequality DSL tests."""

    def test_inequality_dsl_le(self) -> None:
        """不等式 DSL le。/ Inequality DSL le."""
        x = dsl.var("x")
        five = dsl.constant(5.0)
        ineq = ineq_dsl.le(x, five)
        assert ineq is not None

    def test_inequality_dsl_ge(self) -> None:
        """不等式 DSL ge。/ Inequality DSL ge."""
        x = dsl.var("x")
        one = dsl.constant(1.0)
        ineq = ineq_dsl.ge(x, one)
        assert ineq is not None

    def test_inequality_dsl_lt(self) -> None:
        """不等式 DSL lt。/ Inequality DSL lt."""
        x = dsl.var("x")
        ten = dsl.constant(10.0)
        ineq = ineq_dsl.lt(x, ten)
        assert ineq is not None

    def test_inequality_dsl_gt(self) -> None:
        """不等式 DSL gt。/ Inequality DSL gt."""
        x = dsl.var("x")
        zero = dsl.constant(0.0)
        ineq = ineq_dsl.gt(x, zero)
        assert ineq is not None

    def test_inequality_dsl_eq(self) -> None:
        """不等式 DSL eq。/ Inequality DSL eq."""
        x = dsl.var("x")
        three = dsl.constant(3.0)
        ineq = ineq_dsl.eq(x, three)
        assert ineq is not None


# ============================================================
# LatexOps tests
# ============================================================


class TestLatexOps:
    """LaTeX 运算测试。/ LaTeX ops tests."""

    def test_latex_ops_to_latex(self) -> None:
        """LaTeX 运算转换。/ LaTeX ops to_latex."""
        p = CanonicalPolynomial.constant(42.0)
        result = latex_ops_obj.to_latex(p)
        assert result is not None


# ============================================================
# MutableCombineOps tests
# ============================================================


class TestMutableCombineOps:
    """可变合并运算测试。/ Mutable combine ops tests."""

    def test_mutable_combine_sum(self) -> None:
        """可变合并求和。/ Mutable combine sum."""
        p1 = CanonicalPolynomial.constant(1.0)
        p2 = CanonicalPolynomial.constant(2.0)
        result = mutable_combiner.sum((p1, p2))
        assert result is not None

    def test_mutable_combine_product(self) -> None:
        """可变合并乘积。/ Mutable combine product."""
        p1 = CanonicalPolynomial.constant(2.0)
        p2 = CanonicalPolynomial.constant(3.0)
        result = mutable_combiner.product((p1, p2))
        assert result is not None


# ============================================================
# Op registry tests (CompileOps, ConvertOps, DifferentiateOps, LatexOps)
# ============================================================


class TestOpRegistries:
    """运算注册表测试。/ Operation registry tests."""

    def test_compile_ops_registry(self) -> None:
        """编译运算注册表。/ Compile ops registry."""
        from ospf_python.math.symbol.operation.compile_ops import CompileOps
        ops = CompileOps(compiler=compiler)
        assert ops is not None

    def test_compile_ops_compile_and_evaluate(self) -> None:
        """编译运算求值。/ Compile ops compile and evaluate."""
        from ospf_python.math.symbol.operation.compile_ops import CompileOps
        ops = CompileOps(compiler=compiler)
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        result = ops.compile_and_evaluate(xp1, {"x": 2.0})
        assert result == pytest.approx(3.0)

    def test_convert_ops_registry(self) -> None:
        """转换运算注册表。/ Convert ops registry."""
        from ospf_python.math.symbol.operation.convert_ops import ConvertOps
        ops = ConvertOps(converter=converter)
        assert ops is not None

    def test_convert_ops_to_target(self) -> None:
        """转换运算目标转换。/ Convert ops to_target."""
        from ospf_python.math.symbol.operation.convert_ops import ConvertOps
        ops = ConvertOps(converter=converter)
        p = CanonicalPolynomial.constant(5.0)
        result = ops.to_target(p)
        assert result is not None

    def test_differentiate_ops_registry(self) -> None:
        """求导运算注册表。/ Differentiate ops registry."""
        from ospf_python.math.symbol.operation.differentiate_ops import DifferentiateOps
        ops = DifferentiateOps(differentiator=differentiator)
        assert ops is not None

    def test_differentiate_ops_grad(self) -> None:
        """求导运算梯度。/ Differentiate ops grad."""
        from ospf_python.math.symbol.operation.differentiate_ops import DifferentiateOps
        ops = DifferentiateOps(differentiator=differentiator)
        x = dsl.var("x")
        x2 = dsl.product(x, x)
        grad = ops.grad(x2, ["x"])
        assert grad is not None

    def test_latex_ops_registry(self) -> None:
        """LaTeX 运算注册表。/ LaTeX ops registry."""
        from ospf_python.math.symbol.operation.latex_ops import LatexOps
        ops = LatexOps(renderer=latex_renderer)
        assert ops is not None

    def test_latex_ops_to_latex(self) -> None:
        """LaTeX 运算转换。/ LaTeX ops to_latex."""
        from ospf_python.math.symbol.operation.latex_ops import LatexOps
        ops = LatexOps(renderer=latex_renderer)
        p = CanonicalPolynomial.constant(1.0)
        result = ops.to_latex(p)
        assert result is not None


# ============================================================
# Network scheduling context tests (cover 0% files)
# ============================================================


class TestNetworkSchedulingContexts:
    """网络排程上下文测试。/ Network scheduling context tests."""

    def test_edge_context_creation(self) -> None:
        """边上下文创建。/ Edge context creation."""
        from ospf_python.framework.network_scheduling.domain.edge.edge_context import (
            EdgeContext,
        )
        ctx = EdgeContext(network_key="net1")
        assert ctx.network_key == "net1"

    def test_edge_context_with_params(self) -> None:
        """边上下文带参数。/ Edge context with params."""
        from ospf_python.framework.network_scheduling.domain.edge.edge_context import (
            EdgeContext,
        )
        ctx = EdgeContext(network_key="net1", from_node_key="A", to_node_key="B", max_cost=10.0)
        assert ctx.from_node_key == "A"
        assert ctx.to_node_key == "B"
        assert ctx.max_cost == pytest.approx(10.0)

    def test_node_context_creation(self) -> None:
        """节点上下文创建。/ Node context creation."""
        from ospf_python.framework.network_scheduling.domain.node.node_context import (
            NodeContext,
        )
        ctx = NodeContext(network_key="net1")
        assert ctx.network_key == "net1"

    def test_node_context_with_params(self) -> None:
        """节点上下文带参数。/ Node context with params."""
        from ospf_python.framework.network_scheduling.domain.node.node_context import (
            NodeContext,
        )
        ctx = NodeContext(network_key="net1", filter_type="SOURCE", max_results=10)
        assert ctx.filter_type == "SOURCE"
        assert ctx.max_results == 10

    def test_flow_context_creation(self) -> None:
        """流上下文创建。/ Flow context creation."""
        from ospf_python.framework.network_scheduling.domain.flow.flow_context import (
            FlowContext,
        )
        ctx = FlowContext(network_key="net1")
        assert ctx.network_key == "net1"

    def test_flow_context_with_params(self) -> None:
        """流上下文带参数。/ Flow context with params."""
        from ospf_python.framework.network_scheduling.domain.flow.flow_context import (
            FlowContext,
        )
        ctx = FlowContext(network_key="net1", edge_key="e1", min_amount=1.0, max_amount=10.0)
        assert ctx.edge_key == "e1"
        assert ctx.min_amount == pytest.approx(1.0)
        assert ctx.max_amount == pytest.approx(10.0)


# ============================================================
# CSP1D generation service context tests
# ============================================================


class TestCSP1DGenerationServiceContexts:
    """CSP1D 切割方案生成服务上下文测试。/ CSP1D generation service context tests."""

    def test_concurrent_generation_cache_creation(self) -> None:
        """并发生成缓存创建。/ Concurrent generation cache creation."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.concurrent_generation_material_slice_template_cache import (
            ConcurrentGenerationMaterialSliceTemplateCache,
        )
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        assert cache is not None

    def test_generation_quantity_cache_creation(self) -> None:
        """生成数量缓存创建。/ Generation quantity cache creation."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_quantity_cache import (
            GenerationQuantityCache,
        )
        cache = GenerationQuantityCache()
        assert cache is not None

    def test_generation_slice_template_cache_creation(self) -> None:
        """生成切片模板缓存创建。/ Generation slice template cache creation."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_slice_template_cache import (
            GenerationSliceTemplateCache,
        )
        cache = GenerationSliceTemplateCache()
        assert cache is not None

    def test_generation_material_width_index_cache_creation(self) -> None:
        """生成材料宽度索引缓存创建。/ Generation material width index cache creation."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_material_width_index_cache import (
            GenerationMaterialWidthIndexCache,
        )
        cache = GenerationMaterialWidthIndexCache()
        assert cache is not None

    def test_generation_template_reuse_creation(self) -> None:
        """生成模板重用创建。/ Generation template reuse creation."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_template_reuse import (
            GenerationTemplateReuse,
        )
        reuse = GenerationTemplateReuse()
        assert reuse is not None

    def test_generation_width_index_creation(self) -> None:
        """生成宽度索引创建。/ Generation width index creation."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_width_index import (
            GenerationWidthIndex,
        )
        index = GenerationWidthIndex()
        assert index is not None


# ============================================================
# PolynomialConverter deeper tests
# ============================================================


class TestPolynomialConverterDeep:
    """多项式类型转换深度测试。/ Polynomial converter deep tests."""

    def test_canonical_to_linear_with_constant(self) -> None:
        """标准→线性（含常数项）。/ Canonical → Linear with constant."""
        x_sym = Symbol.create(name="x", index=0)
        m = CanonicalMonomial.single(x_sym, coefficient=3.0)
        c = CanonicalMonomial.constant(5.0)
        p = CanonicalPolynomial(terms=[m, c])
        result = converter.convert(p)
        assert result is not None

    def test_canonical_to_quadratic(self) -> None:
        """标准→二次。/ Canonical → Quadratic."""
        q_converter = PolynomialConverter(source_factory=FACTORY, target_factory=QuadraticPolynomial)
        x_sym = Symbol.create(name="x", index=0)
        y_sym = Symbol.create(name="y", index=1)
        # x^2 + 2xy + y^2
        x2 = CanonicalMonomial(coefficient=1.0, powers={x_sym: 2})
        xy = CanonicalMonomial(coefficient=2.0, powers={x_sym: 1, y_sym: 1})
        y2 = CanonicalMonomial(coefficient=1.0, powers={y_sym: 2})
        p = CanonicalPolynomial(terms=[x2, xy, y2])
        result = q_converter.convert(p)
        assert result is not None

    def test_linear_to_canonical(self) -> None:
        """线性→标准。/ Linear → Canonical."""
        l2c = PolynomialConverter(source_factory=LinearPolynomial, target_factory=FACTORY)
        x_sym = Symbol.create(name="x", index=0)
        linear = LinearPolynomial(
            terms=[LinearMonomial.create(symbol=x_sym, coefficient=3.0)],
            constant=2.0,
        )
        result = l2c.convert(linear)
        assert result is not None

    def test_same_type_passthrough(self) -> None:
        """同类型直接返回。/ Same type returns as-is."""
        c2c = PolynomialConverter(source_factory=FACTORY, target_factory=FACTORY)
        p = CanonicalPolynomial.constant(5.0)
        result = c2c.convert(p)
        assert result is p

    def test_unsupported_conversion_raises(self) -> None:
        """不支持的转换抛异常。/ Unsupported conversion raises."""
        bad_converter = PolynomialConverter(source_factory=str, target_factory=int)
        with pytest.raises(TypeError):
            bad_converter.convert("hello")


# ============================================================
# PolynomialStringParser deeper tests
# ============================================================


class TestPolynomialStringParserDeep:
    """多项式字符串解析深度测试。/ Polynomial string parser deep tests."""

    def test_parse_simple_variable(self) -> None:
        """解析简单变量。/ Parse simple variable."""
        parser = PolynomialStringParser(factory=FACTORY)
        result = parser.parse("x")
        assert result is not None

    def test_parse_coefficient_variable(self) -> None:
        """解析系数变量。/ Parse coefficient variable."""
        parser = PolynomialStringParser(factory=FACTORY)
        result = parser.parse("2*x")
        assert result is not None

    def test_parse_polynomial_expression(self) -> None:
        """解析多项式表达式。/ Parse polynomial expression."""
        parser = PolynomialStringParser(factory=FACTORY)
        result = parser.parse("2*x + 3*y - 5")
        assert result is not None

    def test_parse_power_expression(self) -> None:
        """解析幂次表达式。/ Parse power expression."""
        parser = PolynomialStringParser(factory=FACTORY)
        result = parser.parse("x^2")
        assert result is not None

    def test_parse_constant_only(self) -> None:
        """解析纯常数。/ Parse constant only."""
        parser = PolynomialStringParser(factory=FACTORY)
        result = parser.parse("42")
        assert result is not None

    def test_parse_empty_returns_none(self) -> None:
        """空字符串返回 None。/ Empty returns None."""
        parser = PolynomialStringParser(factory=FACTORY)
        result = parser.parse("")
        assert result is None

    def test_parse_whitespace_returns_none(self) -> None:
        """空白字符串返回 None。/ Whitespace returns None."""
        parser = PolynomialStringParser(factory=FACTORY)
        result = parser.parse("   ")
        assert result is None

    def test_parse_unsupported_factory_raises(self) -> None:
        """不支持的工厂类型抛异常。/ Unsupported factory raises."""
        parser = PolynomialStringParser(factory=str)
        with pytest.raises(TypeError):
            parser.parse("x")


# ============================================================
# SymbolIdentitySerde tests
# ============================================================


class TestSymbolIdentitySerde:
    """符号标识序列化测试。/ Symbol identity serde tests."""

    def test_serialize_without_namespace(self) -> None:
        """无命名空间序列化。/ Serialize without namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )
        serde = SymbolIdentitySerde()
        assert serde.serialize("x") == "x"

    def test_serialize_with_namespace(self) -> None:
        """有命名空间序列化。/ Serialize with namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )
        serde = SymbolIdentitySerde(namespace="ns")
        assert serde.serialize("x") == "ns.x"

    def test_deserialize_without_namespace(self) -> None:
        """无命名空间反序列化。/ Deserialize without namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )
        serde = SymbolIdentitySerde()
        assert serde.deserialize("x") == "x"

    def test_deserialize_with_namespace(self) -> None:
        """有命名空间反序列化。/ Deserialize with namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )
        serde = SymbolIdentitySerde(namespace="ns")
        assert serde.deserialize("ns.x") == "x"

    def test_deserialize_wrong_namespace(self) -> None:
        """错误命名空间反序列化。/ Deserialize wrong namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )
        serde = SymbolIdentitySerde(namespace="ns1")
        # Wrong namespace prefix → returns as-is
        assert serde.deserialize("ns2.x") == "ns2.x"

    def test_roundtrip(self) -> None:
        """序列化-反序列化往返。/ Serde roundtrip."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )
        serde = SymbolIdentitySerde(namespace="poly")
        original = "variable"
        serialized = serde.serialize(original)
        deserialized = serde.deserialize(serialized)
        assert deserialized == original
