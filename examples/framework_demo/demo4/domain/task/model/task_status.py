"""Task status enumeration.

任务状态枚举。
"""

from __future__ import annotations

from enum import Enum, unique


@unique
class TaskStatus(Enum):
    """Status of a flight task.

    航班任务的状态。
    """

    SCHEDULED = "SCHEDULED"
    """Task is planned but not yet started.

    任务已计划但尚未开始。
    """

    IN_PROGRESS = "IN_PROGRESS"
    """Task is currently being executed.

    任务正在执行中。
    """

    COMPLETED = "COMPLETED"
    """Task has been completed successfully.

    任务已成功完成。
    """

    CANCELLED = "CANCELLED"
    """Task has been cancelled.

    任务已被取消。
    """

    DELAYED = "DELAYED"
    """Task is delayed from its planned time.

    任务已从计划时间延迟。
    """

    @property
    def is_active(self) -> bool:
        """Whether the task is currently active.

        任务是否当前活跃。
        """
        return self in (
            TaskStatus.SCHEDULED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.DELAYED,
        )
