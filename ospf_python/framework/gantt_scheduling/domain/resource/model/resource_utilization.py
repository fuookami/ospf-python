"""资源利用率 / Resource utilization.

计算和表示资源在调度方案中的利用率指标。
Computes and represents utilization metrics of a resource
in a scheduling plan.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceUtilization:
    """资源利用率 / Resource utilization.

    记录某个资源在给定时间范围内的利用率统计，包括总容量、
    已使用容量和峰值使用量。
    Records utilization statistics of a resource over a given
    time range, including total capacity, used capacity, and
    peak usage.

    Attributes:
        resource_key: 资源标识 / Resource identifier.
        time_range_start: 统计区间起始 / Statistics range start.
        time_range_end: 统计区间结束 / Statistics range end.
        total_capacity: 总可用容量 / Total available capacity.
        used_capacity: 已使用容量 / Used capacity.
        peak_usage: 峰值使用量 / Peak usage amount.
    """

    resource_key: str
    time_range_start: float
    time_range_end: float
    total_capacity: float
    used_capacity: float
    peak_usage: float = 0.0

    @property
    def utilization_rate(self) -> float:
        """利用率 / Utilization rate.

        Returns:
            0.0 到 1.0 之间的比值；总容量为零时返回 0.0。
            A ratio between 0.0 and 1.0; returns 0.0 when
            total_capacity is zero.
        """
        if self.total_capacity <= 0.0:
            return 0.0
        return min(1.0, self.used_capacity / self.total_capacity)

    @property
    def idle_capacity(self) -> float:
        """空闲容量 / Idle capacity."""
        return max(0.0, self.total_capacity - self.used_capacity)

    @property
    def peak_utilization_rate(self) -> float:
        """峰值利用率 / Peak utilization rate.

        Returns:
            峰值使用量与总容量的比值。
            Ratio of peak usage to total capacity.
        """
        if self.total_capacity <= 0.0:
            return 0.0
        return min(1.0, self.peak_usage / self.total_capacity)

    @property
    def duration(self) -> float:
        """统计区间时长 / Statistics range duration."""
        return self.time_range_end - self.time_range_start

    def is_overloaded(self, threshold: float = 1.0) -> bool:
        """检查是否超载。

        Check whether the resource is overloaded.

        Args:
            threshold: 超载阈值，默认 1.0 / Overload threshold,
                defaults to 1.0.

        Returns:
            若利用率超过阈值则返回 True。
            True if utilization rate exceeds the threshold.
        """
        return self.utilization_rate > threshold
