"""甘特调度错误码枚举 / Gantt scheduling error code enumeration.

定义甘特调度领域中的语义化错误码。
Defines semantic error codes for the gantt scheduling domain.
"""

from __future__ import annotations

import enum


class GanttErrors(enum.Enum):
    """甘特调度错误码 / Gantt scheduling error codes.

    用于标识甘特调度过程中各类错误的语义化枚举。
    Semantic enumeration identifying various error
    categories during gantt scheduling.

    Attributes:
        value: 错误码字符串标识 / Error code string identifier.
    """

    TASK_NOT_FOUND = "task_not_found"
    """任务未找到 / Task not found."""

    RESOURCE_NOT_FOUND = "resource_not_found"
    """资源未找到 / Resource not found."""

    SCHEDULING_FAILED = "scheduling_failed"
    """调度失败 / Scheduling failed."""

    CONSTRAINT_VIOLATED = "constraint_violated"
    """约束违反 / Constraint violated."""

    INVALID_TIME_WINDOW = "invalid_time_window"
    """无效时间窗口 / Invalid time window."""

    DUPLICATE_TASK = "duplicate_task"
    """重复任务 / Duplicate task."""

    EXECUTOR_NOT_FOUND = "executor_not_found"
    """执行者未找到 / Executor not found."""

    DEMAND_NOT_SATISFIED = "demand_not_satisfied"
    """需求未满足 / Demand not satisfied."""

    @property
    def description(self) -> str:
        """获取错误描述 / Get error description.

        Returns:
            中英文错误描述 / Bilingual error description.
        """
        return _DESCRIPTIONS.get(self, self.value)


_DESCRIPTIONS: dict[GanttErrors, str] = {
    GanttErrors.TASK_NOT_FOUND: "任务未找到 / Task not found",
    GanttErrors.RESOURCE_NOT_FOUND: "资源未找到 / Resource not found",
    GanttErrors.SCHEDULING_FAILED: "调度失败 / Scheduling failed",
    GanttErrors.CONSTRAINT_VIOLATED: "约束违反 / Constraint violated",
    GanttErrors.INVALID_TIME_WINDOW: "无效时间窗口 / Invalid time window",
    GanttErrors.DUPLICATE_TASK: "重复任务 / Duplicate task",
    GanttErrors.EXECUTOR_NOT_FOUND: "执行者未找到 / Executor not found",
    GanttErrors.DEMAND_NOT_SATISFIED: "需求未满足 / Demand not satisfied",
}
