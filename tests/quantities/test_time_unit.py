"""时间单位测试。/ Time unit tests.

测试时间单位的 SI 转换和往返精度。
Tests SI conversion and round-trip precision for time units.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.unit.physical_unit import PhysicalUnit
from ospf_python.quantities.unit.time_unit import (
    DAY,
    HOUR,
    MILLISECOND,
    MINUTE,
    SECOND,
)


class TestTimeToSI:
    """SI 转换测试 / SI conversion tests."""

    def test_second_to_si(self) -> None:
        """秒到 SI。/ Second to SI."""
        assert SECOND.to_si(1.0) == 1.0

    def test_millisecond_to_si(self) -> None:
        """毫秒到 SI。/ Millisecond to SI."""
        assert MILLISECOND.to_si(1.0) == pytest.approx(0.001)

    def test_minute_to_si(self) -> None:
        """分钟到 SI。/ Minute to SI."""
        assert MINUTE.to_si(1.0) == pytest.approx(60.0)

    def test_hour_to_si(self) -> None:
        """小时到 SI。/ Hour to SI."""
        assert HOUR.to_si(1.0) == pytest.approx(3600.0)

    def test_day_to_si(self) -> None:
        """天到 SI。/ Day to SI."""
        assert DAY.to_si(1.0) == pytest.approx(86400.0)


class TestTimeRoundTrip:
    """往返转换测试 / Round-trip tests."""

    def test_protocol(self) -> None:
        """满足 PhysicalUnit 协议。/ Satisfies protocol."""
        assert isinstance(SECOND, PhysicalUnit)
        assert isinstance(HOUR, PhysicalUnit)
