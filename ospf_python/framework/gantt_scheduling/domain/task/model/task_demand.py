"""任务需求模型 / Task demand model.

定义任务对资源的需求描述。
Defines the resource demand description of a task.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskDemand:
    """任务资源需求 / Task resource demand.

    描述某个任务对某一资源类型的需求量和约束。
    Describes a task's demand quantity and constraints
    for a specific resource type.

    Attributes:
        task_key: 关联的任务键 / Associated task key.
        resource_key: 所需资源键 / Required resource key.
        amount: 需求量 / Demand amount.
        min_amount: 最小需求量 / Minimum demand amount.
            None 表示等于 amount / None means equals amount.
        max_amount: 最大需求量 / Maximum demand amount.
            None 表示等于 amount / None means equals amount.
    """

    task_key: str
    resource_key: str
    amount: float
    min_amount: float | None = None
    max_amount: float | None = None

    @staticmethod
    def create(
        *,
        task_key: str,
        resource_key: str,
        amount: float,
        min_amount: float | None = None,
        max_amount: float | None = None,
    ) -> TaskDemand:
        """工厂方法创建任务需求 / Factory to create task demand.

        Args:
            task_key: 任务键 / Task key.
            resource_key: 资源键 / Resource key.
            amount: 需求量 / Demand amount.
            min_amount: 最小需求量 / Min demand amount.
            max_amount: 最大需求量 / Max demand amount.

        Returns:
            新的任务需求实例 / New task demand instance.
        """
        return TaskDemand(
            task_key=task_key,
            resource_key=resource_key,
            amount=amount,
            min_amount=min_amount,
            max_amount=max_amount,
        )

    @property
    def effective_min(self) -> float:
        """获取有效最小需求量 / Get effective minimum demand.

        Returns:
            最小需求量，未设置时等于 amount。
            Min demand, equals amount when unset.
        """
        return self.min_amount if self.min_amount is not None else self.amount

    @property
    def effective_max(self) -> float:
        """获取有效最大需求量 / Get effective maximum demand.

        Returns:
            最大需求量，未设置时等于 amount。
            Max demand, equals amount when unset.
        """
        return self.max_amount if self.max_amount is not None else self.amount

    @property
    def is_flexible(self) -> bool:
        """需求量是否可灵活调整 / Whether demand is flexible.

        Returns:
            当 min != max 时返回 True。
            True when min != max.
        """
        return self.effective_min != self.effective_max

    def is_satisfied_by(self, available: float) -> bool:
        """检查供给是否满足需求 / Check if supply satisfies demand.

        Args:
            available: 可用量 / Available amount.

        Returns:
            是否满足 / Whether satisfied.
        """
        return available >= self.effective_min

    def with_amount(self, amount: float) -> TaskDemand:
        """创建不同需求量的新实例 / Create new instance with different amount.

        Args:
            amount: 新需求量 / New demand amount.

        Returns:
            新的任务需求 / New task demand.
        """
        return TaskDemand(
            task_key=self.task_key,
            resource_key=self.resource_key,
            amount=amount,
            min_amount=self.min_amount,
            max_amount=self.max_amount,
        )
