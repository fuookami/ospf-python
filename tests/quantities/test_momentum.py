"""动量单位测试。/ Momentum unit tests.

测试动量单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for momentum units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.momentum import (
    GRAM_CENTIMETRE_PER_SECOND,
    KILOGRAM_METRE_PER_SECOND,
    NEWTON_SECOND,
    POUND_FOOT_PER_SECOND,
)


class TestMomentumToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_kg_m_per_s_to_si(self) -> None:
        """kg*m/s 到 SI。/ kg*m/s to SI."""
        assert KILOGRAM_METRE_PER_SECOND.to_si(1.0) == 1.0

    def test_newton_second_to_si(self) -> None:
        """牛顿秒到 SI。/ Newton-second to SI."""
        assert NEWTON_SECOND.to_si(1.0) == 1.0

    def test_g_cm_per_s_to_si(self) -> None:
        """g*cm/s 到 SI。/ g*cm/s to SI."""
        result = GRAM_CENTIMETRE_PER_SECOND.to_si(1.0)
        assert result == pytest.approx(1e-5)

    def test_lb_ft_per_s_to_si(self) -> None:
        """lb*ft/s 到 SI。/ lb*ft/s to SI."""
        result = POUND_FOOT_PER_SECOND.to_si(1.0)
        assert result == pytest.approx(0.13825, rel=1e-3)


class TestMomentumRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 10.0
        si = KILOGRAM_METRE_PER_SECOND.to_si(original)
        back = KILOGRAM_METRE_PER_SECOND.from_si(si)
        assert back == pytest.approx(original)
