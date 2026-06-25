"""任务属性模型 / Task attribute model.

定义任务在调度中的可配置属性。
Defines configurable attributes of a task in scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.gantt_scheduling.domain.task.model.task_type import (
    TaskType,
)


@dataclass(frozen=True)
class TaskAttribute:
    """任务属性 / Task attribute.

    描述任务的调度属性和约束条件。
    Describes scheduling attributes and constraint
    conditions of a task.

    Attributes:
        task_type: 任务类型 / Task type.
        priority: 优先级（数值越大优先级越高）/ Priority
            (higher value = higher priority).
        cancel_enabled: 是否允许取消 / Whether cancellation
            is allowed.
        delay_enabled: 是否允许延迟 / Whether delay is
            allowed.
        advance_enabled: 是否允许提前 / Whether advance is
            allowed.
        max_delay: 最大允许延迟时长（秒）/ Maximum allowed
            delay duration (seconds). None 表示无限制 /
            None means unlimited.
        max_advance: 最大允许提前时长（秒）/ Maximum allowed
            advance duration (seconds). None 表示无限制 /
            None means unlimited.
        parallelable: 是否可并行执行 / Whether parallel
            execution is allowed.
        divisible: 是否可分割执行 / Whether divisible
            execution is allowed.
    """

    task_type: TaskType = TaskType.FIXED
    priority: int = 0
    cancel_enabled: bool = False
    delay_enabled: bool = False
    advance_enabled: bool = False
    max_delay: float | None = None
    max_advance: float | None = None
    parallelable: bool = False
    divisible: bool = False

    @staticmethod
    def create(
        *,
        task_type: TaskType = TaskType.FIXED,
        priority: int = 0,
        cancel_enabled: bool = False,
        delay_enabled: bool = False,
        advance_enabled: bool = False,
        max_delay: float | None = None,
        max_advance: float | None = None,
        parallelable: bool = False,
        divisible: bool = False,
    ) -> TaskAttribute:
        """工厂方法创建任务属性 / Factory method to create task attribute.

        Args:
            task_type: 任务类型 / Task type.
            priority: 优先级 / Priority.
            cancel_enabled: 是否允许取消 / Cancel enabled.
            delay_enabled: 是否允许延迟 / Delay enabled.
            advance_enabled: 是否允许提前 / Advance enabled.
            max_delay: 最大延迟 / Max delay.
            max_advance: 最大提前 / Max advance.
            parallelable: 是否可并行 / Parallelable.
            divisible: 是否可分割 / Divisible.

        Returns:
            新的任务属性实例 / New task attribute instance.
        """
        return TaskAttribute(
            task_type=task_type,
            priority=priority,
            cancel_enabled=cancel_enabled,
            delay_enabled=delay_enabled,
            advance_enabled=advance_enabled,
            max_delay=max_delay,
            max_advance=max_advance,
            parallelable=parallelable,
            divisible=divisible,
        )

    @property
    def is_preemptive(self) -> bool:
        """是否为可抢占任务 / Whether task is preemptive.

        Returns:
            任务类型为 PREEMPTIVE 时返回 True。
            True when task type is PREEMPTIVE.
        """
        return self.task_type.allows_preemption

    @property
    def effective_max_delay(self) -> float:
        """获取有效最大延迟 / Get effective max delay.

        Returns:
            最大延迟秒数，未设置时返回正无穷。
            Max delay in seconds, inf if unset.
        """
        if not self.delay_enabled:
            return 0.0
        return self.max_delay if self.max_delay is not None else float("inf")

    @property
    def effective_max_advance(self) -> float:
        """获取有效最大提前 / Get effective max advance.

        Returns:
            最大提前秒数，未设置时返回正无穷。
            Max advance in seconds, inf if unset.
        """
        if not self.advance_enabled:
            return 0.0
        return self.max_advance if self.max_advance is not None else float("inf")

    def with_priority(self, priority: int) -> TaskAttribute:
        """创建不同优先级的新属性 / Create new attribute with different priority.

        Args:
            priority: 新优先级 / New priority.

        Returns:
            新的 TaskAttribute 实例 / New TaskAttribute instance.
        """
        return TaskAttribute(
            task_type=self.task_type,
            priority=priority,
            cancel_enabled=self.cancel_enabled,
            delay_enabled=self.delay_enabled,
            advance_enabled=self.advance_enabled,
            max_delay=self.max_delay,
            max_advance=self.max_advance,
            parallelable=self.parallelable,
            divisible=self.divisible,
        )
