"""资源容量约束 / Resource capacity constraint.

确保每个资源在任意时间窗口内的使用量不超过其容量上限。
Ensures that each resource's usage within any time window does
not exceed its capacity upper bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_capacity import (
    ResourceCapacity,
)

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_aggregation import (
        ResourceAggregation,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
        ResourceDemand,
    )


@dataclass(frozen=True)
class ResourceCapacityConstraint:
    """资源容量约束 / Resource capacity constraint.

    生成资源容量约束数据，用于注册到优化模型中。每条约束
    确保在指定时间窗口内，所有任务对该资源的需求总量不超过
    资源容量上限。
    Generates resource capacity constraint data for registration
    into the optimization model. Each constraint ensures that
    within a given time window, the total demand from all tasks
    on a resource does not exceed the resource capacity upper bound.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "resource_capacity"

    def build_constraints(
        self,
        aggregation: ResourceAggregation,
    ) -> tuple[ResourceCapacity, ...]:
        """构建资源容量约束列表。

        Build the list of resource capacity constraints.

        遍历所有已注册资源和容量记录，校验每个时间窗口内的
        需求总量是否在容量范围内。
        Iterates over all registered resources and capacity records,
        verifying that total demand within each time window is
        within capacity bounds.

        Args:
            aggregation: 资源聚合。/ Resource aggregation.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.
        """
        constraints: list[ResourceCapacity] = []
        for cap in aggregation.capacities:
            overlapping_demands = self._overlapping_demands(
                aggregation=aggregation,
                resource_key=cap.resource_key,
                window_start=cap.time_window_start,
                window_end=cap.time_window_end,
            )
            total_demand = sum(d.demand_amount for d in overlapping_demands)
            constraints.append(
                ResourceCapacity(
                    resource_key=cap.resource_key,
                    time_window_start=cap.time_window_start,
                    time_window_end=cap.time_window_end,
                    max_capacity=cap.max_capacity,
                    used_capacity=total_demand,
                )
            )
        return tuple(constraints)

    def constraint_name(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return (
            f"{self.constraint_name_prefix}_{resource_key}_{window_start}_{window_end}"
        )

    def is_feasible(
        self,
        aggregation: ResourceAggregation,
    ) -> bool:
        """检查聚合中的容量约束是否可行。

        Check whether capacity constraints are feasible
        in the aggregation.

        Args:
            aggregation: 资源聚合。/ Resource aggregation.

        Returns:
            若所有容量约束均可满足则返回 True。
            True if all capacity constraints can be satisfied.
        """
        for cap in self.build_constraints(aggregation):
            if cap.used_capacity > cap.max_capacity:
                return False
        return True

    def violations(
        self,
        aggregation: ResourceAggregation,
    ) -> tuple[ResourceCapacity, ...]:
        """获取所有违反容量约束的记录。

        Get all records that violate capacity constraints.

        Args:
            aggregation: 资源聚合。/ Resource aggregation.

        Returns:
            违反约束的容量记录元组。
            Tuple of capacity records violating constraints.
        """
        return tuple(
            cap
            for cap in self.build_constraints(aggregation)
            if cap.used_capacity > cap.max_capacity
        )

    @staticmethod
    def _overlapping_demands(
        *,
        aggregation: ResourceAggregation,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> tuple[ResourceDemand, ...]:
        """获取与时间窗口重叠的需求。

        Get demands overlapping with the time window.

        Args:
            aggregation: 资源聚合。/ Resource aggregation.
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            重叠的需求元组。/ Tuple of overlapping demands.
        """
        return tuple(
            d
            for d in aggregation.demands
            if d.resource_key == resource_key
            and d.time_window_start < window_end
            and d.time_window_end > window_start
        )
