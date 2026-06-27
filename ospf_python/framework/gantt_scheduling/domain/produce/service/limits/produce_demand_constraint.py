"""生产需求约束 / Produce demand constraint.

确保每个生产物料项的需求得到满足。
Ensures that each production item's demand is satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_aggregation import (
        ProduceAggregation,
    )


@dataclass(frozen=True)
class ProduceDemandSatisfaction:
    """生产需求满足状态 / Produce demand satisfaction status.

    Attributes:
        item_key: 物料项标识 / Item identifier.
        is_satisfied: 是否已满足 / Whether satisfied.
        assigned_amount: 已分配量 / Assigned amount.
        shortfall: 缺口量 / Shortfall amount.
    """

    item_key: str
    is_satisfied: bool
    assigned_amount: float
    shortfall: float


@dataclass(frozen=True)
class ProduceDemandConstraint:
    """生产需求约束 / Produce demand constraint.

    生成生产需求约束数据，确保每个物料项的生产需求在可用
    产能范围内得到满足。支持刚性需求和柔性需求。
    Generates produce demand constraint data, ensuring each
    item's production demand is satisfied within available
    capacity. Supports mandatory and flexible demands.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        required_amount: 要求的分配量，0.0 表示使用实际需求 /
            Required amount, 0.0 means use actual demand.
    """

    constraint_name_prefix: str = "produce_demand"
    required_amount: float = 0.0

    def build_constraints(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[ProduceDemandSatisfaction, ...]:
        """构建生产需求约束列表。

        Build the list of produce demand constraints.

        遍历所有物料项，检查每个物料项的总分配量是否满足需求。
        Iterates over all items, checking whether each item's
        total assigned amount meets the demand.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            需求满足状态元组。/ Tuple of demand satisfaction data.
        """
        results: list[ProduceDemandSatisfaction] = []
        for item_key in aggregation.item_keys:
            item_assignments = aggregation.assignments_for_item(
                item_key,
            )
            total_assigned = sum(a.assignment_amount for a in item_assignments)
            required = (
                self.required_amount if self.required_amount > 0.0 else total_assigned
            )
            shortfall = max(0.0, required - total_assigned)
            results.append(
                ProduceDemandSatisfaction(
                    item_key=item_key,
                    is_satisfied=shortfall <= 1e-9,
                    assigned_amount=total_assigned,
                    shortfall=shortfall,
                )
            )
        return tuple(results)

    def constraint_name(self, item_key: str) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            item_key: 物料项标识。/ Item identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{item_key}"

    def unsatisfied_demands(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[ProduceDemandSatisfaction, ...]:
        """获取所有未满足的需求。

        Get all unsatisfied demands.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            未满足的需求元组。/ Tuple of unsatisfied demands.
        """
        return tuple(
            s for s in self.build_constraints(aggregation) if not s.is_satisfied
        )

    def is_satisfied(
        self,
        aggregation: ProduceAggregation,
    ) -> bool:
        """检查所有需求是否满足。

        Check whether all demands are satisfied.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            若所有需求均可满足则返回 True。
            True if all demands can be satisfied.
        """
        return len(self.unsatisfied_demands(aggregation)) == 0

    def violations(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[ProduceDemandSatisfaction, ...]:
        """获取违反约束的记录。

        Get records that violate constraints.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            违反约束的需求记录元组。
            Tuple of demand records violating constraints.
        """
        return self.unsatisfied_demands(aggregation)
