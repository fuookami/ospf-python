"""管道列表生成器 / Pipeline list generator.

生成带宽约束评估的约束管道列表。
Generates constraint pipeline lists for bandwidth constraint evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from examples.framework_demo.demo1.bandwidth_context.limits.bandwidth_cost_objective import (
    BandwidthCostObjective,
)
from examples.framework_demo.demo1.bandwidth_context.limits.demand_constraint import (
    DemandConstraint,
)
from examples.framework_demo.demo1.bandwidth_context.limits.edge_bandwidth_constraint import (
    EdgeBandwidthConstraint,
)
from examples.framework_demo.demo1.bandwidth_context.limits.service_capacity_constraint import (
    ServiceCapacityConstraint,
)
from examples.framework_demo.demo1.bandwidth_context.limits.transfer_node_bandwidth_constraint import (
    TransferNodeBandwidthConstraint,
)


@dataclass(frozen=True)
class PipelineConfig:
    """管道配置 / Pipeline configuration.

    控制管道中启用哪些约束和目标。
    Controls which constraints and objectives are enabled
    in the pipeline.

    Attributes:
        enable_demand: 启用需求约束 / Enable demand constraint.
        enable_edge_bandwidth: 启用边带宽约束 /
            Enable edge bandwidth constraint.
        enable_service_capacity: 启用服务容量约束 /
            Enable service capacity constraint.
        enable_transfer_node: 启用中转节点约束 /
            Enable transfer node constraint.
        enable_cost_objective: 启用成本目标 /
            Enable cost objective.
    """

    enable_demand: bool = True
    """启用需求约束 / Enable demand constraint."""

    enable_edge_bandwidth: bool = True
    """启用边带宽约束 / Enable edge bandwidth constraint."""

    enable_service_capacity: bool = True
    """启用服务容量约束 / Enable service capacity constraint."""

    enable_transfer_node: bool = True
    """启用中转节点约束 / Enable transfer node constraint."""

    enable_cost_objective: bool = True
    """启用成本目标 / Enable cost objective."""


@dataclass(frozen=True)
class PipelineEntry:
    """管道条目 / Pipeline entry.

    表示管道中的一个约束或目标条目。
    Represents a constraint or objective entry in the pipeline.

    Attributes:
        name: 条目名称 / Entry name.
        entry_type: 条目类型（constraint/objective）/
            Entry type (constraint/objective).
        enabled: 是否启用 / Whether enabled.
    """

    name: str = ""
    """条目名称 / Entry name."""

    entry_type: str = ""
    """条目类型（constraint/objective）/ Entry type."""

    enabled: bool = True
    """是否启用 / Whether enabled."""


@dataclass(frozen=True)
class PipelineListGenerator:
    """管道列表生成器 / Pipeline list generator.

    根据配置生成约束和目标的管道列表，用于统一的
    评估流程编排。
    Generates a pipeline list of constraints and objectives
    based on configuration, for unified evaluation orchestration.

    Attributes:
        config: 管道配置 / Pipeline configuration.
        demand_constraint: 需求约束 / Demand constraint.
        edge_bw_constraint: 边带宽约束 / Edge bandwidth constraint.
        svc_cap_constraint: 服务容量约束 /
            Service capacity constraint.
        transfer_node_constraint: 中转节点约束 /
            Transfer node constraint.
        cost_objective: 成本目标 / Cost objective.
    """

    config: PipelineConfig = field(
        default_factory=PipelineConfig,
    )
    """管道配置 / Pipeline configuration."""

    demand_constraint: DemandConstraint = field(
        default_factory=DemandConstraint,
    )
    """需求约束 / Demand constraint."""

    edge_bw_constraint: EdgeBandwidthConstraint = field(
        default_factory=EdgeBandwidthConstraint,
    )
    """边带宽约束 / Edge bandwidth constraint."""

    svc_cap_constraint: ServiceCapacityConstraint = field(
        default_factory=ServiceCapacityConstraint,
    )
    """服务容量约束 / Service capacity constraint."""

    transfer_node_constraint: TransferNodeBandwidthConstraint = field(
        default_factory=TransferNodeBandwidthConstraint,
    )
    """中转节点约束 / Transfer node constraint."""

    cost_objective: BandwidthCostObjective = field(
        default_factory=BandwidthCostObjective,
    )
    """成本目标 / Cost objective."""

    def generate_pipeline_entries(self) -> tuple[PipelineEntry, ...]:
        """生成管道条目列表。

        Generate pipeline entry list.

        Returns:
            管道条目元组。/ Tuple of pipeline entries.
        """
        entries: list[PipelineEntry] = []
        entries.append(
            PipelineEntry(
                name=self.demand_constraint.constraint_name_prefix,
                entry_type="constraint",
                enabled=self.config.enable_demand,
            )
        )
        entries.append(
            PipelineEntry(
                name=self.edge_bw_constraint.constraint_name_prefix,
                entry_type="constraint",
                enabled=self.config.enable_edge_bandwidth,
            )
        )
        entries.append(
            PipelineEntry(
                name=self.svc_cap_constraint.constraint_name_prefix,
                entry_type="constraint",
                enabled=self.config.enable_service_capacity,
            )
        )
        entries.append(
            PipelineEntry(
                name=self.transfer_node_constraint.constraint_name_prefix,
                entry_type="constraint",
                enabled=self.config.enable_transfer_node,
            )
        )
        entries.append(
            PipelineEntry(
                name=self.cost_objective.objective_name,
                entry_type="objective",
                enabled=self.config.enable_cost_objective,
            )
        )
        return tuple(entries)

    def enabled_constraints(self) -> tuple[PipelineEntry, ...]:
        """获取已启用的约束条目。

        Get enabled constraint entries.

        Returns:
            已启用的约束条目元组。
            Tuple of enabled constraint entries.
        """
        return tuple(
            e
            for e in self.generate_pipeline_entries()
            if e.enabled and e.entry_type == "constraint"
        )

    def enabled_objectives(self) -> tuple[PipelineEntry, ...]:
        """获取已启用的目标条目。

        Get enabled objective entries.

        Returns:
            已启用的目标条目元组。
            Tuple of enabled objective entries.
        """
        return tuple(
            e
            for e in self.generate_pipeline_entries()
            if e.enabled and e.entry_type == "objective"
        )

    def pipeline_summary(self) -> dict[str, int]:
        """生成管道摘要。

        Generate pipeline summary.

        Returns:
            包含约束数、目标数和总数的摘要字典。
            Summary dict with constraint count, objective count,
            and total count.
        """
        entries = self.generate_pipeline_entries()
        constraints = sum(
            1 for e in entries if e.enabled and e.entry_type == "constraint"
        )
        objectives = sum(
            1 for e in entries if e.enabled and e.entry_type == "objective"
        )
        return {
            "total": len(entries),
            "enabled_constraints": constraints,
            "enabled_objectives": objectives,
            "disabled": len(entries) - constraints - objectives,
        }
