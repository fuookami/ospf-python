"""资源模型 / Resource model.

甘特调度中的资源实体，表示可用于执行任务的生产资源。
Resource entity in gantt scheduling, representing a production
resource available for task execution.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_type import (
    ResourceType,
)


@dataclass(frozen=True)
class Resource:
    """资源 / Resource.

    表示一个可调度的生产资源，包含标识、名称、容量、类型和可用时间窗口。
    Represents a schedulable production resource with identity, name,
    capacity, type, and availability windows.

    Attributes:
        resource_key: 资源唯一标识 / Unique resource identifier.
        name: 资源名称 / Resource display name.
        capacity: 资源总容量 / Total resource capacity.
        resource_type: 资源类型 / Resource type classification.
        availability: 可用时间窗口列表，每项为 (start, end) /
            Availability window list, each item is (start, end).
    """

    resource_key: str
    name: str
    capacity: float
    resource_type: ResourceType = ResourceType.MACHINE
    availability: tuple[tuple[float, float], ...] = ()

    def is_available_at(self, time_point: float) -> bool:
        """检查资源在指定时刻是否可用。

        Check whether the resource is available at the given time point.

        Args:
            time_point: 待检查的时间点。/ Time point to check.

        Returns:
            若资源在该时刻可用则返回 True；无可用窗口时默认可用。
            True if available at that point; defaults to True when
            no availability windows are defined.
        """
        if not self.availability:
            return True
        return any(start <= time_point <= end for start, end in self.availability)

    def available_during(
        self,
        *,
        start: float,
        end: float,
    ) -> bool:
        """检查资源在整个时间区间内是否可用。

        Check whether the resource is available throughout the
        entire given interval.

        Args:
            start: 区间起始时间。/ Interval start time.
            end: 区间结束时间。/ Interval end time.

        Returns:
            若资源在整个区间内可用则返回 True。
            True if the resource is available for the full interval.
        """
        if not self.availability:
            return True
        return any(
            w_start <= start and end <= w_end for w_start, w_end in self.availability
        )

    def effective_capacity_during(
        self,
        *,
        start: float,
        end: float,
    ) -> float:
        """计算指定区间内的有效容量。

        Calculate the effective capacity within the given interval.
        Returns full capacity if the resource is available for the
        entire interval, otherwise returns 0.0.

        Args:
            start: 区间起始时间。/ Interval start time.
            end: 区间结束时间。/ Interval end time.

        Returns:
            有效容量值。/ Effective capacity value.
        """
        if self.available_during(start=start, end=end):
            return self.capacity
        return 0.0
