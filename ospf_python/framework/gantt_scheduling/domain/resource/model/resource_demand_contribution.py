"""资源需求贡献 / Resource demand contribution.

将任务的资源需求分解为对多个资源的贡献份额。
Decomposes a task's resource demand into contribution shares
across multiple resources.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceDemandContribution:
    """资源需求贡献 / Resource demand contribution.

    表示某个任务对特定资源的需求贡献比例，用于在多资源替代
    或分流场景下分配需求量。
    Represents a task's demand contribution ratio to a specific
    resource, used to allocate demand in multi-resource
    substitution or splitting scenarios.

    Attributes:
        task_key: 关联任务标识 / Associated task identifier.
        resource_key: 目标资源标识 / Target resource identifier.
        contribution_ratio: 贡献比例 (0.0, 1.0] /
            Contribution ratio (0.0, 1.0].
        base_demand: 基础需求量 / Base demand amount.
    """

    task_key: str
    resource_key: str
    contribution_ratio: float
    base_demand: float

    @property
    def effective_demand(self) -> float:
        """有效需求量 = 基础需求 * 贡献比例。

        Effective demand = base_demand * contribution_ratio.
        """
        return self.base_demand * self.contribution_ratio

    def with_ratio(self, new_ratio: float) -> ResourceDemandContribution:
        """创建贡献比例修改后的副本。

        Create a copy with a modified contribution ratio.

        Args:
            new_ratio: 新的贡献比例。/ New contribution ratio.

        Returns:
            比例更新后的 ResourceDemandContribution 副本。
            A new instance with updated contribution_ratio.
        """
        return ResourceDemandContribution(
            task_key=self.task_key,
            resource_key=self.resource_key,
            contribution_ratio=new_ratio,
            base_demand=self.base_demand,
        )
