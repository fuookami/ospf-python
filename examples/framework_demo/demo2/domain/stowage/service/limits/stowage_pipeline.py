"""装载管道 / Stowage pipeline.

将所有约束和目标组合为统一的评估管道。
Composes all constraints and objectives into a unified
evaluation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.stowage.model.stowage_result import (
    Penalty,
    StowageResult,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.access_constraint import (
    AccessConstraint,
    AccessPoint,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.compatibility_constraint import (
    CompatibilityConstraint,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.fragility_constraint import (
    FragilityConstraint,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.fuel_efficiency_objective import (
    FuelEfficiencyObjective,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.hazmat_segregation_constraint import (
    HazmatSegregationConstraint,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.loading_time_objective import (
    LoadingTimeObjective,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.max_volume_constraint import (
    MaxVolumeConstraint,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.max_weight_constraint import (
    MaxWeightConstraint,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.priority_constraint import (
    PriorityConstraint,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.sequence_constraint import (
    SequenceConstraint,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.space_utilization_objective import (
    SpaceUtilizationObjective,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.temperature_constraint import (
    TemperatureConstraint,
    TemperatureRequirement,
    TemperatureZone,
)
from examples.framework_demo.demo2.domain.stowage.service.limits.weight_distribution_objective import (
    WeightDistributionObjective,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.balance_limit import (
        BalanceLimit,
    )
    from examples.framework_demo.demo2.domain.stowage.model.compatibility_limit import (
        CompatibilityLimit,
    )
    from examples.framework_demo.demo2.domain.stowage.model.hazmat_limit import (
        HazmatLimit,
    )
    from examples.framework_demo.demo2.domain.stowage.model.sequence_limit import (
        SequenceLimit,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_compartment import (
        StowageCompartment,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_plan import (
        StowagePlan,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_position import (
        StowagePosition,
    )
    from examples.framework_demo.demo2.domain.stowage.service.limits.balance_constraint import (
        BalanceConstraint,
    )


@dataclass(frozen=True)
class PipelineConfig:
    """管道配置 / Pipeline configuration.

    控制管道中启用哪些约束和目标。
    Controls which constraints and objectives are enabled
    in the pipeline.

    Attributes:
        enable_weight: 启用重量约束 / Enable weight constraint.
        enable_volume: 启用容积约束 / Enable volume constraint.
        enable_balance: 启用平衡约束 / Enable balance constraint.
        enable_compatibility: 启用兼容性约束 /
            Enable compatibility constraint.
        enable_sequence: 启用顺序约束 / Enable sequence constraint.
        enable_hazmat: 启用危险品约束 / Enable hazmat constraint.
        enable_priority: 启用优先级约束 / Enable priority constraint.
        enable_fragility: 启用易碎品约束 / Enable fragility constraint.
        enable_temperature: 启用温度约束 / Enable temperature constraint.
        enable_access: 启用可达性约束 / Enable access constraint.
        enable_weight_distribution: 启用重量分布目标 /
            Enable weight distribution objective.
        enable_space_utilization: 启用空间利用目标 /
            Enable space utilization objective.
        enable_loading_time: 启用装载时间目标 /
            Enable loading time objective.
        enable_fuel_efficiency: 启用燃油效率目标 /
            Enable fuel efficiency objective.
    """

    enable_weight: bool = True
    """启用重量约束 / Enable weight constraint."""

    enable_volume: bool = True
    """启用容积约束 / Enable volume constraint."""

    enable_balance: bool = True
    """启用平衡约束 / Enable balance constraint."""

    enable_compatibility: bool = True
    """启用兼容性约束 / Enable compatibility constraint."""

    enable_sequence: bool = True
    """启用顺序约束 / Enable sequence constraint."""

    enable_hazmat: bool = True
    """启用危险品约束 / Enable hazmat constraint."""

    enable_priority: bool = True
    """启用优先级约束 / Enable priority constraint."""

    enable_fragility: bool = True
    """启用易碎品约束 / Enable fragility constraint."""

    enable_temperature: bool = True
    """启用温度约束 / Enable temperature constraint."""

    enable_access: bool = True
    """启用可达性约束 / Enable access constraint."""

    enable_weight_distribution: bool = True
    """启用重量分布目标 / Enable weight distribution objective."""

    enable_space_utilization: bool = True
    """启用空间利用目标 / Enable space utilization objective."""

    enable_loading_time: bool = True
    """启用装载时间目标 / Enable loading time objective."""

    enable_fuel_efficiency: bool = True
    """启用燃油效率目标 / Enable fuel efficiency objective."""


@dataclass(frozen=True)
class ObjectiveScores:
    """目标函数评分 / Objective function scores.

    记录各优化目标的评分。
    Records scores for each optimization objective.

    Attributes:
        weight_distribution: 重量分布评分 /
            Weight distribution score.
        space_utilization: 空间利用评分 /
            Space utilization score.
        loading_time: 装载时间评分 /
            Loading time score.
        fuel_efficiency: 燃油效率评分 /
            Fuel efficiency score.
        total: 总评分 / Total score.
    """

    weight_distribution: float = 0.0
    """重量分布评分 / Weight distribution score."""

    space_utilization: float = 0.0
    """空间利用评分 / Space utilization score."""

    loading_time: float = 0.0
    """装载时间评分 / Loading time score."""

    fuel_efficiency: float = 0.0
    """燃油效率评分 / Fuel efficiency score."""

    total: float = 0.0
    """总评分 / Total score."""


@dataclass(frozen=True)
class PipelineResult:
    """管道结果 / Pipeline result.

    封装管道评估的完整结果。
    Encapsulates the complete result of pipeline evaluation.

    Attributes:
        stowage_result: 装载结果 / Stowage result.
        objective_scores: 目标函数评分 / Objective scores.
    """

    stowage_result: StowageResult = None  # type: ignore[assignment]
    """装载结果 / Stowage result."""

    objective_scores: ObjectiveScores = ObjectiveScores()
    """目标函数评分 / Objective scores."""

    @property
    def is_feasible(self) -> bool:
        """是否可行。

        Whether the result is feasible.

        Returns:
            所有约束均满足时返回 True。
            True if all constraints are satisfied.
        """
        return self.stowage_result.is_feasible

    @property
    def total_score(self) -> float:
        """总评分。

        Total score.

        Returns:
            目标函数总评分。/ Total objective score.
        """
        return self.objective_scores.total


@dataclass(frozen=True)
class StowagePipeline:
    """装载管道 / Stowage pipeline.

    将所有约束和目标组合为统一的评估管道。按顺序执行
    各约束检查，收集违反信息，然后计算各目标函数评分。
    Composes all constraints and objectives into a unified
    evaluation pipeline. Executes constraint checks sequentially,
    collects violations, then computes objective scores.

    Attributes:
        config: 管道配置 / Pipeline configuration.
        weight_constraint: 重量约束 / Weight constraint.
        volume_constraint: 容积约束 / Volume constraint.
        balance_constraint: 平衡约束 / Balance constraint.
        compatibility_constraint: 兼容性约束 /
            Compatibility constraint.
        sequence_constraint: 顺序约束 / Sequence constraint.
        hazmat_constraint: 危险品约束 / Hazmat constraint.
        priority_constraint: 优先级约束 / Priority constraint.
        fragility_constraint: 易碎品约束 / Fragility constraint.
        temperature_constraint: 温度约束 / Temperature constraint.
        access_constraint: 可达性约束 / Access constraint.
        weight_distribution: 重量分布目标 /
            Weight distribution objective.
        space_utilization: 空间利用目标 /
            Space utilization objective.
        loading_time: 装载时间目标 / Loading time objective.
        fuel_efficiency: 燃油效率目标 / Fuel efficiency objective.
    """

    config: PipelineConfig = field(
        default_factory=PipelineConfig,
    )
    """管道配置 / Pipeline configuration."""

    weight_constraint: MaxWeightConstraint = field(
        default_factory=MaxWeightConstraint,
    )
    """重量约束 / Weight constraint."""

    volume_constraint: MaxVolumeConstraint = field(
        default_factory=MaxVolumeConstraint,
    )
    """容积约束 / Volume constraint."""

    balance_constraint: BalanceConstraint | None = None
    """平衡约束 / Balance constraint."""

    compatibility_constraint: CompatibilityConstraint = field(
        default_factory=CompatibilityConstraint,
    )
    """兼容性约束 / Compatibility constraint."""

    sequence_constraint: SequenceConstraint = field(
        default_factory=SequenceConstraint,
    )
    """顺序约束 / Sequence constraint."""

    hazmat_constraint: HazmatSegregationConstraint = field(
        default_factory=HazmatSegregationConstraint,
    )
    """危险品约束 / Hazmat constraint."""

    priority_constraint: PriorityConstraint = field(
        default_factory=PriorityConstraint,
    )
    """优先级约束 / Priority constraint."""

    fragility_constraint: FragilityConstraint = field(
        default_factory=FragilityConstraint,
    )
    """易碎品约束 / Fragility constraint."""

    temperature_constraint: TemperatureConstraint = field(
        default_factory=TemperatureConstraint,
    )
    """温度约束 / Temperature constraint."""

    access_constraint: AccessConstraint = field(
        default_factory=AccessConstraint,
    )
    """可达性约束 / Access constraint."""

    weight_distribution: WeightDistributionObjective = field(
        default_factory=WeightDistributionObjective,
    )
    """重量分布目标 / Weight distribution objective."""

    space_utilization: SpaceUtilizationObjective = field(
        default_factory=SpaceUtilizationObjective,
    )
    """空间利用目标 / Space utilization objective."""

    loading_time: LoadingTimeObjective = field(
        default_factory=LoadingTimeObjective,
    )
    """装载时间目标 / Loading time objective."""

    fuel_efficiency: FuelEfficiencyObjective = field(
        default_factory=FuelEfficiencyObjective,
    )
    """燃油效率目标 / Fuel efficiency objective."""

    def evaluate(
        self,
        *,
        plan: StowagePlan,
        compartments: tuple[StowageCompartment, ...],
        items: tuple[StowageItem, ...],
        positions: dict[str, StowagePosition],
        assignments: dict[str, tuple[str, ...]],
        compatibility_limits: tuple[CompatibilityLimit, ...] = (),
        sequence_limits: tuple[SequenceLimit, ...] = (),
        hazmat_limits: tuple[HazmatLimit, ...] = (),
        balance_limits: tuple[BalanceLimit, ...] = (),
        temperature_requirements: tuple[TemperatureRequirement, ...] = (),
        temperature_zones: tuple[TemperatureZone, ...] = (),
        access_points: tuple[AccessPoint, ...] = (),
        loading_order: dict[str, int] | None = None,
    ) -> PipelineResult:
        """执行管道评估。

        Execute pipeline evaluation.

        Args:
            plan: 装载方案。/ Stowage plan.
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            positions: 货物位置映射。/ Item position mapping.
            assignments: 分配映射。/ Assignment mapping.
            compatibility_limits: 兼容性限制。/
                Compatibility limits.
            sequence_limits: 顺序限制。/ Sequence limits.
            hazmat_limits: 危险品限制。/ Hazmat limits.
            balance_limits: 平衡限制。/ Balance limits.
            temperature_requirements: 温度需求。/
                Temperature requirements.
            temperature_zones: 温控区域。/ Temperature zones.
            access_points: 可达点。/ Access points.
            loading_order: 装载顺序。/ Loading order.

        Returns:
            管道评估结果。/ Pipeline evaluation result.
        """
        penalties: list[Penalty] = []
        effective_order = loading_order or {}

        if self.config.enable_weight:
            weight_violations = self.weight_constraint.check_compartments(
                compartments=compartments,
                items=items,
                assignments=assignments,
            )
            for v in weight_violations:
                penalties.append(
                    Penalty(
                        constraint_type="max_weight",
                        penalty_value=v.excess,
                        description=(
                            f"Compartment {v.compartment_id} "
                            f"exceeds weight by {v.excess:.1f} kg"
                        ),
                    )
                )

        if self.config.enable_volume:
            volume_violations = self.volume_constraint.check_compartments(
                compartments=compartments,
                items=items,
                assignments=assignments,
            )
            for vv in volume_violations:
                penalties.append(
                    Penalty(
                        constraint_type="max_volume",
                        penalty_value=vv.excess,
                        description=(
                            f"Compartment {vv.compartment_id} "
                            f"exceeds volume by "
                            f"{vv.excess:.2f} m3"
                        ),
                    )
                )

        if self.config.enable_compatibility:
            compat_violations = self.compatibility_constraint.check_assignments(
                limits=compatibility_limits,
                items=items,
                assignments=assignments,
            )
            for cv in compat_violations:
                penalties.append(
                    Penalty(
                        constraint_type="compatibility",
                        penalty_value=100.0,
                        description=(
                            f"Incompatible items "
                            f"{cv.item_a} and {cv.item_b} "
                            f"in compartment {cv.compartment_id}"
                        ),
                    )
                )

        if self.config.enable_sequence and effective_order:
            seq_violations = self.sequence_constraint.check_sequence(
                limits=sequence_limits,
                loading_order=effective_order,
            )
            for sv in seq_violations:
                penalties.append(
                    Penalty(
                        constraint_type="sequence",
                        penalty_value=50.0,
                        description=(
                            f"Sequence violation: "
                            f"{sv.violated_limit.item_a} "
                            f"should be "
                            f"{sv.violated_limit.order} "
                            f"{sv.violated_limit.item_b}"
                        ),
                    )
                )

        if self.config.enable_hazmat:
            hazmat_violations = self.hazmat_constraint.check_segregation(
                limits=hazmat_limits,
                positions=positions,
            )
            for hv in hazmat_violations:
                penalties.append(
                    Penalty(
                        constraint_type="hazmat_segregation",
                        penalty_value=hv.deficit * 10.0,
                        description=(
                            f"Hazmat items {hv.item_a} and "
                            f"{hv.item_b} too close: "
                            f"{hv.actual_distance:.1f}m < "
                            f"{hv.required_distance:.1f}m"
                        ),
                    )
                )

        if self.config.enable_priority and effective_order:
            priority_violations = self.priority_constraint.check_order(
                items=items,
                loading_order=effective_order,
            )
            for pv in priority_violations:
                penalties.append(
                    Penalty(
                        constraint_type="priority",
                        penalty_value=30.0,
                        description=(
                            f"Priority violation: "
                            f"{pv.higher_item} should load "
                            f"before {pv.lower_item}"
                        ),
                    )
                )

        if self.config.enable_fragility:
            fragility_violations = self.fragility_constraint.check_stacking(
                items=items,
                positions=positions,
            )
            for fv in fragility_violations:
                penalties.append(
                    Penalty(
                        constraint_type="fragility",
                        penalty_value=fv.pressure_ratio * 20.0,
                        description=(
                            f"Fragile item {fv.fragile_item} "
                            f"under {fv.heavy_item}, "
                            f"pressure ratio "
                            f"{fv.pressure_ratio:.2f}"
                        ),
                    )
                )

        if self.config.enable_temperature:
            temp_assignments = {
                item_id: comp_id
                for comp_id, ids in assignments.items()
                for item_id in ids
            }
            temp_violations = self.temperature_constraint.check_assignments(
                requirements=temperature_requirements,
                zones=temperature_zones,
                assignments=temp_assignments,
            )
            for tv in temp_violations:
                penalties.append(
                    Penalty(
                        constraint_type="temperature",
                        penalty_value=80.0,
                        description=(
                            f"Item {tv.item_id} in "
                            f"compartment {tv.compartment_id} "
                            f"has incompatible temperature"
                        ),
                    )
                )

        if self.config.enable_access:
            access_violations = self.access_constraint.check_access(
                access_points=access_points,
                positions=positions,
            )
            for av in access_violations:
                penalties.append(
                    Penalty(
                        constraint_type="access",
                        penalty_value=av.blocking_amount * 15.0,
                        description=(
                            f"Item {av.item_id} blocks "
                            f"access point "
                            f"{av.access_point.point_id}"
                        ),
                    )
                )

        feasibility = 1.0 if not penalties else 0.0
        result = StowageResult(
            plan=plan,
            feasibility=feasibility,
            penalties=tuple(penalties),
        )

        objective_scores = self._compute_objectives(
            items=items,
            positions=positions,
            compartments=compartments,
            assignments=assignments,
        )

        return PipelineResult(
            stowage_result=result,
            objective_scores=objective_scores,
        )

    def _compute_objectives(
        self,
        *,
        items: tuple[StowageItem, ...],
        positions: dict[str, StowagePosition],
        compartments: tuple[StowageCompartment, ...],
        assignments: dict[str, tuple[str, ...]],
    ) -> ObjectiveScores:
        """计算各目标函数评分。

        Compute objective function scores.

        Args:
            items: 货物列表。/ Item list.
            positions: 货物位置映射。/ Item position mapping.
            compartments: 货舱列表。/ Compartment list.
            assignments: 分配映射。/ Assignment mapping.

        Returns:
            目标函数评分。/ Objective scores.
        """
        wd_score = 0.0
        su_score = 0.0
        lt_score = 0.0
        fe_score = 0.0

        item_placements = tuple(
            (item, positions[item.item_id])
            for item in items
            if item.item_id in positions
        )

        if self.config.enable_weight_distribution:
            wd_score = self.weight_distribution.calculate_imbalance(
                item_placements,
            )

        if self.config.enable_space_utilization:
            su_score = self.space_utilization.calculate_utilization(
                compartments=compartments,
                items=items,
                assignments=assignments,
            )

        if self.config.enable_loading_time:
            lt_score = self.loading_time.calculate_total_time(
                items=items,
                positions=positions,
                compartments=compartments,
            )

        if self.config.enable_fuel_efficiency:
            fe_score = self.fuel_efficiency.calculate_total_impact(
                item_placements,
            )

        total = wd_score + (1.0 - su_score) + lt_score + fe_score

        return ObjectiveScores(
            weight_distribution=wd_score,
            space_utilization=su_score,
            loading_time=lt_score,
            fuel_efficiency=fe_score,
            total=total,
        )

    def check_all_feasible(
        self,
        *,
        compartments: tuple[StowageCompartment, ...],
        items: tuple[StowageItem, ...],
        positions: dict[str, StowagePosition],
        assignments: dict[str, tuple[str, ...]],
        compatibility_limits: tuple[CompatibilityLimit, ...] = (),
        sequence_limits: tuple[SequenceLimit, ...] = (),
        hazmat_limits: tuple[HazmatLimit, ...] = (),
        loading_order: dict[str, int] | None = None,
    ) -> bool:
        """快速检查所有约束是否可行。

        Quick check whether all constraints are feasible.

        Args:
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            positions: 货物位置映射。/ Item position mapping.
            assignments: 分配映射。/ Assignment mapping.
            compatibility_limits: 兼容性限制。/
                Compatibility limits.
            sequence_limits: 顺序限制。/ Sequence limits.
            hazmat_limits: 危险品限制。/ Hazmat limits.
            loading_order: 装载顺序。/ Loading order.

        Returns:
            所有约束均满足时返回 True。
            True if all constraints are satisfied.
        """
        if not self.weight_constraint.is_feasible(
            compartments=compartments,
            items=items,
            assignments=assignments,
        ):
            return False

        if not self.volume_constraint.is_feasible(
            compartments=compartments,
            items=items,
            assignments=assignments,
        ):
            return False

        if not self.compatibility_constraint.is_feasible(
            limits=compatibility_limits,
            items=items,
            assignments=assignments,
        ):
            return False

        effective_order = loading_order or {}
        if effective_order and not self.sequence_constraint.is_feasible(
            limits=sequence_limits,
            loading_order=effective_order,
        ):
            return False

        if not self.hazmat_constraint.is_feasible(
            limits=hazmat_limits,
            positions=positions,
        ):
            return False

        if effective_order and not self.priority_constraint.is_feasible(
            items=items,
            loading_order=effective_order,
        ):
            return False

        return self.fragility_constraint.is_feasible(items=items, positions=positions)
