"""Turnaround model for ground operations.

地面运营周转模型。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Turnaround:
    """Ground turnaround operations between flights.

    航班间的地面周转操作。
    """

    task_id: str
    """ID of the turnaround task.

    周转任务的 ID。
    """

    ground_time: int
    """Ground time in minutes.

    地面时间（分钟）。
    """

    tasks: tuple[str, ...] = ()
    """IDs of sub-tasks during turnaround (cleaning, refueling, etc.).

    周转期间的子任务 ID（清洁、加油等）。
    """

    @property
    def task_count(self) -> int:
        """Number of turnaround sub-tasks.

        周转子任务数量。
        """
        return len(self.tasks)

    @property
    def is_quick_turn(self) -> bool:
        """Whether this is a quick turnaround (<45 minutes).

        是否为快速周转（少于 45 分钟）。
        """
        return self.ground_time < 45

    @property
    def estimated_hours(self) -> float:
        """Ground time expressed in hours.

        以小时表示的地面时间。
        """
        return self.ground_time / 60.0

    def has_task(self, sub_task_id: str) -> bool:
        """Check if a sub-task is part of this turnaround.

        检查子任务是否属于此周转。

        Args:
            sub_task_id: Sub-task identifier to check.

        Returns:
            True if the sub-task exists in this turnaround.
        """
        return sub_task_id in self.tasks
