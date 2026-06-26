"""Bunch model for scheduling task groups.

编排任务组模型 / Scheduling task group model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bunch:
    """A group of tasks scheduled on the same resource within a time window.

    在同一资源上、在时间窗口内调度的任务组。
    """

    bunch_id: str
    tasks: tuple[str, ...]
    resource_type: str
    start_time: float
    end_time: float

    @property
    def duration(self) -> float:
        """Total duration of the bunch in time units.

        任务组的总持续时间（时间单位）。
        """
        return self.end_time - self.start_time

    @property
    def task_count(self) -> int:
        """Number of tasks in the bunch.

        任务组中的任务数量。
        """
        return len(self.tasks)

    def overlaps(self, other: Bunch) -> bool:
        """Check whether this bunch temporally overlaps with another.

        检查此任务组是否与另一个在时间上重叠。
        """
        if self.resource_type != other.resource_type:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time

    def contains_task(self, task_id: str) -> bool:
        """Check whether a task belongs to this bunch.

        检查某个任务是否属于此任务组。
        """
        return task_id in self.tasks

    def time_gap_to(self, other: Bunch) -> float:
        """Calculate the time gap between this bunch and another.

        计算此任务组与另一个之间的时间间隔。
        """
        if self.end_time <= other.start_time:
            return other.start_time - self.end_time
        if other.end_time <= self.start_time:
            return self.start_time - other.end_time
        return 0.0
