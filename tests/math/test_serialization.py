"""序列化工具测试。

Serialization utility tests.

测试 serialize_number 和 deserialize_number 函数。
Tests serialize_number and deserialize_number functions.
"""

from __future__ import annotations

from fractions import Fraction

from ospf_python.math.serialization import (
    deserialize_number,
    serialize_number,
)

# ── serialize_number ────────────────────────────────────────────


class TestSerializeNumber:
    """数值序列化测试。"""

    def test_serialize_int(self) -> None:
        """序列化整数。/ Serialize int."""
        assert serialize_number(42) == "42"

    def test_serialize_float(self) -> None:
        """序列化浮点数。/ Serialize float."""
        result = serialize_number(3.14)
        assert "3.14" in result

    def test_serialize_fraction(self) -> None:
        """序列化分数。/ Serialize fraction."""
        assert serialize_number(Fraction(3, 4)) == "3/4"

    def test_serialize_negative_int(self) -> None:
        """序列化负整数。/ Serialize negative int."""
        assert serialize_number(-5) == "-5"

    def test_serialize_zero(self) -> None:
        """序列化零。/ Serialize zero."""
        assert serialize_number(0) == "0"


# ── deserialize_number ──────────────────────────────────────────


class TestDeserializeNumber:
    """数值反序列化测试。"""

    def test_deserialize_int(self) -> None:
        """反序列化整数。/ Deserialize int."""
        assert deserialize_number("42") == 42
        assert isinstance(deserialize_number("42"), int)

    def test_deserialize_float(self) -> None:
        """反序列化浮点数。/ Deserialize float."""
        result = deserialize_number("3.14")
        assert abs(result - 3.14) < 1e-10
        assert isinstance(result, float)

    def test_deserialize_fraction(self) -> None:
        """反序列化分数。/ Deserialize fraction."""
        result = deserialize_number("3/4")
        assert isinstance(result, Fraction)
        assert result == Fraction(3, 4)

    def test_deserialize_negative_int(self) -> None:
        """反序列化负整数。/ Deserialize negative int."""
        assert deserialize_number("-5") == -5

    def test_deserialize_scientific(self) -> None:
        """反序列化科学计数法。/ Deserialize scientific notation."""
        result = deserialize_number("1e3")
        assert isinstance(result, float)
        assert abs(result - 1000.0) < 1e-10


# ── Round-trip ──────────────────────────────────────────────────


class TestRoundTrip:
    """往返序列化测试。"""

    def test_int_round_trip(self) -> None:
        """整数往返。/ Int round trip."""
        original = 42
        s = serialize_number(original)
        result = deserialize_number(s)
        assert result == original

    def test_fraction_round_trip(self) -> None:
        """分数往返。/ Fraction round trip."""
        original = Fraction(3, 7)
        s = serialize_number(original)
        result = deserialize_number(s)
        assert result == original
