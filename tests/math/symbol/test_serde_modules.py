"""符号序列化模块测试。

Tests for symbol serde modules: PolynomialSerde,
InequalitySerde, and JsonSerde.
"""

from __future__ import annotations

from ospf_python.math.symbol.inequality.canonical_inequality import (
    CanonicalInequality,
)
from ospf_python.math.symbol.inequality.comparison import (
    Comparison,
)
from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.serde.inequality_serde import (
    InequalitySerde,
)
from ospf_python.math.symbol.serde.json_serde import (
    JsonSerde,
)
from ospf_python.math.symbol.serde.polynomial_serde import (
    PolynomialSerde,
)
from ospf_python.math.symbol.symbol import Symbol

# ============================================================
# PolynomialSerde
# ============================================================


class TestPolynomialSerde:
    """PolynomialSerde 测试。/ PolynomialSerde tests."""

    def setup_method(self) -> None:
        """初始化序列化器。/ Initialize serde."""
        self.serde = PolynomialSerde()

    def test_serialize_zero(self) -> None:
        """序列化零多项式。/ Serialize zero."""
        poly = CanonicalPolynomial.zero()
        assert self.serde.serialize(poly) == "0"

    def test_serialize_constant(self) -> None:
        """序列化常数多项式。/ Serialize constant."""
        poly = CanonicalPolynomial.constant(5.0)
        assert self.serde.serialize(poly) == "5"

    def test_serialize_single_variable(self) -> None:
        """序列化单变量。/ Serialize single variable."""
        x = Symbol.create("x")
        poly = CanonicalPolynomial.of(
            CanonicalMonomial.single(x),
        )
        result = self.serde.serialize(poly)
        assert "x" in result

    def test_serialize_coefficient(self) -> None:
        """序列化带系数项。/ Serialize with coefficient."""
        x = Symbol.create("x")
        poly = CanonicalPolynomial.of(
            CanonicalMonomial.single(x, coefficient=3.0),
        )
        result = self.serde.serialize(poly)
        assert "3" in result
        assert "x" in result

    def test_serialize_power(self) -> None:
        """序列化幂次项。/ Serialize power term."""
        x = Symbol.create("x")
        poly = CanonicalPolynomial.of(
            CanonicalMonomial.single(x, power=2),
        )
        result = self.serde.serialize(poly)
        assert "x^2" in result

    def test_serialize_multi_term(self) -> None:
        """序列化多项目。/ Serialize multi-term."""
        x = Symbol.create("x")
        poly = CanonicalPolynomial.of(
            CanonicalMonomial.single(x, coefficient=3.0, power=2),
            CanonicalMonomial.single(x, coefficient=2.0),
            CanonicalMonomial.constant(1.0),
        )
        result = self.serde.serialize(poly)
        assert "x^2" in result
        assert "x" in result
        assert "1" in result

    def test_deserialize_constant(self) -> None:
        """反序列化常数。/ Deserialize constant."""
        poly = self.serde.deserialize("5")
        assert len(poly.terms) == 1
        assert poly.terms[0].is_constant
        assert poly.terms[0].coefficient == 5.0

    def test_deserialize_variable(self) -> None:
        """反序列化变量。/ Deserialize variable."""
        poly = self.serde.deserialize("x")
        assert len(poly.terms) == 1
        x = Symbol.create("x")
        assert x in poly.terms[0].powers

    def test_deserialize_expression(self) -> None:
        """反序列化表达式。/ Deserialize expression."""
        poly = self.serde.deserialize("3x^2 + 2x + 1")
        assert len(poly.terms) == 3

    def test_roundtrip_constant(self) -> None:
        """常数往返测试。/ Constant roundtrip."""
        original = CanonicalPolynomial.constant(42.0)
        serialized = self.serde.serialize(original)
        deserialized = self.serde.deserialize(serialized)
        assert deserialized.terms[0].coefficient == 42.0

    def test_roundtrip_expression(self) -> None:
        """表达式往返测试。/ Expression roundtrip."""
        x = Symbol.create("x")
        original = CanonicalPolynomial.of(
            CanonicalMonomial.single(x, coefficient=3.0, power=2),
            CanonicalMonomial.single(x, coefficient=2.0),
            CanonicalMonomial.constant(1.0),
        )
        serialized = self.serde.serialize(original)
        deserialized = self.serde.deserialize(serialized)
        assert len(deserialized.terms) == 3


# ============================================================
# InequalitySerde
# ============================================================


class TestInequalitySerde:
    """InequalitySerde 测试。/ InequalitySerde tests."""

    def setup_method(self) -> None:
        """初始化序列化器。/ Initialize serde."""
        self.poly_serde = PolynomialSerde()
        self.ineq_serde = InequalitySerde(
            polynomial_serde=self.poly_serde,
        )

    def test_serialize_le(self) -> None:
        """序列化 <=。/ Serialize <=."""
        x = Symbol.create("x")
        ineq = CanonicalInequality(
            left=CanonicalPolynomial.of(
                CanonicalMonomial.single(x),
            ),
            right=CanonicalPolynomial.constant(5.0),
            comparison=Comparison.LE,
        )
        result = self.ineq_serde.serialize(ineq)
        assert "<=" in result
        assert "x" in result
        assert "5" in result

    def test_serialize_ge(self) -> None:
        """序列化 >=。/ Serialize >=."""
        x = Symbol.create("x")
        ineq = CanonicalInequality(
            left=CanonicalPolynomial.of(
                CanonicalMonomial.single(x, coefficient=2.0),
            ),
            right=CanonicalPolynomial.constant(10.0),
            comparison=Comparison.GE,
        )
        result = self.ineq_serde.serialize(ineq)
        assert ">=" in result

    def test_serialize_lt(self) -> None:
        """序列化 <。/ Serialize <."""
        x = Symbol.create("x")
        ineq = CanonicalInequality(
            left=CanonicalPolynomial.of(
                CanonicalMonomial.single(x),
            ),
            right=CanonicalPolynomial.constant(5.0),
            comparison=Comparison.LT,
        )
        result = self.ineq_serde.serialize(ineq)
        assert "<" in result
        assert "<=" not in result

    def test_deserialize_le(self) -> None:
        """反序列化 <=。/ Deserialize <=."""
        ineq = self.ineq_serde.deserialize("x <= 5")
        assert ineq.comparison == Comparison.LE

    def test_deserialize_ge(self) -> None:
        """反序列化 >=。/ Deserialize >=."""
        ineq = self.ineq_serde.deserialize("x >= 5")
        assert ineq.comparison == Comparison.GE

    def test_deserialize_lt(self) -> None:
        """反序列化 <。/ Deserialize <."""
        ineq = self.ineq_serde.deserialize("x < 5")
        assert ineq.comparison == Comparison.LT

    def test_deserialize_gt(self) -> None:
        """反序列化 >。/ Deserialize >."""
        ineq = self.ineq_serde.deserialize("x > 5")
        assert ineq.comparison == Comparison.GT

    def test_deserialize_eq(self) -> None:
        """反序列化 ==。/ Deserialize ==."""
        ineq = self.ineq_serde.deserialize("x == 5")
        assert ineq.comparison == Comparison.EQ

    def test_deserialize_ne(self) -> None:
        """反序列化 !=。/ Deserialize !=."""
        ineq = self.ineq_serde.deserialize("x != 5")
        assert ineq.comparison == Comparison.NE

    def test_roundtrip(self) -> None:
        """往返测试。/ Roundtrip."""
        x = Symbol.create("x")
        original = CanonicalInequality(
            left=CanonicalPolynomial.of(
                CanonicalMonomial.single(x, coefficient=2.0),
            ),
            right=CanonicalPolynomial.constant(10.0),
            comparison=Comparison.LE,
        )
        serialized = self.ineq_serde.serialize(original)
        deserialized = self.ineq_serde.deserialize(serialized)
        assert deserialized.comparison == Comparison.LE


# ============================================================
# JsonSerde
# ============================================================


class TestJsonSerde:
    """JsonSerde 测试。/ JsonSerde tests."""

    def test_to_json_dict(self) -> None:
        """序列化字典。/ Serialize dict."""
        result = JsonSerde.to_json({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result

    def test_to_json_list(self) -> None:
        """序列化列表。/ Serialize list."""
        result = JsonSerde.to_json([1, 2, 3])
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_to_json_nested(self) -> None:
        """序列化嵌套结构。/ Serialize nested."""
        obj = {"a": [1, 2], "b": {"c": 3}}
        result = JsonSerde.to_json(obj)
        assert '"a"' in result
        assert '"b"' in result

    def test_from_json_dict(self) -> None:
        """反序列化字典。/ Deserialize dict."""
        result = JsonSerde.from_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_from_json_list(self) -> None:
        """反序列化列表。/ Deserialize list."""
        result = JsonSerde.from_json("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_roundtrip(self) -> None:
        """往返测试。/ Roundtrip."""
        original = {"x": 1, "y": [2, 3]}
        serialized = JsonSerde.to_json(original)
        deserialized = JsonSerde.from_json(serialized)
        assert deserialized == original

    def test_to_json_enum(self) -> None:
        """序列化枚举。/ Serialize enum."""
        result = JsonSerde.to_json(Comparison.LE)
        assert '"<="' in result

    def test_to_json_dataclass(self) -> None:
        """序列化 dataclass。/ Serialize dataclass."""
        from dataclasses import dataclass

        @dataclass
        class Point:
            x: int
            y: int

        result = JsonSerde.to_json(Point(x=1, y=2))
        assert '"x"' in result
        assert '"y"' in result
