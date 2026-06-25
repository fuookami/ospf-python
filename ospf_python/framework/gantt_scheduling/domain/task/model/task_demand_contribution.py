"""任务需求贡献模型 / Task demand contribution model.

描述任务对资源需求约束的贡献系数。
Describes a task's contribution coefficient to
resource demand constraints.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskDemandContribution:
    """任务需求贡献 / Task demand contribution.

    在列生成框架中，描述某个任务对某一资源需求约束的
    贡献系数。用于构建约束矩阵中的系数项。
    In the column generation framework, describes a
    task's contribution coefficient to a resource demand
    constraint. Used to build coefficient entries in the
    constraint matrix.

    Attributes:
        task_key: 任务键 / Task key.
        resource_key: 资源键 / Resource key.
        coefficient: 贡献系数 / Contribution coefficient.
            正值表示消耗资源，负值表示释放资源。
            Positive = consumes resource, negative = releases.
    """

    task_key: str
    resource_key: str
    coefficient: float

    @staticmethod
    def create(
        *,
        task_key: str,
        resource_key: str,
        coefficient: float,
    ) -> TaskDemandContribution:
        """工厂方法创建贡献 / Factory to create contribution.

        Args:
            task_key: 任务键 / Task key.
            resource_key: 资源键 / Resource key.
            coefficient: 贡献系数 / Contribution coefficient.

        Returns:
            新的贡献实例 / New contribution instance.
        """
        return TaskDemandContribution(
            task_key=task_key,
            resource_key=resource_key,
            coefficient=coefficient,
        )

    @staticmethod
    def consumption(
        task_key: str,
        resource_key: str,
        amount: float,
    ) -> TaskDemandContribution:
        """创建资源消耗贡献 / Create resource consumption contribution.

        Args:
            task_key: 任务键 / Task key.
            resource_key: 资源键 / Resource key.
            amount: 消耗量 / Consumption amount.

        Returns:
            正系数的贡献实例 / Positive coefficient contribution.
        """
        return TaskDemandContribution(
            task_key=task_key,
            resource_key=resource_key,
            coefficient=amount,
        )

    @staticmethod
    def release(
        task_key: str,
        resource_key: str,
        amount: float,
    ) -> TaskDemandContribution:
        """创建资源释放贡献 / Create resource release contribution.

        Args:
            task_key: 任务键 / Task key.
            resource_key: 资源键 / Resource key.
            amount: 释放量 / Release amount.

        Returns:
            负系数的贡献实例 / Negative coefficient contribution.
        """
        return TaskDemandContribution(
            task_key=task_key,
            resource_key=resource_key,
            coefficient=-amount,
        )

    @property
    def is_consumption(self) -> bool:
        """是否为资源消耗 / Whether this is resource consumption.

        Returns:
            系数为正时返回 True。
            True when coefficient is positive.
        """
        return self.coefficient > 0

    @property
    def is_release(self) -> bool:
        """是否为资源释放 / Whether this is resource release.

        Returns:
            系数为负时返回 True。
            True when coefficient is negative.
        """
        return self.coefficient < 0

    @property
    def absolute_contribution(self) -> float:
        """获取绝对贡献量 / Get absolute contribution amount.

        Returns:
            系数的绝对值 / Absolute value of coefficient.
        """
        return abs(self.coefficient)

    def scaled(self, factor: float) -> TaskDemandContribution:
        """缩放贡献系数 / Scale contribution coefficient.

        Args:
            factor: 缩放因子 / Scale factor.

        Returns:
            缩放后的新实例 / New scaled instance.
        """
        return TaskDemandContribution(
            task_key=self.task_key,
            resource_key=self.resource_key,
            coefficient=self.coefficient * factor,
        )
