"""任务调度方案定义 / Task scheduling solution definition.

封装单个任务的调度结果，包括时间安排和资源分配。
Encapsulates the scheduling result of a single task,
including time arrangement and resource assignment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskSolution:
    """任务调度方案 / Task scheduling solution.

    记录单个任务的调度执行方案，包含开始/结束时间、
    分配的资源和调度成本。
    Records the scheduling execution plan of a single task,
    including start/end times, assigned resource, and cost.

    Attributes:
        task_key: 任务唯一标识 / Unique task identifier.
        start_time: 开始时间（秒）/ Start time (seconds).
        end_time: 结束时间（秒）/ End time (seconds).
        resource_key: 分配的资源键 / Assigned resource key.
        cost: 调度成本 / Scheduling cost.
    """

    task_key: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    resource_key: str = ""
    cost: float = 0.0

    # ==================== 查询 / Queries =========================

    @property
    def duration(self) -> float:
        """获取实际持续时长 / Get actual duration.

        Returns:
            结束时间减去开始时间。
            End time minus start time.
        """
        return self.end_time - self.start_time

    @property
    def is_assigned(self) -> bool:
        """是否已分配资源 / Whether resource is assigned.

        Returns:
            分配了资源时返回 True。
            True when a resource is assigned.
        """
        return len(self.resource_key) > 0

    @property
    def is_scheduled(self) -> bool:
        """是否已调度 / Whether scheduled.

        Returns:
            有有效时间安排时返回 True。
            True when a valid time arrangement exists.
        """
        return self.end_time > self.start_time

    def is_delayed_beyond(self, deadline: float) -> bool:
        """检查是否超过截止时间 / Check if exceeds deadline.

        Args:
            deadline: 截止时间（秒）/ Deadline (seconds).

        Returns:
            结束时间超过截止时间时返回 True。
            True when end time exceeds deadline.
        """
        return self.end_time > deadline

    def overlaps_with(
        self,
        other: TaskSolution,
    ) -> bool:
        """检查与另一任务方案是否时间重叠。

        Check if time overlaps with another task solution.

        Args:
            other: 另一任务方案 / Another task solution.

        Returns:
            时间区间有重叠时返回 True。
            True when time intervals overlap.
        """
        return self.start_time < other.end_time and other.start_time < self.end_time

    def shares_resource_with(
        self,
        other: TaskSolution,
    ) -> bool:
        """检查与另一任务方案是否使用同一资源。

        Check if shares the same resource with another task.

        Args:
            other: 另一任务方案 / Another task solution.

        Returns:
            使用同一资源时返回 True。
            True when sharing the same resource.
        """
        return len(self.resource_key) > 0 and self.resource_key == other.resource_key
