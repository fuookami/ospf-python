"""装箱效能评估流水线。

Loading effectiveness pipeline composing all constraints and objectives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.loading_effectiveness_result import LoadingEffectivenessResult
from ...model.loading_metric import LoadingMetric

if TYPE_CHECKING:
    from ...model.compartment_loading import CompartmentLoading
    from ...model.effectiveness_threshold import EffectivenessThreshold
    from .access_sequence_constraint import AccessSequenceConstraint, AccessSequenceItem
    from .center_of_gravity_constraint import CenterOfGravityConstraint, CGItem
    from .hazmat_distance_constraint import HazmatDistanceConstraint, HazmatItem
    from .priority_constraint import PriorityConstraint, PriorityItem
    from .space_utilization_objective import SpaceUtilizationObjective
    from .stacking_constraint import StackingConstraint, StackingItem
    from .temperature_zone_constraint import TemperatureItem, TemperatureZoneConstraint
    from .volume_constraint import VolumeConstraint
    from .weight_balance_constraint import WeightBalanceConstraint
    from .weight_balance_objective import WeightBalanceObjective


@dataclass(frozen=True)
class PipelineInput:
    """流水线输入数据。

    Aggregates all input data needed by the loading effectiveness pipeline.

    Attributes:
        compartments: 各舱室装载状态 / Compartment loading states
        stacking_items: 堆码物品信息 / Stacking item data
        hazmat_items: 危险品信息 / Hazmat item data
        temp_items: 温控物品信息 / Temperature item data
        priority_items: 优先级物品信息 / Priority item data
        sequence_items: 卸载顺序物品信息 / Access sequence item data
        cg_items: 重心物品信息 / CG item data
    """

    compartments: tuple[CompartmentLoading, ...]
    stacking_items: tuple[StackingItem, ...]
    hazmat_items: tuple[HazmatItem, ...]
    temp_items: tuple[TemperatureItem, ...]
    priority_items: tuple[PriorityItem, ...]
    sequence_items: tuple[AccessSequenceItem, ...]
    cg_items: tuple[CGItem, ...]


@dataclass(frozen=True)
class LoadingEffectivenessPipeline:
    """装箱效能评估流水线。

    Composes all constraints and objectives into a single evaluation
    pipeline that produces a comprehensive effectiveness result.

    Attributes:
        volume_constraint: 体积约束 / Volume constraint
        weight_balance_constraint: 重量平衡约束 / Weight balance constraint
        stacking_constraint: 堆码约束 / Stacking constraint
        access_constraint: 卸载顺序约束 / Access sequence constraint
        hazmat_constraint: 危险品距离约束 / Hazmat distance constraint
        temp_constraint: 温区隔离约束 / Temperature zone constraint
        priority_constraint: 优先级约束 / Priority constraint
        cg_constraint: 重心约束 / CG constraint
        space_objective: 空间利用率目标 / Space utilization objective
        weight_objective: 重量平衡目标 / Weight balance objective
        threshold: 效能阈值 / Effectiveness threshold
    """

    volume_constraint: VolumeConstraint
    weight_balance_constraint: WeightBalanceConstraint
    stacking_constraint: StackingConstraint
    access_constraint: AccessSequenceConstraint
    hazmat_constraint: HazmatDistanceConstraint
    temp_constraint: TemperatureZoneConstraint
    priority_constraint: PriorityConstraint
    cg_constraint: CenterOfGravityConstraint
    space_objective: SpaceUtilizationObjective
    weight_objective: WeightBalanceObjective
    threshold: EffectivenessThreshold

    def evaluate(self, data: PipelineInput) -> LoadingEffectivenessResult:
        """执行完整效能评估。

        Runs all constraints and objectives, collects metrics,
        and produces the final effectiveness result.

        Args:
            data: 流水线输入数据 / Pipeline input data

        Returns:
            LoadingEffectivenessResult: 评估结果 / Evaluation result
        """
        metrics: list[LoadingMetric] = []
        all_feasible = True

        # --- 约束评估 ---
        vol_ok, _ = self.volume_constraint.evaluate(data.compartments)
        metrics.append(
            LoadingMetric(
                metric_name="volume_compliance",
                value=1.0 if vol_ok else 0.0,
                weight=0.15,
                target=1.0,
            )
        )
        if not vol_ok:
            all_feasible = False

        bal_ok, distribution = self.weight_balance_constraint.evaluate(
            data.compartments,
        )
        metrics.append(
            LoadingMetric(
                metric_name="weight_balance",
                value=min(
                    distribution.lateral_balance, distribution.longitudinal_balance
                ),
                weight=0.15,
                target=1.0 - self.weight_balance_constraint.max_lateral_imbalance,
            )
        )
        if not bal_ok:
            all_feasible = False

        stack_ok, _ = self.stacking_constraint.evaluate(data.stacking_items)
        metrics.append(
            LoadingMetric(
                metric_name="stacking_compliance",
                value=1.0 if stack_ok else 0.0,
                weight=0.10,
                target=1.0,
            )
        )
        if not stack_ok:
            all_feasible = False

        access_ok, _ = self.access_constraint.evaluate(data.sequence_items)
        metrics.append(
            LoadingMetric(
                metric_name="access_sequence",
                value=1.0 if access_ok else 0.0,
                weight=0.10,
                target=1.0,
            )
        )
        if not access_ok:
            all_feasible = False

        hazmat_ok, _ = self.hazmat_constraint.evaluate(data.hazmat_items)
        metrics.append(
            LoadingMetric(
                metric_name="hazmat_distance",
                value=1.0 if hazmat_ok else 0.0,
                weight=0.10,
                target=1.0,
            )
        )
        if not hazmat_ok:
            all_feasible = False

        temp_ok, _ = self.temp_constraint.evaluate(data.temp_items)
        metrics.append(
            LoadingMetric(
                metric_name="temperature_zone",
                value=1.0 if temp_ok else 0.0,
                weight=0.10,
                target=1.0,
            )
        )
        if not temp_ok:
            all_feasible = False

        prio_ok, _ = self.priority_constraint.evaluate(data.priority_items)
        metrics.append(
            LoadingMetric(
                metric_name="priority_order",
                value=1.0 if prio_ok else 0.0,
                weight=0.05,
                target=1.0,
            )
        )
        if not prio_ok:
            all_feasible = False

        cg_ok, _ = self.cg_constraint.evaluate(data.cg_items)
        metrics.append(
            LoadingMetric(
                metric_name="center_of_gravity",
                value=1.0 if cg_ok else 0.0,
                weight=0.10,
                target=1.0,
            )
        )
        if not cg_ok:
            all_feasible = False

        # --- 目标评估 ---
        _, space_score = self.space_objective.compute(data.compartments)
        metrics.append(
            LoadingMetric(
                metric_name="space_utilization",
                value=space_score / max(self.space_objective.weight, 0.001),
                weight=0.10,
                target=0.9,
            )
        )

        _, balance_score = self.weight_objective.compute(data.compartments)
        metrics.append(
            LoadingMetric(
                metric_name="weight_balance_score",
                value=balance_score / max(self.weight_objective.weight, 0.001),
                weight=0.05,
                target=0.95,
            )
        )

        return LoadingEffectivenessResult.from_metrics(
            tuple(metrics),
            feasible=all_feasible,
        )
