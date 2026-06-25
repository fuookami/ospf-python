"""资源需求 / Resource demand.

描述任务对资源的容量需求。
Describes a task's capacity demand on a resource.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceDemand:
    """资源需求 / Resource demand.

    表示某个任务在指定时间窗口内对特定资源的容量需求量。
    Represents a task's capacity demand on a specific resource
    within a given time window.

    Attributes:
        resource_key: 目标资源标识 / Target resource identifier.
        task_key: 关联任务标识 / Associated task identifier.
        time_window_start: 需求时间窗口起始 / Demand window start.
        time_window_end: 需求时间窗口结束 / Demand window end.
        demand_amount: 需求量 / Demand amount.
        is_mandatory: 是否为刚性需求 / Whether demand is mandatory.
    """

    resource_key: str
    task_key: str
    time_window_start: float
    time_window_end: float
    demand_amount: float
    is_mandatory: bool = True

    @property
    def duration(self) -> float:
        """需求持续时间 / Demand duration."""
        return self.time_window_end - self.time_window_start

    def overlaps_with(self, other: ResourceDemand) -> bool:
        """检查与另一个需求是否存在时间重叠。

        Check whether this demand overlaps in time with another.

        Args:
            other: 另一个资源需求。/ Another resource demand.

        Returns:
            若两者时间窗口有交集且属于同一资源则返回 True。
            True if both time windows intersect and share the
            same resource.
        """
        if self.resource_key != other.resource_key:
            return False
        return (
            self.time_window_start < other.time_window_end
            and other.time_window_start < self.time_window_end
        )

    def with_amount(self, new_amount: float) -> ResourceDemand:
        """创建需求量修改后的副本。

        Create a copy with a modified demand amount.

        Args:
            new_amount: 新的需求量。/ New demand amount.

        Returns:
            需求量更新后的 ResourceDemand 副本。
            A new ResourceDemand with updated demand_amount.
        """
        return ResourceDemand(
            resource_key=self.resource_key,
            task_key=self.task_key,
            time_window_start=self.time_window_start,
            time_window_end=self.time_window_end,
            demand_amount=new_amount,
            is_mandatory=self.is_mandatory,
        )
