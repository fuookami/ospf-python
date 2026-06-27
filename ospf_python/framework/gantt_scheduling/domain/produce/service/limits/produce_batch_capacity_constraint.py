"""生产批次容量约束 / Produce batch capacity constraint.

确保每个生产批次在任意时间窗口内的使用量不超过批次容量上限。
Ensures that each production batch's usage within any time
window does not exceed its batch capacity upper bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_aggregation import (
        ProduceAggregation,
    )


@dataclass(frozen=True)
class BatchCapacityData:
    """批次容量约束数据 / Batch capacity constraint data.

    表示一条批次容量约束的快照数据。
    Represents a snapshot of a batch capacity constraint.

    Attributes:
        batch_key: 批次标识 / Batch identifier.
        time_window_start: 时间窗口起始 / Time window start.
        time_window_end: 时间窗口结束 / Time window end.
        max_capacity: 最大容量 / Maximum capacity.
        used_capacity: 已使用容量 / Used capacity.
    """

    batch_key: str
    time_window_start: float
    time_window_end: float
    max_capacity: float
    used_capacity: float = 0.0

    @property
    def remaining_capacity(self) -> float:
        """剩余容量 / Remaining capacity."""
        return max(0.0, self.max_capacity - self.used_capacity)

    @property
    def is_over_capacity(self) -> bool:
        """是否超容 / Whether over capacity."""
        return self.used_capacity > self.max_capacity


@dataclass(frozen=True)
class ProduceBatchCapacityConstraint:
    """生产批次容量约束 / Produce batch capacity constraint.

    生成生产批次容量约束数据，用于注册到优化模型中。每条约束
    确保在指定时间窗口内，所有物料项对批次的需求总量不超过
    批次容量上限。
    Generates produce batch capacity constraint data for
    registration into the optimization model. Each constraint
    ensures that within a given time window, the total demand
    from all items on a batch does not exceed the batch capacity
    upper bound.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "produce_batch_capacity"

    def build_constraints(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[BatchCapacityData, ...]:
        """构建批次容量约束列表。

        Build the list of batch capacity constraints.

        遍历所有已注册批次和容量记录，校验每个批次内的
        需求总量是否在容量范围内。
        Iterates over all registered batches and capacity records,
        verifying that total demand within each batch is within
        capacity bounds.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.
        """
        constraints: list[BatchCapacityData] = []
        for cap in aggregation.batch_capacities:
            total_demand = aggregation.total_demand_for_batch(
                cap.batch_key,
            )
            constraints.append(
                BatchCapacityData(
                    batch_key=cap.batch_key,
                    time_window_start=cap.time_window_start,
                    time_window_end=cap.time_window_end,
                    max_capacity=cap.max_capacity,
                    used_capacity=total_demand,
                )
            )
        return tuple(constraints)

    def constraint_name(self, batch_key: str) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            batch_key: 批次标识。/ Batch identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{batch_key}"

    def is_satisfied(
        self,
        aggregation: ProduceAggregation,
    ) -> bool:
        """检查批次容量约束是否满足。

        Check whether batch capacity constraints are satisfied.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            若所有批次容量约束均可满足则返回 True。
            True if all batch capacity constraints can be satisfied.
        """
        for cap in self.build_constraints(aggregation):
            if cap.is_over_capacity:
                return False
        return True

    def violations(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[BatchCapacityData, ...]:
        """获取所有违反批次容量约束的记录。

        Get all records that violate batch capacity constraints.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            违反约束的批次容量记录元组。
            Tuple of batch capacity records violating constraints.
        """
        return tuple(
            cap for cap in self.build_constraints(aggregation) if cap.is_over_capacity
        )
