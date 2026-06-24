"""压强单位测试。/ Pressure unit tests.

测试压强单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for pressure units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.pressure import (
    ATMOSPHERE,
    BAR,
    KILOPASCAL,
    MEGAPASCAL,
    PASCAL,
    PSI,
)


class TestPressureToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_pascal_to_si(self) -> None:
        """帕斯卡到 SI。/ Pascal to SI."""
        assert PASCAL.to_si(1.0) == 1.0

    def test_kilopascal_to_si(self) -> None:
        """千帕到 SI。/ Kilopascal to SI."""
        assert KILOPASCAL.to_si(1.0) == 1000.0

    def test_megapascal_to_si(self) -> None:
        """兆帕到 SI。/ Megapascal to SI."""
        assert MEGAPASCAL.to_si(1.0) == 1e6

    def test_bar_to_si(self) -> None:
        """巴到 SI。/ Bar to SI."""
        assert BAR.to_si(1.0) == pytest.approx(1e5)

    def test_atmosphere_to_si(self) -> None:
        """标准大气压到 SI。/ Atmosphere to SI."""
        assert ATMOSPHERE.to_si(1.0) == pytest.approx(101_325.0)

    def test_psi_to_si(self) -> None:
        """PSI 到 SI。/ PSI to SI."""
        result = PSI.to_si(1.0)
        assert result == pytest.approx(6894.76, rel=1e-3)


class TestPressureRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 101.325
        si = KILOPASCAL.to_si(original)
        back = KILOPASCAL.from_si(si)
        assert back == pytest.approx(original)
