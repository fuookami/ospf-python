"""资源可用性 / Resource availability.

管理资源在时间轴上的可用性窗口和空闲时段计算。
Manages resource availability windows on the timeline
and free-slot computation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
        Resource,
    )


@dataclass(frozen=True)
class ResourceAvailability:
    """资源可用性 / Resource availability.

    封装资源的可用时间窗口，提供空闲时段查询和占用检测。
    Wraps a resource's availability windows, providing free-slot
    queries and occupancy checks.

    Attributes:
        resource: 关联资源 / Associated resource.
        occupied_windows: 已占用时间窗口列表 /
            List of occupied time windows as (start, end).
    """

    resource: Resource
    occupied_windows: tuple[tuple[float, float], ...] = ()

    @property
    def resource_key(self) -> str:
        """资源标识 / Resource identifier."""
        return self.resource.resource_key

    def is_free_at(self, time_point: float) -> bool:
        """检查指定时刻是否空闲。

        Check whether the resource is free at the given time point.

        Args:
            time_point: 待检查的时间点。/ Time point to check.

        Returns:
            若资源在该时刻可用且未被占用则返回 True。
            True if the resource is available and not occupied.
        """
        if not self.resource.is_available_at(time_point):
            return False
        return not any(s <= time_point <= e for s, e in self.occupied_windows)

    def free_slots_within(
        self,
        *,
        start: float,
        end: float,
    ) -> tuple[tuple[float, float], ...]:
        """计算区间内的空闲时段。

        Compute free slots within the given interval.

        Args:
            start: 区间起始。/ Interval start.
            end: 区间结束。/ Interval end.

        Returns:
            空闲时段元组，每项为 (slot_start, slot_end)。
            Tuple of free slots, each as (slot_start, slot_end).
        """
        if not self.resource.available_during(start=start, end=end):
            return ()

        # 按起始时间排序已占用窗口 / Sort occupied windows by start
        sorted_occ = sorted(
            (
                (max(s, start), min(e, end))
                for s, e in self.occupied_windows
                if s < end and e > start
            ),
        )

        # 从 start 开始逐步切割空闲段 / Cut free segments
        slots: list[tuple[float, float]] = []
        cursor = start
        for occ_start, occ_end in sorted_occ:
            if cursor < occ_start:
                slots.append((cursor, occ_start))
            cursor = max(cursor, occ_end)
        if cursor < end:
            slots.append((cursor, end))

        return tuple(slots)

    def with_occupation(
        self,
        *,
        start: float,
        end: float,
    ) -> ResourceAvailability:
        """创建添加占用后的副本。

        Create a copy with an additional occupied window.

        Args:
            start: 占用起始。/ Occupation start.
            end: 占用结束。/ Occupation end.

        Returns:
            包含新占用窗口的 ResourceAvailability 副本。
            A new ResourceAvailability with the occupation added.
        """
        return ResourceAvailability(
            resource=self.resource,
            occupied_windows=self.occupied_windows + ((start, end),),
        )

    @property
    def total_occupied_duration(self) -> float:
        """总占用时长 / Total occupied duration."""
        return sum(e - s for s, e in self.occupied_windows)
