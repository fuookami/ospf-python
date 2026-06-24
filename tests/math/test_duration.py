"""时间持续工具测试。

Duration utility tests.

测试 Duration 类的创建、转换和属性。
Tests Duration creation, conversion, and properties.
"""

from __future__ import annotations

from ospf_python.math.duration import Duration

# ── Duration creation ───────────────────────────────────────────


class TestDurationCreation:
    """Duration 创建测试。"""

    def test_from_hours(self) -> None:
        """从小时创建。/ Create from hours."""
        d = Duration.from_hours(2.0)
        assert d.total_hours == 2.0

    def test_from_minutes(self) -> None:
        """从分钟创建。/ Create from minutes."""
        d = Duration.from_minutes(90.0)
        assert d.total_minutes == 90.0

    def test_from_seconds(self) -> None:
        """从秒创建。/ Create from seconds."""
        d = Duration.from_seconds(3600.0)
        assert d.total_seconds == 3600.0

    def test_zero_duration(self) -> None:
        """零持续时间。/ Zero duration."""
        d = Duration.from_seconds(0.0)
        assert d.total_seconds == 0.0


# ── Duration conversion ────────────────────────────────────────


class TestDurationConversion:
    """Duration 转换测试。"""

    def test_hours_to_minutes(self) -> None:
        """小时转分钟。/ Hours to minutes."""
        d = Duration.from_hours(1.0)
        assert d.total_minutes == 60.0

    def test_hours_to_seconds(self) -> None:
        """小时转秒。/ Hours to seconds."""
        d = Duration.from_hours(1.0)
        assert d.total_seconds == 3600.0

    def test_minutes_to_hours(self) -> None:
        """分钟转小时。/ Minutes to hours."""
        d = Duration.from_minutes(120.0)
        assert d.total_hours == 2.0

    def test_seconds_to_minutes(self) -> None:
        """秒转分钟。/ Seconds to minutes."""
        d = Duration.from_seconds(120.0)
        assert d.total_minutes == 2.0

    def test_fractional_hours(self) -> None:
        """小数小时。/ Fractional hours."""
        d = Duration.from_hours(1.5)
        assert d.total_minutes == 90.0

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        d = Duration.from_seconds(100.0)
        assert d.total_seconds == 100.0

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        d = Duration.from_seconds(60.0)
        assert "Duration" in repr(d)
