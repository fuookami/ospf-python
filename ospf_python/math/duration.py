"""时间持续工具。

Duration utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Duration:
    """时间持续封装。

    Duration wrapper around timedelta.

    Attributes:
        delta: 底层 timedelta 对象。/ Underlying timedelta.
    """

    delta: timedelta

    @staticmethod
    def from_hours(hours: float) -> Duration:
        """从小时创建持续时间。

        Create duration from hours.

        Args:
            hours: 小时数。/ Number of hours.

        Returns:
            对应的 Duration 实例。/ Corresponding Duration.
        """
        return Duration(delta=timedelta(hours=hours))

    @staticmethod
    def from_minutes(minutes: float) -> Duration:
        """从分钟创建持续时间。

        Create duration from minutes.

        Args:
            minutes: 分钟数。/ Number of minutes.

        Returns:
            对应的 Duration 实例。/ Corresponding Duration.
        """
        return Duration(delta=timedelta(minutes=minutes))

    @staticmethod
    def from_seconds(seconds: float) -> Duration:
        """从秒创建持续时间。

        Create duration from seconds.

        Args:
            seconds: 秒数。/ Number of seconds.

        Returns:
            对应的 Duration 实例。/ Corresponding Duration.
        """
        return Duration(delta=timedelta(seconds=seconds))

    @property
    def total_hours(self) -> float:
        """获取总小时数。/ Get total hours."""
        return self.delta.total_seconds() / 3600

    @property
    def total_minutes(self) -> float:
        """获取总分钟数。/ Get total minutes."""
        return self.delta.total_seconds() / 60

    @property
    def total_seconds(self) -> float:
        """获取总秒数。/ Get total seconds."""
        return self.delta.total_seconds()
