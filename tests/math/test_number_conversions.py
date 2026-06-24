"""数值转换工具测试。

Number conversion utility tests.

测试 to_float、to_int、to_rational 转换函数。
Tests to_float, to_int, to_rational conversion functions.
"""

from __future__ import annotations

from fractions import Fraction

from ospf_python.math.number_conversions import (
    to_float,
    to_int,
    to_rational,
)

# ── to_float ────────────────────────────────────────────────────


class TestToFloat:
    """转浮点数测试。"""

    def test_int_to_float(self) -> None:
        """整数转浮点。/ Int to float."""
        assert to_float(42) == 42.0
        assert isinstance(to_float(42), float)

    def test_float_to_float(self) -> None:
        """浮点转浮点。/ Float to float."""
        assert to_float(3.14) == 3.14

    def test_fraction_to_float(self) -> None:
        """分数转浮点。/ Fraction to float."""
        assert abs(to_float(Fraction(1, 4)) - 0.25) < 1e-10

    def test_zero(self) -> None:
        """零值转换。/ Zero conversion."""
        assert to_float(0) == 0.0

    def test_negative(self) -> None:
        """负值转换。/ Negative conversion."""
        assert to_float(-5) == -5.0


# ── to_int ──────────────────────────────────────────────────────


class TestToInt:
    """转整数测试。"""

    def test_float_truncation(self) -> None:
        """浮点截断。/ Float truncation."""
        assert to_int(3.7) == 3

    def test_int_to_int(self) -> None:
        """整数转整数。/ Int to int."""
        assert to_int(42) == 42

    def test_fraction_to_int(self) -> None:
        """分数转整数。/ Fraction to int."""
        assert to_int(Fraction(7, 2)) == 3

    def test_negative_truncation(self) -> None:
        """负值截断。/ Negative truncation."""
        assert to_int(-3.7) == -3

    def test_zero(self) -> None:
        """零值转换。/ Zero conversion."""
        assert to_int(0.0) == 0


# ── to_rational ─────────────────────────────────────────────────


class TestToRational:
    """转有理数测试。"""

    def test_int_to_rational(self) -> None:
        """整数转有理数。/ Int to rational."""
        r = to_rational(5)
        assert isinstance(r, Fraction)
        assert r == Fraction(5, 1)

    def test_fraction_passthrough(self) -> None:
        """分数直通。/ Fraction passthrough."""
        f = Fraction(3, 7)
        assert to_rational(f) == f

    def test_float_to_rational(self) -> None:
        """浮点转有理数。/ Float to rational."""
        r = to_rational(0.5)
        assert isinstance(r, Fraction)

    def test_zero(self) -> None:
        """零值转换。/ Zero conversion."""
        r = to_rational(0)
        assert r == Fraction(0, 1)

    def test_negative(self) -> None:
        """负值转换。/ Negative conversion."""
        r = to_rational(-3)
        assert r == Fraction(-3, 1)
