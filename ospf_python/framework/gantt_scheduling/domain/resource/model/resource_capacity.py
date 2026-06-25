"""资源容量 / Resource capacity.

描述资源在特定时间窗口内的可用容量。
Describes the available capacity of a resource within a
specific time window.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceCapacity:
    """资源容量 / Resource capacity.

    表示某个资源在指定时间窗口内的容量上限，用于约束模型中
    的容量限制注册。
    Represents the capacity upper bound of a resource within a
    specified time window, used for capacity limit registration
    in the constraint model.

    Attributes:
        resource_key: 资源标识 / Resource identifier.
        time_window_start: 时间窗口起始 / Time window start.
        time_window_end: 时间窗口结束 / Time window end.
        max_capacity: 最大容量 / Maximum capacity.
        used_capacity: 已使用容量 / Already used capacity.
    """

    resource_key: str
    time_window_start: float
    time_window_end: float
    max_capacity: float
    used_capacity: float = 0.0

    @property
    def remaining_capacity(self) -> float:
        """剩余可用容量 / Remaining available capacity."""
        return max(0.0, self.max_capacity - self.used_capacity)

    @property
    def utilization_ratio(self) -> float:
        """容量利用率 / Capacity utilization ratio.

        Returns:
            0.0 到 1.0 之间的比值；最大容量为零时返回 0.0。
            A ratio between 0.0 and 1.0; returns 0.0 when
            max_capacity is zero.
        """
        if self.max_capacity <= 0.0:
            return 0.0
        return min(1.0, self.used_capacity / self.max_capacity)

    def can_accommodate(self, demand: float) -> bool:
        """检查是否能容纳额外需求。

        Check whether the capacity can accommodate additional demand.

        Args:
            demand: 额外需求量。/ Additional demand amount.

        Returns:
            若剩余容量足够则返回 True。
            True if remaining capacity is sufficient.
        """
        return demand <= self.remaining_capacity

    def with_usage(self, additional: float) -> ResourceCapacity:
        """创建增加使用量后的副本。

        Create a copy with additional usage recorded.

        Args:
            additional: 新增使用量。/ Additional usage amount.

        Returns:
            使用量更新后的 ResourceCapacity 副本。
            A new ResourceCapacity with updated used_capacity.
        """
        return ResourceCapacity(
            resource_key=self.resource_key,
            time_window_start=self.time_window_start,
            time_window_end=self.time_window_end,
            max_capacity=self.max_capacity,
            used_capacity=self.used_capacity + additional,
        )
