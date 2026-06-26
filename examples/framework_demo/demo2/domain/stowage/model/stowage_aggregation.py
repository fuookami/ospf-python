"""装载聚合 / Stowage aggregation.

聚合多个装载方案的汇总信息。
Aggregates summary information from multiple stowage plans.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_plan import (
        StowagePlan,
    )


@dataclass(frozen=True)
class StowageAggregation:
    """装载聚合 / Stowage aggregation.

    汇总多个装载方案的统计信息，提供全局视角的
    重量、容积和货物数量统计。
    Summarizes statistics from multiple stowage plans,
    providing a global view of weight, volume, and item
    count statistics.

    Attributes:
        plans: 装载方案列表 / Stowage plan list.
        total_weight: 总重量（千克）/ Total weight (kg).
    """

    plans: tuple[StowagePlan, ...] = field(
        default_factory=tuple,
    )
    """装载方案列表 / Stowage plan list."""

    total_weight: float = 0.0
    """总重量（千克）/ Total weight (kg)."""

    @staticmethod
    def from_plans(
        plans: tuple[StowagePlan, ...],
    ) -> StowageAggregation:
        """从方案列表创建聚合。

        Create aggregation from plan list.

        Args:
            plans: 装载方案列表。/ Stowage plan list.

        Returns:
            聚合实例。/ Aggregation instance.
        """
        total = sum(p.total_weight for p in plans)
        return StowageAggregation(
            plans=plans,
            total_weight=total,
        )

    @property
    def plan_count(self) -> int:
        """方案数量。

        Number of plans.

        Returns:
            方案个数。/ Plan count.
        """
        return len(self.plans)

    @property
    def total_item_count(self) -> int:
        """货物总数量。

        Total number of cargo items.

        Returns:
            所有方案的货物件数之和。
            Sum of item counts across all plans.
        """
        return sum(p.item_count for p in self.plans)

    @property
    def average_weight_per_plan(self) -> float:
        """每方案平均重量。

        Average weight per plan.

        Returns:
            总重量除以方案数，无方案时返回 0.0。
            Total weight divided by plan count, or 0.0 if no plans.
        """
        if not self.plans:
            return 0.0
        return self.total_weight / len(self.plans)

    def plan_by_id(
        self,
        plan_id: str,
    ) -> StowagePlan | None:
        """按标识查找方案。

        Find plan by identifier.

        Args:
            plan_id: 方案标识。/ Plan identifier.

        Returns:
            匹配的方案，不存在时返回 None。
            Matching plan, or None if not found.
        """
        for plan in self.plans:
            if plan.plan_id == plan_id:
                return plan
        return None

    def plans_for_aircraft(
        self,
        aircraft_id: str,
    ) -> tuple[StowagePlan, ...]:
        """获取指定飞机的所有方案。

        Get all plans for a specific aircraft.

        Args:
            aircraft_id: 飞机标识。/ Aircraft identifier.

        Returns:
            匹配的方案元组。/ Tuple of matching plans.
        """
        return tuple(p for p in self.plans if p.aircraft_id == aircraft_id)

    def with_plan(self, plan: StowagePlan) -> StowageAggregation:
        """添加方案到聚合。

        Add a plan to the aggregation.

        Args:
            plan: 要添加的方案。/ Plan to add.

        Returns:
            包含新方案的聚合副本。
            A new aggregation with the plan added.
        """
        return StowageAggregation(
            plans=self.plans + (plan,),
            total_weight=self.total_weight + plan.total_weight,
        )
