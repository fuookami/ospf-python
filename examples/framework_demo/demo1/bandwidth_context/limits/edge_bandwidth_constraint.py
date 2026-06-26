"""边带宽约束 / Edge bandwidth constraint.

确保每条边的总分配带宽不超过其容量限制。
Ensures that each edge's total allocated bandwidth does not
exceed its capacity limit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeCapacityViolation:
    """边容量违反记录 / Edge capacity violation record.

    记录一条边的带宽超限信息。
    Records bandwidth excess information for an edge.

    Attributes:
        edge_id: 边标识 / Edge identifier.
        total_allocated: 总分配带宽 / Total allocated bandwidth.
        capacity: 边容量 / Edge capacity.
        excess: 超出量 / Excess amount.
    """

    edge_id: str = ""
    """边标识 / Edge identifier."""

    total_allocated: float = 0.0
    """总分配带宽 / Total allocated bandwidth."""

    capacity: float = 0.0
    """边容量 / Edge capacity."""

    excess: float = 0.0
    """超出量 / Excess amount."""


@dataclass(frozen=True)
class EdgeBandwidthConstraint:
    """边带宽约束 / Edge bandwidth constraint.

    验证每条边的总分配带宽不超过其容量。遍历所有边的
    带宽分配，计算当前总用量并与容量比较。
    Validates that each edge's total allocated bandwidth does not
    exceed its capacity. Iterates over all edge allocations,
    computing current total usage and comparing against capacity.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "edge_bw"
    """约束名称前缀 / Constraint name prefix."""

    def check_edges(
        self,
        *,
        edge_capacities: dict[str, float],
        edge_allocations: dict[str, float],
    ) -> tuple[EdgeCapacityViolation, ...]:
        """检查所有边的带宽约束。

        Check bandwidth constraints for all edges.

        Args:
            edge_capacities: 边到容量的映射。
                / Edge-to-capacity mapping.
            edge_allocations: 边到分配带宽的映射。
                / Edge-to-allocated-bandwidth mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[EdgeCapacityViolation] = []
        for edge_id, capacity in edge_capacities.items():
            if capacity <= 0.0:
                continue
            allocated = edge_allocations.get(edge_id, 0.0)
            if allocated > capacity:
                violations.append(
                    EdgeCapacityViolation(
                        edge_id=edge_id,
                        total_allocated=allocated,
                        capacity=capacity,
                        excess=allocated - capacity,
                    )
                )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        edge_capacities: dict[str, float],
        edge_allocations: dict[str, float],
    ) -> bool:
        """检查边带宽约束是否可行。

        Check whether edge bandwidth constraints are feasible.

        Args:
            edge_capacities: 边到容量的映射。
                / Edge-to-capacity mapping.
            edge_allocations: 边到分配带宽的映射。
                / Edge-to-allocated-bandwidth mapping.

        Returns:
            所有边的带宽均在容量内时返回 True。
            True if all edge bandwidths are within capacity.
        """
        return (
            len(
                self.check_edges(
                    edge_capacities=edge_capacities,
                    edge_allocations=edge_allocations,
                )
            )
            == 0
        )

    def remaining_capacity(
        self,
        edge_id: str,
        edge_capacities: dict[str, float],
        edge_allocations: dict[str, float],
    ) -> float:
        """计算指定边的剩余容量。

        Calculate remaining capacity for an edge.

        Args:
            edge_id: 边标识。/ Edge identifier.
            edge_capacities: 边到容量的映射。
                / Edge-to-capacity mapping.
            edge_allocations: 边到分配带宽的映射。
                / Edge-to-allocated-bandwidth mapping.

        Returns:
            剩余容量，边不存在时返回 0.0。
            Remaining capacity, or 0.0 if edge not found.
        """
        capacity = edge_capacities.get(edge_id, 0.0)
        if capacity <= 0.0:
            return 0.0
        allocated = edge_allocations.get(edge_id, 0.0)
        return max(0.0, capacity - allocated)

    def constraint_name(
        self,
        edge_id: str,
    ) -> str:
        """生成约束名称。

        Generate constraint name.

        Args:
            edge_id: 边标识。/ Edge identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{edge_id}"
