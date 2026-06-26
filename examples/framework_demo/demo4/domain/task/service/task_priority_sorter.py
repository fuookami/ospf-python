"""Task priority sorter service.

任务优先级排序服务。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from ..model.task_priority import TaskPriority

if TYPE_CHECKING:
    from ..model.flight_task import FlightTask


class TaskPrioritySorter:
    """Sorts flight tasks by priority and other criteria.

    按优先级和其他标准对航班任务排序。
    """

    def sort_by_priority(
        self,
        tasks: Sequence[FlightTask],
    ) -> Sequence[FlightTask]:
        """Sort tasks by priority (critical first).

        按优先级排序任务（关键任务优先）。

        Args:
            tasks: Tasks to sort.

        Returns:
            Tasks sorted by priority then departure time.
        """
        return tuple(
            sorted(
                tasks,
                key=lambda t: (
                    t.priority.value,
                    t.departure_time,
                ),
            )
        )

    def sort_by_urgency(
        self,
        tasks: Sequence[FlightTask],
    ) -> Sequence[FlightTask]:
        """Sort tasks by urgency (earliest departure first).

        按紧急程度排序任务（最早出发优先）。

        Args:
            tasks: Tasks to sort.

        Returns:
            Tasks sorted by departure time.
        """
        return tuple(
            sorted(
                tasks,
                key=lambda t: t.departure_time,
            )
        )

    def get_critical_tasks(
        self,
        tasks: Sequence[FlightTask],
    ) -> Sequence[FlightTask]:
        """Filter and return only critical priority tasks.

        筛选并返回仅关键优先级的任务。

        Args:
            tasks: Tasks to filter.

        Returns:
            Only tasks with CRITICAL priority.
        """
        return tuple(t for t in tasks if t.priority == TaskPriority.CRITICAL)

    def get_active_tasks_sorted(
        self,
        tasks: Sequence[FlightTask],
    ) -> Sequence[FlightTask]:
        """Get active tasks sorted by priority.

        获取按优先级排序的活跃任务。

        Args:
            tasks: Tasks to filter and sort.

        Returns:
            Active tasks sorted by priority.
        """
        active = tuple(t for t in tasks if t.status.is_active)
        return self.sort_by_priority(active)

    def partition_by_priority(
        self,
        tasks: Sequence[FlightTask],
    ) -> dict[TaskPriority, list[FlightTask]]:
        """Partition tasks into priority buckets.

        将任务按优先级分桶。

        Args:
            tasks: Tasks to partition.

        Returns:
            Dictionary mapping each priority to its tasks.
        """
        buckets: dict[TaskPriority, list[FlightTask]] = {p: [] for p in TaskPriority}

        for task in tasks:
            buckets[task.priority].append(task)

        return buckets
