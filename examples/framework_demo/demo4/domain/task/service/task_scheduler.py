"""Task scheduler service.

任务调度服务。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Sequence

from ..model.task_schedule import TaskSchedule

if TYPE_CHECKING:
    from ..model.flight_task import FlightTask


@dataclass(frozen=True)
class SchedulingResult:
    """Result of a scheduling operation.

    调度操作的结果。
    """

    schedules: tuple[TaskSchedule, ...] = ()
    """Generated schedules.

    生成的调度计划。
    """

    unscheduled_task_ids: tuple[str, ...] = ()
    """Tasks that could not be scheduled.

    无法调度的任务。
    """

    @property
    def scheduled_count(self) -> int:
        """Number of successfully scheduled tasks.

        成功调度的任务数量。
        """
        return len(self.schedules)

    @property
    def all_scheduled(self) -> bool:
        """Whether all tasks were scheduled.

        是否所有任务都已调度。
        """
        return len(self.unscheduled_task_ids) == 0


class TaskScheduler:
    """Schedules flight tasks respecting precedence constraints.

    遵循优先约束调度航班任务。
    """

    def __init__(self) -> None:
        """Initialize the task scheduler.

        初始化任务调度器。
        """
        self._precedence_rules: dict[str, tuple[str, ...]] = {}

    def add_precedence(
        self,
        task_id: str,
        predecessors: Sequence[str],
    ) -> None:
        """Add precedence constraints for a task.

        为任务添加优先约束。

        Args:
            task_id: Task that must come after predecessors.
            predecessors: Task IDs that must complete first.
        """
        self._precedence_rules[task_id] = tuple(predecessors)

    def schedule(
        self,
        tasks: Sequence[FlightTask],
        *,
        start_time: datetime,
        min_gap_minutes: int = 30,
    ) -> SchedulingResult:
        """Schedule tasks with precedence constraints.

        按优先约束调度任务。

        Args:
            tasks: Tasks to schedule.
            start_time: Earliest scheduling start time.
            min_gap_minutes: Minimum gap between tasks.

        Returns:
            SchedulingResult with generated schedules.
        """
        task_map = {t.task_id: t for t in tasks}
        sorted_ids = self._topological_sort([t.task_id for t in tasks])
        schedules: list[TaskSchedule] = []
        completion_times: dict[str, datetime] = {}
        unscheduled: list[str] = []
        current_time = start_time
        gap = timedelta(minutes=min_gap_minutes)

        for task_id in sorted_ids:
            task = task_map.get(task_id)
            if task is None:
                unscheduled.append(task_id)
                continue

            predecessors = self._precedence_rules.get(task_id, ())
            earliest = current_time
            for pred_id in predecessors:
                pred_end = completion_times.get(pred_id)
                if pred_end is not None:
                    pred_candidate = pred_end + gap
                    if pred_candidate > earliest:
                        earliest = pred_candidate

            duration = timedelta(minutes=task.duration_minutes)
            planned_end = earliest + duration

            schedule = TaskSchedule(
                task_id=task_id,
                planned_start=earliest,
                planned_end=planned_end,
            )
            schedules.append(schedule)
            completion_times[task_id] = planned_end
            current_time = planned_end + gap

        return SchedulingResult(
            schedules=tuple(schedules),
            unscheduled_task_ids=tuple(unscheduled),
        )

    def _topological_sort(
        self,
        task_ids: Sequence[str],
    ) -> list[str]:
        """Sort tasks by precedence using topological order.

        按优先级使用拓扑顺序对任务排序。

        Args:
            task_ids: All task IDs to sort.

        Returns:
            Task IDs in topological order.
        """
        id_set = set(task_ids)
        visited: set[str] = set()
        result: list[str] = []

        def dfs(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            for pred in self._precedence_rules.get(node, ()):
                if pred in id_set:
                    dfs(pred)
            result.append(node)

        for tid in task_ids:
            dfs(tid)

        return result
