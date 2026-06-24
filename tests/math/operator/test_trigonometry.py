"""三角函数运算符测试。

Trigonometric function operator tests.

测试 sin_op、cos_op、tan_op、asin_op、acos_op、atan_op。
Tests sin_op, cos_op, tan_op, asin_op, acos_op, atan_op.
"""

from __future__ import annotations

import math

from ospf_python.math.operator.trigonometry import (
    acos_op,
    asin_op,
    atan_op,
    cos_op,
    sin_op,
    tan_op,
)

# ── sin_op / cos_op / tan_op ────────────────────────────────────


class TestTrigFunctions:
    """三角函数测试。"""

    def test_sin_zero(self) -> None:
        """sin(0) = 0。/ sin(0) = 0."""
        assert math.isclose(sin_op(0.0), 0.0)

    def test_sin_pi_half(self) -> None:
        """sin(pi/2) = 1。/ sin(pi/2) = 1."""
        assert math.isclose(sin_op(math.pi / 2), 1.0)

    def test_cos_zero(self) -> None:
        """cos(0) = 1。/ cos(0) = 1."""
        assert math.isclose(cos_op(0.0), 1.0)

    def test_cos_pi(self) -> None:
        """cos(pi) = -1。/ cos(pi) = -1."""
        assert math.isclose(cos_op(math.pi), -1.0)

    def test_tan_zero(self) -> None:
        """tan(0) = 0。/ tan(0) = 0."""
        assert math.isclose(tan_op(0.0), 0.0)

    def test_tan_pi_quarter(self) -> None:
        """tan(pi/4) = 1。/ tan(pi/4) = 1."""
        assert math.isclose(tan_op(math.pi / 4), 1.0)


# ── asin_op / acos_op / atan_op ─────────────────────────────────


class TestInverseTrigFunctions:
    """反三角函数测试。"""

    def test_asin_zero(self) -> None:
        """asin(0) = 0。/ asin(0) = 0."""
        assert math.isclose(asin_op(0.0), 0.0)

    def test_asin_one(self) -> None:
        """asin(1) = pi/2。/ asin(1) = pi/2."""
        assert math.isclose(asin_op(1.0), math.pi / 2)

    def test_acos_one(self) -> None:
        """acos(1) = 0。/ acos(1) = 0."""
        assert math.isclose(acos_op(1.0), 0.0)

    def test_acos_zero(self) -> None:
        """acos(0) = pi/2。/ acos(0) = pi/2."""
        assert math.isclose(acos_op(0.0), math.pi / 2)

    def test_atan_zero(self) -> None:
        """atan(0) = 0。/ atan(0) = 0."""
        assert math.isclose(atan_op(0.0), 0.0)

    def test_atan_one(self) -> None:
        """atan(1) = pi/4。/ atan(1) = pi/4."""
        assert math.isclose(atan_op(1.0), math.pi / 4)
