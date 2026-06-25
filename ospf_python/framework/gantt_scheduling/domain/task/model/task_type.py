"""任务类型枚举 / Task type enumeration.

定义甘特调度中任务的执行模式类型。
Defines task execution mode types in gantt scheduling.
"""

from __future__ import annotations

import enum


class TaskType(enum.Enum):
    """任务类型 / Task type.

    描述任务的调度执行模式。
    Describes the scheduling execution mode of a task.

    Attributes:
        value: 类型字符串标识 / Type string identifier.
    """

    FIXED = "fixed"
    """固定任务 / Fixed task.

    执行时间固定，不可被抢占或分割。
    Fixed execution time, cannot be preempted or split.
    """

    VARIABLE = "variable"
    """可变任务 / Variable task.

    执行时间可在允许范围内调整。
    Execution time adjustable within allowed range.
    """

    PREEMPTIVE = "preemptive"
    """可抢占任务 / Preemptive task.

    可被更高优先级任务中断并稍后恢复。
    Can be interrupted by higher-priority tasks
    and resumed later.
    """

    @property
    def allows_preemption(self) -> bool:
        """是否允许抢占 / Whether preemption is allowed.

        Returns:
            仅 PREEMPTIVE 类型返回 True。
            True only for PREEMPTIVE type.
        """
        return self is TaskType.PREEMPTIVE

    @property
    def allows_duration_change(self) -> bool:
        """是否允许调整时长 / Whether duration change is allowed.

        Returns:
            VARIABLE 和 PREEMPTIVE 类型返回 True。
            True for VARIABLE and PREEMPTIVE types.
        """
        return self in (TaskType.VARIABLE, TaskType.PREEMPTIVE)

    def is_compatible_with(self, other: TaskType) -> bool:
        """检查与另一任务类型的兼容性。

        Check compatibility with another task type.

        固定任务不可与可抢占任务在同一资源上并行。
        Fixed tasks cannot run in parallel with preemptive
        tasks on the same resource.

        Args:
            other: 另一任务类型 / The other task type.

        Returns:
            是否兼容 / Whether compatible.
        """
        if self is TaskType.FIXED and other is TaskType.PREEMPTIVE:
            return False
        return not (self is TaskType.PREEMPTIVE and other is TaskType.FIXED)
