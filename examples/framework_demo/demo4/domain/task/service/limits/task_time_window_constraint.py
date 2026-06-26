"""Task time window constraint.

任务时间窗口约束。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ...model.task_schedule import TaskSchedule


@dataclass(frozen=True)
class TimeWindow:
    """A time window constraint for a task.

    任务的时间窗口约束。
    """

    task_id: str
    """Task this window applies to.

    此窗口适用的任务。
    """

    earliest_start: datetime
    """Earliest allowed start time.

    最早允许开始时间。
    """

    latest_end: datetime
    """Latest allowed end time.

    最晚允许结束时间。
    """

    @property
    def span_hours(self) -> float:
        """Window span in hours.

        窗口跨度（小时）。
        """
        delta = self.latest_end - self.earliest_start
        return delta.total_seconds() / 3600.0


class TaskTimeWindowConstraint:
    """Enforces time window constraints on tasks.

    执行任务的时间窗口约束。
    """

    def __init__(self) -> None:
        """Initialize time window constraint.

        初始化时间窗口约束。
        """
        self._windows: dict[str, TimeWindow] = {}

    def add_window(self, window: TimeWindow) -> None:
        """Add a time window constraint.

        添加时间窗口约束。

        Args:
            window: The time window to add.
        """
        self._windows[window.task_id] = window

    def validate(
        self,
        schedules: Sequence[TaskSchedule],
    ) -> Sequence[str]:
        """Validate schedules against time windows.

        根据时间窗口验证调度。

        Args:
            schedules: Schedules to validate.

        Returns:
            Violation descriptions (empty if valid).
        """
        violations: list[str] = []

        for schedule in schedules:
            window = self._windows.get(schedule.task_id)
            if window is None:
                continue

            if schedule.planned_start < window.earliest_start:
                violations.append(
                    f"{schedule.task_id}: starts "
                    f"before earliest allowed "
                    f"{window.earliest_start}"
                )

            if schedule.planned_end > window.latest_end:
                violations.append(
                    f"{schedule.task_id}: ends after latest allowed {window.latest_end}"
                )

        return tuple(violations)

    def is_valid(
        self,
        schedules: Sequence[TaskSchedule],
    ) -> bool:
        """Check if schedules fit within time windows.

        检查调度是否在时间窗口内。

        Args:
            schedules: Schedules to check.

        Returns:
            True if all schedules fit their windows.
        """
        return len(self.validate(schedules)) == 0

    def get_window(
        self,
        task_id: str,
    ) -> TimeWindow | None:
        """Get the time window for a task.

        获取任务的时间窗口。

        Args:
            task_id: Task ID to look up.

        Returns:
            TimeWindow if set, None otherwise.
        """
        return self._windows.get(task_id)
