"""Pipeline list generator — 管道列表生成器。

为路由上下文生成约束和目标管道列表，供优化模型注册使用。
Generates constraint and objective pipeline lists for the
route context, used for optimization model registration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .limits.node_assignment_constraint import NodeAssignmentConstraint
from .limits.service_assignment_constraint import ServiceAssignmentConstraint
from .limits.service_cost_objective import ServiceCostObjective

if TYPE_CHECKING:
    from .aggregation import RouteAggregation


@dataclass(frozen=True)
class PipelineEntry:
    """管道条目 / Pipeline entry.

    表示约束或目标管道中的一个条目。
    Represents a single entry in a constraint or objective pipeline.

    Attributes:
        name: 条目名称 / Entry name.
        kind: 条目类型（constraint 或 objective） /
            Entry kind (constraint or objective).
        priority: 执行优先级（越小越先执行） /
            Execution priority (lower = earlier).
    """

    name: str
    kind: str
    priority: int = 0


@dataclass(frozen=True)
class PipelineListGenerator:
    """管道列表生成器 / Pipeline list generator.

    根据路由聚合状态生成约束和目标管道列表。
    约束包括流守恒约束和服务路由约束；
    目标为最小化总路由代价。
    Generates constraint and objective pipeline lists based
    on route aggregation state. Constraints include flow
    conservation and service routing; the objective is to
    minimize total routing cost.

    Attributes:
        enable_flow_conservation: 是否启用流守恒约束 /
            Whether to enable flow conservation constraints.
        enable_service_routing: 是否启用服务路由约束 /
            Whether to enable service routing constraints.
        enable_cost_objective: 是否启用代价目标 /
            Whether to enable cost objective.
    """

    enable_flow_conservation: bool = True
    enable_service_routing: bool = True
    enable_cost_objective: bool = True

    def generate_entries(self) -> tuple[PipelineEntry, ...]:
        """生成管道条目列表。

        Generate the pipeline entry list.

        根据配置生成约束和目标条目，按优先级排序。
        Generates constraint and objective entries based on
        configuration, sorted by priority.

        Returns:
            管道条目元组 / Tuple of pipeline entries.
        """
        entries: list[PipelineEntry] = []

        if self.enable_flow_conservation:
            entries.append(
                PipelineEntry(
                    name=NodeAssignmentConstraint().constraint_name_prefix,
                    kind="constraint",
                    priority=10,
                )
            )

        if self.enable_service_routing:
            entries.append(
                PipelineEntry(
                    name=ServiceAssignmentConstraint().constraint_name_prefix,
                    kind="constraint",
                    priority=20,
                )
            )

        if self.enable_cost_objective:
            entries.append(
                PipelineEntry(
                    name=ServiceCostObjective().objective_name,
                    kind="objective",
                    priority=100,
                )
            )

        return tuple(sorted(entries, key=lambda e: e.priority))

    def constraint_entries(self) -> tuple[PipelineEntry, ...]:
        """获取约束管道条目。

        Get constraint pipeline entries.

        Returns:
            约束条目元组 / Tuple of constraint entries.
        """
        return tuple(e for e in self.generate_entries() if e.kind == "constraint")

    def objective_entries(self) -> tuple[PipelineEntry, ...]:
        """获取目标管道条目。

        Get objective pipeline entries.

        Returns:
            目标条目元组 / Tuple of objective entries.
        """
        return tuple(e for e in self.generate_entries() if e.kind == "objective")

    def validate_aggregation(
        self,
        aggregation: RouteAggregation,
    ) -> tuple[str, ...]:
        """验证聚合状态是否满足管道要求。

        Validate that aggregation state meets pipeline requirements.

        检查图是否非空、是否有服务注册。
        Checks that graph is non-empty and services are registered.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            验证错误消息元组，空表示通过。
            Tuple of validation error messages, empty means passed.
        """
        errors: list[str] = []

        if not aggregation.graph.nodes:
            errors.append(
                "图为空，至少需要一个节点 / Graph is empty, at least one node required"
            )

        if not aggregation.services:
            errors.append(
                "未注册服务，至少需要一条服务 / No services registered, at least one required"
            )

        if self.enable_flow_conservation and not aggregation.assignments:
            errors.append(
                "启用流守恒约束但无分配 / Flow conservation enabled but no assignments"
            )

        return tuple(errors)
