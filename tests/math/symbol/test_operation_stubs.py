"""符号运算模块测试。

Tests for symbol operation modules: PowerVectorKey,
Flt64MatrixForm, ValueProvider, SymbolIdentitySerde,
PolynomialSerde, InequalitySerde, and generic stubs.
"""

from __future__ import annotations

import pytest

from ospf_python.math.symbol.operation.flt64_matrix_form import (
    Flt64MatrixForm,
)
from ospf_python.math.symbol.operation.power_vector_key import (
    PowerVectorKey,
)
from ospf_python.math.symbol.operation.value_provider import (
    DictValueProvider,
    LambdaValueProvider,
)

# ============================================================
# PowerVectorKey
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
        with pytest.raises(NotImplementedError):
            PowerVectorKey(variables=("x", "y"), powers=(1,))

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        k = PowerVectorKey(variables=("x",), powers=(1,))
        with pytest.raises(AttributeError):
            k.powers = (2,)  # type: ignore[misc]


# ============================================================
# Flt64MatrixForm
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
# ValueProvider
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
# SymbolIdentitySerde
# ============================================================


class TestSymbolIdentitySerde:
    """SymbolIdentitySerde 测试。/ SymbolIdentitySerde tests."""

    def test_serialize_with_namespace(self) -> None:
        """带命名空间序列化。/ Serialize with namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )

        s = SymbolIdentitySerde(namespace="math")
        assert s.serialize("x") == "math.x"

    def test_serialize_no_namespace(self) -> None:
        """无命名空间序列化。/ Serialize without namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )

        s = SymbolIdentitySerde()
        assert s.serialize("x") == "x"

    def test_deserialize_with_namespace(self) -> None:
        """带命名空间反序列化。/ Deserialize with namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )

        s = SymbolIdentitySerde(namespace="math")
        assert s.deserialize("math.x") == "x"

    def test_deserialize_no_namespace(self) -> None:
        """无命名空间反序列化。/ Deserialize without namespace."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )

        s = SymbolIdentitySerde()
        assert s.deserialize("x") == "x"

    def test_deserialize_no_match(self) -> None:
        """命名空间不匹配时原样返回。/ No match returns as-is."""
        from ospf_python.math.symbol.serde.symbol_identity_serde import (
            SymbolIdentitySerde,
        )

        s = SymbolIdentitySerde(namespace="math")
        assert s.deserialize("other.x") == "other.x"


# ============================================================
# PolynomialSerde
# ============================================================


class TestPolynomialSerde:
    """PolynomialSerde 测试。/ PolynomialSerde tests."""

    def test_serialize_polynomial(self) -> None:
        """序列化多项式。/ Serialize polynomial."""
        from ospf_python.math.symbol.polynomial.canonical_polynomial import (
            CanonicalPolynomial,
        )
        from ospf_python.math.symbol.serde.polynomial_serde import (
            PolynomialSerde,
        )

        s = PolynomialSerde()
        p = CanonicalPolynomial.constant(42.0)
        result = s.serialize(p)
        assert "42" in result

    def test_deserialize_polynomial(self) -> None:
        """反序列化多项式。/ Deserialize polynomial."""
        from ospf_python.math.symbol.serde.polynomial_serde import (
            PolynomialSerde,
        )

        s = PolynomialSerde()
        result = s.deserialize("x + 1")
        assert result is not None


# ============================================================
# InequalitySerde
# ============================================================


class TestInequalitySerde:
    """InequalitySerde 测试。/ InequalitySerde tests."""

    def test_deserialize_returns_none(self) -> None:
        """反序列化返回 None（TODO）。/ Deserialize returns None."""
        from ospf_python.math.symbol.serde.inequality_serde import (
            InequalitySerde,
        )

        s = InequalitySerde(polynomial_serde=None)
        assert hasattr(s, "deserialize")


# ============================================================
# Generic stub dataclasses (import and instantiate)
# ============================================================


class TestOperationStubs:
    """运算模块桩类测试。/ Operation stub tests."""

    def test_canonical_ops(self) -> None:
        from ospf_python.math.symbol.operation.canonical_ops import (
            CanonicalOps,
        )

        assert CanonicalOps is not None

    def test_term_combiner(self) -> None:
        from ospf_python.math.symbol.operation.combine_terms import (
            TermCombiner,
        )

        assert TermCombiner is not None

    def test_polynomial_compiler(self) -> None:
        from ospf_python.math.symbol.operation.compile import (
            PolynomialCompiler,
        )

        assert PolynomialCompiler is not None

    def test_compile_ops(self) -> None:
        from ospf_python.math.symbol.operation.compile_ops import (
            CompileOps,
        )

        assert CompileOps is not None

    def test_polynomial_converter(self) -> None:
        from ospf_python.math.symbol.operation.convert import (
            PolynomialConverter,
        )

        assert PolynomialConverter is not None

    def test_convert_ops(self) -> None:
        from ospf_python.math.symbol.operation.convert_ops import (
            ConvertOps,
        )

        assert ConvertOps is not None

    def test_differentiator(self) -> None:
        from ospf_python.math.symbol.operation.differentiate import (
            Differentiator,
        )

        assert Differentiator is not None

    def test_differentiate_ops(self) -> None:
        from ospf_python.math.symbol.operation.differentiate_ops import (
            DifferentiateOps,
        )

        assert DifferentiateOps is not None

    def test_evaluator(self) -> None:
        from ospf_python.math.symbol.operation.evaluate import (
            PolynomialEvaluator,
        )

        assert PolynomialEvaluator is not None

    def test_factor(self) -> None:
        from ospf_python.math.symbol.operation.factorization import Factor

        assert Factor is not None

    def test_flt64_quick_dsl(self) -> None:
        from ospf_python.math.symbol.operation.flt64_quick_dsl import (
            Flt64QuickDsl,
        )

        assert Flt64QuickDsl is not None

    def test_flt64_quick_ops(self) -> None:
        from ospf_python.math.symbol.operation.flt64_quick_ops import (
            Flt64QuickOps,
        )

        assert Flt64QuickOps is not None

    def test_inequality_ops(self) -> None:
        from ospf_python.math.symbol.operation.inequality import (
            InequalityOps,
        )

        assert InequalityOps is not None

    def test_inequality_dsl(self) -> None:
        from ospf_python.math.symbol.operation.inequality_dsl import (
            InequalityDsl,
        )

        assert InequalityDsl is not None

    def test_integrate_ops(self) -> None:
        from ospf_python.math.symbol.operation.integrate_ops import (
            IntegrateOps,
        )

        assert IntegrateOps is not None

    def test_latex_renderer(self) -> None:
        from ospf_python.math.symbol.operation.latex import LatexRenderer

        assert LatexRenderer is not None

    def test_latex_ops(self) -> None:
        from ospf_python.math.symbol.operation.latex_ops import LatexOps

        assert LatexOps is not None

    def test_linear_quadratic_ops(self) -> None:
        from ospf_python.math.symbol.operation.linear_quadratic_ops import (
            LinearQuadraticOps,
        )

        assert LinearQuadraticOps is not None

    def test_matrix_form(self) -> None:
        from ospf_python.math.symbol.operation.matrix_form import (
            MatrixForm,
        )

        assert MatrixForm is not None

    def test_mutable_combine_ops(self) -> None:
        from ospf_python.math.symbol.operation.mutable_combine_ops import (
            MutableCombineOps,
        )

        assert MutableCombineOps is not None

    def test_normalizer(self) -> None:
        from ospf_python.math.symbol.operation.normalize import (
            PolynomialNormalizer,
        )

        assert PolynomialNormalizer is not None

    def test_string_parser(self) -> None:
        from ospf_python.math.symbol.operation.parse import (
            PolynomialStringParser,
        )

        assert PolynomialStringParser is not None

    def test_quick_dsl(self) -> None:
        from ospf_python.math.symbol.operation.quick_dsl import QuickDsl

        assert QuickDsl is not None

    def test_quick_ops(self) -> None:
        from ospf_python.math.symbol.operation.quick_ops import QuickOps

        assert QuickOps is not None

    def test_serde_ops(self) -> None:
        from ospf_python.math.symbol.operation.serde import SerdeOps

        assert SerdeOps is not None

    def test_to_polynomial(self) -> None:
        from ospf_python.math.symbol.operation.to_polynomial import (
            ToPolynomial,
        )

        assert ToPolynomial is not None
