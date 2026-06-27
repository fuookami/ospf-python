"""生产批次需求约束 / Produce batch demand constraint.

确保每个生产批次的需求得到满足。
Ensures that each production batch's demand is satisfied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_aggregation import (
        ProduceAggregation,
    )


@dataclass(frozen=True)
class BatchDemandSatisfaction:
    """批次需求满足状态 / Batch demand satisfaction status.

    Attributes:
        batch_key: 批次标识 / Batch identifier.
        is_satisfied: 是否已满足 / Whether satisfied.
        assigned_amount: 已分配量 / Assigned amount.
        shortfall: 缺口量 / Shortfall amount.
    """

    batch_key: str
    is_satisfied: bool
    assigned_amount: float
    shortfall: float


@dataclass(frozen=True)
class ProduceBatchDemandConstraint:
    """生产批次需求约束 / Produce batch demand constraint.

    生成生产批次需求约束数据，确保每个批次的物料需求
    在可用产能范围内得到满足。
    Generates produce batch demand constraint data, ensuring
    each batch's material demand is satisfied within available
    capacity.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        required_amount: 要求的分配量，0.0 表示使用实际需求 /
            Required amount, 0.0 means use actual demand.
    """

    constraint_name_prefix: str = "produce_batch_demand"
    required_amount: float = 0.0

    def build_constraints(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[BatchDemandSatisfaction, ...]:
        """构建批次需求约束列表。

        Build the list of batch demand constraints.

        遍历所有批次，检查每个批次的总分配量是否满足需求。
        Iterates over all batches, checking whether each batch's
        total assigned amount meets the demand.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            批次需求满足状态元组。
            Tuple of batch demand satisfaction data.
        """
        results: list[BatchDemandSatisfaction] = []
        for batch_key in aggregation.batch_keys:
            batch_assignments = aggregation.assignments_for_batch(
                batch_key,
            )
            total_assigned = sum(a.assignment_amount for a in batch_assignments)
            required = (
                self.required_amount if self.required_amount > 0.0 else total_assigned
            )
            shortfall = max(0.0, required - total_assigned)
            results.append(
                BatchDemandSatisfaction(
                    batch_key=batch_key,
                    is_satisfied=shortfall <= 1e-9,
                    assigned_amount=total_assigned,
                    shortfall=shortfall,
                )
            )
        return tuple(results)

    def constraint_name(self, batch_key: str) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            batch_key: 批次标识。/ Batch identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{batch_key}"

    def unsatisfied_demands(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[BatchDemandSatisfaction, ...]:
        """获取所有未满足的批次需求。

        Get all unsatisfied batch demands.

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
        """检查所有批次需求是否满足。

        Check whether all batch demands are satisfied.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            若所有批次需求均可满足则返回 True。
            True if all batch demands can be satisfied.
        """
        return len(self.unsatisfied_demands(aggregation)) == 0

    def violations(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[BatchDemandSatisfaction, ...]:
        """获取违反约束的记录。

        Get records that violate constraints.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            违反约束的需求记录元组。
            Tuple of demand records violating constraints.
        """
        return self.unsatisfied_demands(aggregation)
