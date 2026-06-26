"""Task aggregation model.

任务聚合模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

from .task_priority import TaskPriority
from .task_status import TaskStatus

if TYPE_CHECKING:
    from .flight_task import FlightTask


@dataclass(frozen=True)
class TaskAggregation:
    """Aggregated view of flight tasks grouped by various dimensions.

    按不同维度分组的航班任务聚合视图。
    """

    tasks: tuple[FlightTask, ...] = ()
    """All flight tasks in the aggregation.

    聚合中的所有航班任务。
    """

    by_status: dict[TaskStatus, tuple[FlightTask, ...]] = field(default_factory=dict)
    """Tasks grouped by status.

    按状态分组的任务。
    """

    by_priority: dict[TaskPriority, tuple[FlightTask, ...]] = field(
        default_factory=dict
    )
    """Tasks grouped by priority.

    按优先级分组的任务。
    """

    @property
    def total_count(self) -> int:
        """Total number of tasks.

        任务总数。
        """
        return len(self.tasks)

    @property
    def active_count(self) -> int:
        """Number of active (scheduled, in-progress, delayed) tasks.

        活跃任务数量（已计划、进行中、已延迟）。
        """
        return sum(1 for t in self.tasks if t.status.is_active)

    @property
    def completed_count(self) -> int:
        """Number of completed tasks.

        已完成任务数量。
        """
        status_tasks = self.by_status.get(TaskStatus.COMPLETED, ())
        return len(status_tasks)

    @property
    def critical_count(self) -> int:
        """Number of critical priority tasks.

        关键优先级任务数量。
        """
        priority_tasks = self.by_priority.get(TaskPriority.CRITICAL, ())
        return len(priority_tasks)

    @property
    def completion_rate(self) -> float:
        """Task completion rate (0.0 to 1.0).

        任务完成率（0.0 到 1.0）。
        """
        if self.total_count == 0:
            return 0.0
        return self.completed_count / self.total_count

    @classmethod
    def from_tasks(
        cls,
        tasks: Sequence[FlightTask],
    ) -> TaskAggregation:
        """Build aggregation from a sequence of tasks.

        从任务序列构建聚合。

        Args:
            tasks: Sequence of flight tasks to aggregate.

        Returns:
            New TaskAggregation grouped by status and priority.
        """
        task_tuple = tuple(tasks)
        by_status: dict[TaskStatus, list[FlightTask]] = {}
        by_priority: dict[TaskPriority, list[FlightTask]] = {}

        for task in task_tuple:
            by_status.setdefault(task.status, []).append(task)
            by_priority.setdefault(task.priority, []).append(task)

        return cls(
            tasks=task_tuple,
            by_status={k: tuple(v) for k, v in by_status.items()},
            by_priority={k: tuple(v) for k, v in by_priority.items()},
        )
