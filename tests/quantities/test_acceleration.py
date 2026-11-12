"""加速度单位测试。/ Acceleration unit tests.

测试加速度单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for acceleration units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.acceleration import (
    FOOT_PER_SQ_SECOND,
    GAL,
    GRAVITY_STANDARD,
    KILOMETRE_PER_SQ_HOUR,
    METRE_PER_SQ_SECOND,
)


class TestAccelerationToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_metre_per_sq_second_to_si(self) -> None:
        """m/s^2 到 SI。/ m/s^2 to SI."""
        assert METRE_PER_SQ_SECOND.to_si(1.0) == 1.0

    def test_gravity_to_si(self) -> None:
        """重力加速度到 SI。/ Gravity to SI."""
        result = GRAVITY_STANDARD.to_si(1.0)
        assert result == pytest.approx(9.80665, rel=1e-4)

    def test_gal_to_si(self) -> None:
        """伽到 SI。/ Gal to SI."""
        assert GAL.to_si(1.0) == pytest.approx(0.01)

    def test_foot_per_sq_second_to_si(self) -> None:
        """ft/s^2 到 SI。/ ft/s^2 to SI."""
        result = FOOT_PER_SQ_SECOND.to_si(1.0)
        assert result == pytest.approx(0.3048, rel=1e-4)


class TestAccelerationRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 9.81
        si = METRE_PER_SQ_SECOND.to_si(original)
        back = METRE_PER_SQ_SECOND.from_si(si)
        assert back == pytest.approx(original)


def test_kilometre_per_sq_hour_matches_first_principles() -> None:
    """1 km/h² = 1000 m / (3600 s)² = 7.716e-05 m/s²。

    历史实现写成 1/12 960 000，漏了 km→m 的分子 1000，系数小了 1000 倍。
    The old factor 1/12_960_000 dropped the km->m numerator of 1000, making it 1000x small.
    """
    assert KILOMETRE_PER_SQ_HOUR.to_si(1.0) == pytest.approx(
        1000.0 / 3600.0**2, rel=1e-12
    )
    assert KILOMETRE_PER_SQ_HOUR.to_si(3600.0 * 3600.0 / 1000.0) == pytest.approx(
        1.0, rel=1e-12
    )
