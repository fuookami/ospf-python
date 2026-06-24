"""比较运算枚举测试。

Comparison operator enumeration tests.

测试 Comparison 枚举的值、属性和转换。
Tests Comparison enum values, properties, and transformations.
"""

from __future__ import annotations

from ospf_python.math.symbol.inequality.comparison import Comparison

# ── Comparison enum ─────────────────────────────────────────────


class TestComparisonEnum:
    """比较运算枚举测试。"""

    def test_values(self) -> None:
        """枚举值。/ Enum values."""
        assert Comparison.LE.value == "<="
        assert Comparison.GE.value == ">="
        assert Comparison.LT.value == "<"
        assert Comparison.GT.value == ">"
        assert Comparison.EQ.value == "=="
        assert Comparison.NE.value == "!="

    def test_symbol(self) -> None:
        """符号属性。/ Symbol property."""
        assert Comparison.LE.symbol == "<="
        assert Comparison.GT.symbol == ">"


# ── Comparison strictness ───────────────────────────────────────


class TestComparisonStrictness:
    """比较严格性测试。"""

    def test_strict_operators(self) -> None:
        """严格比较运算符。/ Strict comparison operators."""
        assert Comparison.LT.is_strict
        assert Comparison.GT.is_strict
        assert Comparison.NE.is_strict

    def test_non_strict_operators(self) -> None:
        """非严格比较运算符。/ Non-strict comparison operators."""
        assert not Comparison.LE.is_strict
        assert not Comparison.GE.is_strict
        assert not Comparison.EQ.is_strict


# ── Comparison negation ─────────────────────────────────────────


class TestComparisonNegation:
    """比较取反测试。"""

    def test_negate_le(self) -> None:
        """取反 <= 为 >。/ Negate LE to GT."""
        assert Comparison.LE.negated == Comparison.GT

    def test_negate_ge(self) -> None:
        """取反 >= 为 <。/ Negate GE to LT."""
        assert Comparison.GE.negated == Comparison.LT

    def test_negate_lt(self) -> None:
        """取反 < 为 >=。/ Negate LT to GE."""
        assert Comparison.LT.negated == Comparison.GE

    def test_negate_eq(self) -> None:
        """取反 == 为 !=。/ Negate EQ to NE."""
        assert Comparison.EQ.negated == Comparison.NE

    def test_negate_ne(self) -> None:
        """取反 != 为 ==。/ Negate NE to EQ."""
        assert Comparison.NE.negated == Comparison.EQ


# ── Comparison reversal ─────────────────────────────────────────


class TestComparisonReversal:
    """比较反转测试。"""

    def test_reverse_le(self) -> None:
        """反转 <= 为 >=。/ Reverse LE to GE."""
        assert Comparison.LE.reversed == Comparison.GE

    def test_reverse_lt(self) -> None:
        """反转 < 为 >。/ Reverse LT to GT."""
        assert Comparison.LT.reversed == Comparison.GT

    def test_reverse_eq(self) -> None:
        """反转 == 为 ==。/ Reverse EQ to EQ."""
        assert Comparison.EQ.reversed == Comparison.EQ

    def test_reverse_ne(self) -> None:
        """反转 != 为 !=。/ Reverse NE to NE."""
        assert Comparison.NE.reversed == Comparison.NE
