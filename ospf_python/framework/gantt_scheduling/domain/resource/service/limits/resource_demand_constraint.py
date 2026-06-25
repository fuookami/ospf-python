"""资源需求约束 / Resource demand constraint.

确保每个任务的资源需求得到满足，支持刚性和柔性需求。
Ensures that each task's resource demands are satisfied,
supporting both mandatory and flexible demands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_aggregation import (
        ResourceAggregation,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
        ResourceDemand,
    )


@dataclass(frozen=True)
class DemandSatisfaction:
    """需求满足状态 / Demand satisfaction status.

    Attributes:
        demand: 原始需求 / Original demand.
        is_satisfied: 是否已满足 / Whether satisfied.
        shortfall: 缺口量 / Shortfall amount.
    """

    demand: ResourceDemand
    is_satisfied: bool
    shortfall: float


@dataclass(frozen=True)
class ResourceDemandConstraint:
    """资源需求约束 / Resource demand constraint.

    生成资源需求约束数据，确保每个任务在指定时间窗口内获得
    所需的资源容量。支持刚性需求（必须满足）和柔性需求
    （允许部分满足）。
    Generates resource demand constraint data, ensuring each task
    receives the required resource capacity within its time window.
    Supports mandatory demands (must be satisfied) and flexible
    demands (partial satisfaction allowed).

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "resource_demand"

    def build_constraints(
        self,
        aggregation: ResourceAggregation,
    ) -> tuple[DemandSatisfaction, ...]:
        """构建资源需求约束列表。

        Build the list of resource demand constraints.

        遍历所有需求，检查每个需求是否能在对应资源的容量
        范围内得到满足。
        Iterates over all demands, checking whether each demand
        can be satisfied within the corresponding resource capacity.

        Args:
            aggregation: 资源聚合。/ Resource aggregation.

        Returns:
            需求满足状态元组。/ Tuple of demand satisfaction statuses.
        """
        results: list[DemandSatisfaction] = []
        for demand in aggregation.demands:
            capacity = aggregation.get_capacity(
                resource_key=demand.resource_key,
                window_start=demand.time_window_start,
                window_end=demand.time_window_end,
            )
            if capacity is None:
                # 无容量记录时检查资源是否存在
                # Check resource existence when no capacity record
                resource = aggregation.get_resource(
                    demand.resource_key,
                )
                if resource is None:
                    results.append(
                        DemandSatisfaction(
                            demand=demand,
                            is_satisfied=False,
                            shortfall=demand.demand_amount,
                        )
                    )
                else:
                    effective = resource.effective_capacity_during(
                        start=demand.time_window_start,
                        end=demand.time_window_end,
                    )
                    shortfall = max(
                        0.0,
                        demand.demand_amount - effective,
                    )
                    results.append(
                        DemandSatisfaction(
                            demand=demand,
                            is_satisfied=shortfall <= 0.0,
                            shortfall=shortfall,
                        )
                    )
            else:
                shortfall = max(
                    0.0,
                    demand.demand_amount - capacity.remaining_capacity,
                )
                results.append(
                    DemandSatisfaction(
                        demand=demand,
                        is_satisfied=shortfall <= 0.0,
                        shortfall=shortfall,
                    )
                )
        return tuple(results)

    def constraint_name(
        self,
        *,
        task_key: str,
        resource_key: str,
    ) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            task_key: 任务标识。/ Task identifier.
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{task_key}_{resource_key}"

    def unsatisfied_demands(
        self,
        aggregation: ResourceAggregation,
    ) -> tuple[DemandSatisfaction, ...]:
        """获取所有未满足的需求。

        Get all unsatisfied demands.

        Args:
            aggregation: 资源聚合。/ Resource aggregation.

        Returns:
            未满足的需求元组。/ Tuple of unsatisfied demands.
        """
        return tuple(
            s for s in self.build_constraints(aggregation) if not s.is_satisfied
        )

    def mandatory_violations(
        self,
        aggregation: ResourceAggregation,
    ) -> tuple[DemandSatisfaction, ...]:
        """获取所有刚性需求违反。

        Get all mandatory demand violations.

        Args:
            aggregation: 资源聚合。/ Resource aggregation.

        Returns:
            刚性需求违反元组。/ Tuple of mandatory violations.
        """
        return tuple(
            s
            for s in self.build_constraints(aggregation)
            if not s.is_satisfied and s.demand.is_mandatory
        )

    def is_feasible(
        self,
        aggregation: ResourceAggregation,
    ) -> bool:
        """检查所有刚性需求是否可行。

        Check whether all mandatory demands are feasible.

        Args:
            aggregation: 资源聚合。/ Resource aggregation.

        Returns:
            若所有刚性需求均可满足则返回 True。
            True if all mandatory demands can be satisfied.
        """
        return len(self.mandatory_violations(aggregation)) == 0
