"""电流单位测试。/ Current unit tests.

测试电流单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for current units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.current import (
    AMPERE,
    KILOAMPERE,
    MICROAMPERE,
    MILLIAMPERE,
)


class TestCurrentToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_ampere_to_si(self) -> None:
        """安培到 SI。/ Ampere to SI."""
        assert AMPERE.to_si(1.0) == 1.0

    def test_milliampere_to_si(self) -> None:
        """毫安到 SI。/ Milliampere to SI."""
        assert MILLIAMPERE.to_si(1.0) == pytest.approx(0.001)

    def test_microampere_to_si(self) -> None:
        """微安到 SI。/ Microampere to SI."""
        assert MICROAMPERE.to_si(1.0) == pytest.approx(1e-6)

    def test_kiloampere_to_si(self) -> None:
        """千安到 SI。/ Kiloampere to SI."""
        assert KILOAMPERE.to_si(1.0) == 1000.0


class TestCurrentRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_roundtrip(self) -> None:
        """往返转换。/ Roundtrip."""
        original = 5.0
        si = AMPERE.to_si(original)
        back = AMPERE.from_si(si)
        assert back == pytest.approx(original)
