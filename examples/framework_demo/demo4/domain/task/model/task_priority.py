"""Task priority enumeration.

任务优先级枚举。
"""

from __future__ import annotations

from enum import IntEnum, unique


@unique
class TaskPriority(IntEnum):
    """Priority level of a flight task.

    航班任务的优先级。
    """

    CRITICAL = 0
    """Must be scheduled first, highest priority.

    必须优先调度，最高优先级。
    """

    HIGH = 1
    """High priority task.

    高优先级任务。
    """

    NORMAL = 2
    """Standard priority task.

    标准优先级任务。
    """

    LOW = 3
    """Lowest priority task.

    最低优先级任务。
    """

    @property
    def display_name(self) -> str:
        """Human-readable display name.

        人类可读的显示名称。
        """
        return {
            TaskPriority.CRITICAL: "Critical",
            TaskPriority.HIGH: "High",
            TaskPriority.NORMAL: "Normal",
            TaskPriority.LOW: "Low",
        }[self]
