"""生产容量约束 / Produce capacity constraint.

确保每个生产单元在任意时间窗口内的使用量不超过其容量上限。
Ensures that each production unit's usage within any time window
does not exceed its capacity upper bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_aggregation import (
        ProduceAggregation,
    )


@dataclass(frozen=True)
class ProduceCapacityData:
    """生产容量约束数据 / Produce capacity constraint data.

    表示一条生产容量约束的快照数据。
    Represents a snapshot of a produce capacity constraint.

    Attributes:
        produce_key: 生产单元标识 / Production unit identifier.
        time_window_start: 时间窗口起始 / Time window start.
        time_window_end: 时间窗口结束 / Time window end.
        max_capacity: 最大容量 / Maximum capacity.
        used_capacity: 已使用容量 / Used capacity.
    """

    produce_key: str
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
class ProduceCapacityConstraint:
    """生产容量约束 / Produce capacity constraint.

    生成生产容量约束数据，用于注册到优化模型中。每条约束
    确保在指定时间窗口内，所有物料项对生产单元的需求总量不
    超过生产容量上限。
    Generates produce capacity constraint data for registration
    into the optimization model. Each constraint ensures that
    within a given time window, the total demand from all items
    on a production unit does not exceed the capacity upper bound.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "produce_capacity"

    def build_constraints(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[ProduceCapacityData, ...]:
        """构建生产容量约束列表。

        Build the list of produce capacity constraints.

        遍历所有已注册生产单元和容量记录，校验每个时间窗口内的
        需求总量是否在容量范围内。
        Iterates over all registered production units and capacity
        records, verifying that total demand within each time
        window is within capacity bounds.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            容量约束数据元组。/ Tuple of capacity constraint data.
        """
        constraints: list[ProduceCapacityData] = []
        for cap in aggregation.capacities:
            overlapping = self._overlapping_demands(
                aggregation=aggregation,
                produce_key=cap.produce_key,
                window_start=cap.time_window_start,
                window_end=cap.time_window_end,
            )
            total_demand = sum(d.demand_amount for d in overlapping)
            constraints.append(
                ProduceCapacityData(
                    produce_key=cap.produce_key,
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
        produce_key: str,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            produce_key: 生产单元标识。/ Production unit id.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return (
            f"{self.constraint_name_prefix}_{produce_key}_{window_start}_{window_end}"
        )

    def is_satisfied(
        self,
        aggregation: ProduceAggregation,
    ) -> bool:
        """检查聚合中的容量约束是否满足。

        Check whether capacity constraints are satisfied
        in the aggregation.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            若所有容量约束均可满足则返回 True。
            True if all capacity constraints can be satisfied.
        """
        for cap in self.build_constraints(aggregation):
            if cap.is_over_capacity:
                return False
        return True

    def violations(
        self,
        aggregation: ProduceAggregation,
    ) -> tuple[ProduceCapacityData, ...]:
        """获取所有违反容量约束的记录。

        Get all records that violate capacity constraints.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.

        Returns:
            违反约束的容量记录元组。
            Tuple of capacity records violating constraints.
        """
        return tuple(
            cap for cap in self.build_constraints(aggregation) if cap.is_over_capacity
        )

    @staticmethod
    def _overlapping_demands(
        *,
        aggregation: ProduceAggregation,
        produce_key: str,
        window_start: float,
        window_end: float,
    ) -> tuple:
        """获取与时间窗口重叠的需求。

        Get demands overlapping with the time window.

        Args:
            aggregation: 生产聚合。/ Produce aggregation.
            produce_key: 生产单元标识。/ Production unit id.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            重叠的需求元组。/ Tuple of overlapping demands.
        """
        return tuple(
            d
            for d in aggregation.demands
            if d.produce_key == produce_key
            and d.time_window_start < window_end
            and d.time_window_end > window_start
        )
