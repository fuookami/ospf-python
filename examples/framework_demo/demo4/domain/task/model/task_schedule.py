"""Task schedule model.

任务调度模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TaskSchedule:
    """Planned and actual timing for a flight task.

    航班任务的计划和实际时间。
    """

    task_id: str
    """ID of the scheduled task.

    被调度任务的 ID。
    """

    planned_start: datetime
    """Planned start time.

    计划开始时间。
    """

    planned_end: datetime
    """Planned end time.

    计划结束时间。
    """

    actual_start: datetime | None = None
    """Actual start time, None if not yet started.

    实际开始时间，尚未开始时为 None。
    """

    actual_end: datetime | None = None
    """Actual end time, None if not yet finished.

    实际结束时间，尚未结束时为 None。
    """

    @property
    def is_started(self) -> bool:
        """Whether the task has actually started.

        任务是否已实际开始。
        """
        return self.actual_start is not None

    @property
    def is_completed(self) -> bool:
        """Whether the task has actually completed.

        任务是否已实际完成。
        """
        return self.actual_start is not None and self.actual_end is not None

    @property
    def delay_minutes(self) -> int:
        """Delay in minutes from planned start (0 if on time).

        相对于计划开始的延迟分钟数（准时为 0）。
        """
        if self.actual_start is None:
            return 0
        delta = self.actual_start - self.planned_start
        return max(0, int(delta.total_seconds() // 60))

    @property
    def planned_duration_minutes(self) -> int:
        """Planned duration in minutes.

        计划持续时间（分钟）。
        """
        delta = self.planned_end - self.planned_start
        return int(delta.total_seconds() // 60)
