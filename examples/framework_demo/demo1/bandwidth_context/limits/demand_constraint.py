"""需求约束 / Demand constraint.

确保每条服务的带宽需求得到满足。
Ensures that each service's bandwidth demand is met.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemandViolation:
    """需求违反记录 / Demand violation record.

    记录一条服务的带宽需求未满足信息。
    Records unmet bandwidth demand information for a service.

    Attributes:
        service_id: 服务标识 / Service identifier.
        required_demand: 需求量 / Required demand.
        allocated_bandwidth: 已分配带宽 / Allocated bandwidth.
        shortfall: 缺口量 / Shortfall amount.
    """

    service_id: str = ""
    """服务标识 / Service identifier."""

    required_demand: float = 0.0
    """需求量 / Required demand."""

    allocated_bandwidth: float = 0.0
    """已分配带宽 / Allocated bandwidth."""

    shortfall: float = 0.0
    """缺口量 / Shortfall amount."""


@dataclass(frozen=True)
class DemandConstraint:
    """需求约束 / Demand constraint.

    验证每条服务的带宽分配是否满足其需求。遍历所有服务，
    比较已分配带宽与需求量。
    Validates that each service's bandwidth allocation meets its
    demand. Iterates over all services, comparing allocated
    bandwidth against demand.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        tolerance: 容差比例 / Tolerance ratio.
    """

    constraint_name_prefix: str = "demand"
    """约束名称前缀 / Constraint name prefix."""

    tolerance: float = 0.01
    """容差比例 / Tolerance ratio."""

    def check_demands(
        self,
        *,
        service_demands: dict[str, float],
        service_allocations: dict[str, float],
    ) -> tuple[DemandViolation, ...]:
        """检查所有服务的需求约束。

        Check demand constraints for all services.

        Args:
            service_demands: 服务到需求量的映射。
                / Service-to-demand mapping.
            service_allocations: 服务到已分配带宽的映射。
                / Service-to-allocated-bandwidth mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[DemandViolation] = []
        for svc_id, demand in service_demands.items():
            if demand <= 0.0:
                continue
            allocated = service_allocations.get(svc_id, 0.0)
            threshold = demand * (1.0 - self.tolerance)
            if allocated < threshold:
                violations.append(
                    DemandViolation(
                        service_id=svc_id,
                        required_demand=demand,
                        allocated_bandwidth=allocated,
                        shortfall=demand - allocated,
                    )
                )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        service_demands: dict[str, float],
        service_allocations: dict[str, float],
    ) -> bool:
        """检查需求约束是否可行。

        Check whether demand constraints are feasible.

        Args:
            service_demands: 服务到需求量的映射。
                / Service-to-demand mapping.
            service_allocations: 服务到已分配带宽的映射。
                / Service-to-allocated-bandwidth mapping.

        Returns:
            所有服务需求均满足时返回 True。
            True if all service demands are satisfied.
        """
        return (
            len(
                self.check_demands(
                    service_demands=service_demands,
                    service_allocations=service_allocations,
                )
            )
            == 0
        )

    def constraint_name(
        self,
        service_id: str,
    ) -> str:
        """生成约束名称。

        Generate constraint name.

        Args:
            service_id: 服务标识。/ Service identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{service_id}"
