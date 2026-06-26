"""Service assignment constraint — 服务路由约束。

确保每条服务均被分配有效路由。
Ensures that each service is assigned a valid route.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..aggregation import RouteAggregation


@dataclass(frozen=True)
class ServiceRoutingStatus:
    """服务路由状态 / Service routing status.

    Attributes:
        service_id: 服务标识 / Service identifier.
        is_routed: 是否已路由 / Whether routed.
        path_length: 路径长度（节点数） / Path length (node count).
        starts_at_source: 路径是否从源节点开始 /
            Whether path starts at source.
        ends_at_target: 路径是否在目标节点结束 /
            Whether path ends at target.
    """

    service_id: str
    is_routed: bool
    path_length: int
    starts_at_source: bool
    ends_at_target: bool


@dataclass(frozen=True)
class ServiceAssignmentConstraint:
    """服务路由约束 / Service assignment constraint.

    生成服务级路由约束数据。验证每条服务是否已被分配
    一条从源节点到目标节点的有效路径。
    Generates service-level routing constraint data. Verifies
    that each service has been assigned a valid path from
    source to target node.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "service_routing"

    def build_constraints(
        self,
        aggregation: RouteAggregation,
    ) -> tuple[ServiceRoutingStatus, ...]:
        """构建服务路由约束列表。

        Build the list of service routing constraints.

        遍历所有已注册服务，检查每条服务是否被分配了
        一条有效的从源到目标的路径。
        Iterates over all registered services, checking whether
        each has been assigned a valid source-to-target path.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            服务路由状态元组 / Tuple of service routing statuses.
        """
        results: list[ServiceRoutingStatus] = []
        for service in aggregation.services:
            assignment = aggregation.get_assignment(service.service_id)

            if assignment is None or not assignment.is_valid:
                results.append(
                    ServiceRoutingStatus(
                        service_id=service.service_id,
                        is_routed=False,
                        path_length=0,
                        starts_at_source=False,
                        ends_at_target=False,
                    )
                )
                continue

            starts_at_source = assignment.path[0] == service.source
            ends_at_target = assignment.path[-1] == service.target

            results.append(
                ServiceRoutingStatus(
                    service_id=service.service_id,
                    is_routed=starts_at_source and ends_at_target,
                    path_length=len(assignment.path),
                    starts_at_source=starts_at_source,
                    ends_at_target=ends_at_target,
                )
            )

        return tuple(results)

    def constraint_name(self, service_id: str) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            service_id: 服务标识 / Service identifier.

        Returns:
            约束名称字符串 / Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{service_id}"

    def is_feasible(self, aggregation: RouteAggregation) -> bool:
        """检查服务路由约束是否可行。

        Check whether service routing constraints are feasible.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            若所有服务均已有效路由则返回 True。
            True if all services have been validly routed.
        """
        return all(status.is_routed for status in self.build_constraints(aggregation))

    def unrouted_services(
        self,
        aggregation: RouteAggregation,
    ) -> tuple[ServiceRoutingStatus, ...]:
        """获取所有未路由的服务。

        Get all unrouted services.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            未路由服务状态元组 / Tuple of unrouted service statuses.
        """
        return tuple(
            status
            for status in self.build_constraints(aggregation)
            if not status.is_routed
        )
