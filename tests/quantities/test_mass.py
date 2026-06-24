"""质量单位测试。/ Mass unit tests.

测试质量单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for mass units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.mass import (
    GRAM,
    KILOGRAM,
    MILLIGRAM,
    OUNCE,
    POUND,
)
from ospf_python.quantities.unit.physical_unit import PhysicalUnit


class TestMassToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_kilogram_to_si(self) -> None:
        """千克到 SI。/ Kilogram to SI."""
        assert KILOGRAM.to_si(1.0) == 1.0

    def test_gram_to_si(self) -> None:
        """克到 SI。/ Gram to SI."""
        assert GRAM.to_si(1.0) == 0.001

    def test_milligram_to_si(self) -> None:
        """毫克到 SI。/ Milligram to SI."""
        assert MILLIGRAM.to_si(1.0) == pytest.approx(1e-6)

    def test_pound_to_si(self) -> None:
        """磅到 SI。/ Pound to SI."""
        result = POUND.to_si(1.0)
        assert result == pytest.approx(0.45359237, rel=1e-6)

    def test_ounce_to_si(self) -> None:
        """盎司到 SI。/ Ounce to SI."""
        result = OUNCE.to_si(1.0)
        assert result == pytest.approx(0.0283495, rel=1e-4)


class TestMassRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_mass_roundtrip(self) -> None:
        """质量往返转换。/ Mass roundtrip."""
        original = 5.5
        si = POUND.to_si(original)
        back = POUND.from_si(si)
        assert back == pytest.approx(original)

    def test_protocol(self) -> None:
        """满足 PhysicalUnit 协议。/ Satisfies protocol."""
        assert isinstance(KILOGRAM, PhysicalUnit)
        assert isinstance(GRAM, PhysicalUnit)
