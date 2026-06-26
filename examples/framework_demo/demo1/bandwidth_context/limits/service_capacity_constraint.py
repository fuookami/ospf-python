"""服务容量约束 / Service capacity constraint.

确保每条服务的带宽分配不超过其最大容量限制。
Ensures that each service's bandwidth allocation does not
exceed its maximum capacity limit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceCapacityViolation:
    """服务容量违反记录 / Service capacity violation record.

    记录一条服务的带宽超限信息。
    Records bandwidth excess information for a service.

    Attributes:
        service_id: 服务标识 / Service identifier.
        allocated_bandwidth: 已分配带宽 / Allocated bandwidth.
        max_capacity: 最大容量 / Maximum capacity.
        excess: 超出量 / Excess amount.
    """

    service_id: str = ""
    """服务标识 / Service identifier."""

    allocated_bandwidth: float = 0.0
    """已分配带宽 / Allocated bandwidth."""

    max_capacity: float = 0.0
    """最大容量 / Maximum capacity."""

    excess: float = 0.0
    """超出量 / Excess amount."""


@dataclass(frozen=True)
class ServiceCapacityConstraint:
    """服务容量约束 / Service capacity constraint.

    验证每条服务的带宽分配不超过其最大容量。遍历所有服务，
    比较已分配带宽与最大容量。
    Validates that each service's bandwidth allocation does not
    exceed its maximum capacity. Iterates over all services,
    comparing allocated bandwidth against maximum capacity.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "svc_cap"
    """约束名称前缀 / Constraint name prefix."""

    def check_services(
        self,
        *,
        service_max_capacities: dict[str, float],
        service_allocations: dict[str, float],
    ) -> tuple[ServiceCapacityViolation, ...]:
        """检查所有服务的容量约束。

        Check capacity constraints for all services.

        Args:
            service_max_capacities: 服务到最大容量的映射。
                / Service-to-max-capacity mapping.
            service_allocations: 服务到已分配带宽的映射。
                / Service-to-allocated-bandwidth mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[ServiceCapacityViolation] = []
        for svc_id, max_cap in service_max_capacities.items():
            if max_cap <= 0.0:
                continue
            allocated = service_allocations.get(svc_id, 0.0)
            if allocated > max_cap:
                violations.append(
                    ServiceCapacityViolation(
                        service_id=svc_id,
                        allocated_bandwidth=allocated,
                        max_capacity=max_cap,
                        excess=allocated - max_cap,
                    )
                )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        service_max_capacities: dict[str, float],
        service_allocations: dict[str, float],
    ) -> bool:
        """检查服务容量约束是否可行。

        Check whether service capacity constraints are feasible.

        Args:
            service_max_capacities: 服务到最大容量的映射。
                / Service-to-max-capacity mapping.
            service_allocations: 服务到已分配带宽的映射。
                / Service-to-allocated-bandwidth mapping.

        Returns:
            所有服务的带宽均在容量内时返回 True。
            True if all service bandwidths are within capacity.
        """
        return (
            len(
                self.check_services(
                    service_max_capacities=service_max_capacities,
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
