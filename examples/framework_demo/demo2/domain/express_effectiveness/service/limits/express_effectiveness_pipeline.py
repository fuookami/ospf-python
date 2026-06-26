"""快递效能评估流水线。

Express effectiveness pipeline composing delivery constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.express_metric import ExpressMetric
from ...model.express_result import ExpressResult

if TYPE_CHECKING:
    from .express_cost_objective import ExpressCostObjective, ExpressCostShipment
    from .priority_mixing_constraint import (
        PriorityMixingConstraint,
        PriorityMixingShipment,
    )
    from .time_window_constraint import TimeWindowConstraint, TimeWindowShipment


@dataclass(frozen=True)
class ExpressPipelineInput:
    """快递流水线输入数据。

    Aggregates all input data for the express effectiveness pipeline.

    Attributes:
        time_shipments: 时间窗快件数据 / Time window shipment data
        mixing_shipments: 混装快件数据 / Priority mixing shipment data
        cost_shipments: 成本快件数据 / Cost shipment data
    """

    time_shipments: tuple[TimeWindowShipment, ...]
    mixing_shipments: tuple[PriorityMixingShipment, ...]
    cost_shipments: tuple[ExpressCostShipment, ...]


@dataclass(frozen=True)
class ExpressEffectivenessPipeline:
    """快递效能评估流水线。

    Composes time window, priority mixing, and cost constraints
    into a unified evaluation pipeline.

    Attributes:
        time_constraint: 时间窗约束 / Time window constraint
        mixing_constraint: 混装约束 / Priority mixing constraint
        cost_objective: 成本目标 / Cost objective
        min_score: 最低通过分数 / Minimum passing score
    """

    time_constraint: TimeWindowConstraint
    mixing_constraint: PriorityMixingConstraint
    cost_objective: ExpressCostObjective
    min_score: float

    def evaluate(self, data: ExpressPipelineInput) -> ExpressResult:
        """执行完整效能评估。

        Runs all constraints and objectives and produces the final result.

        Args:
            data: 流水线输入数据 / Pipeline input data

        Returns:
            ExpressResult: 评估结果 / Evaluation result
        """
        metrics: list[ExpressMetric] = []
        all_feasible = True

        # --- 时间窗约束 ---
        time_ok, _ = self.time_constraint.evaluate(data.time_shipments)
        on_time_rate = self.time_constraint.on_time_rate(data.time_shipments)
        metrics.append(
            ExpressMetric(
                metric_name="time_window_compliance",
                value=1.0 if time_ok else on_time_rate,
                target=1.0,
            )
        )
        if not time_ok:
            all_feasible = False

        # --- 优先级混装约束 ---
        mixing_ok, _ = self.mixing_constraint.evaluate(data.mixing_shipments)
        metrics.append(
            ExpressMetric(
                metric_name="priority_segregation",
                value=1.0 if mixing_ok else 0.0,
                target=1.0,
            )
        )
        if not mixing_ok:
            all_feasible = False

        # --- 成本目标 ---
        total_cost, cost_score = self.cost_objective.compute_total(
            data.cost_shipments,
        )
        within_budget = self.cost_objective.is_within_budget(data.cost_shipments)
        metrics.append(
            ExpressMetric(
                metric_name="cost_efficiency",
                value=cost_score / max(self.cost_objective.weight, 0.001),
                target=0.8,
            )
        )
        if not within_budget:
            all_feasible = False

        # --- 计算预计配送时间 ---
        if data.time_shipments:
            avg_time = sum(s.estimated_time for s in data.time_shipments) / len(
                data.time_shipments
            )
        else:
            avg_time = 0.0

        return ExpressResult.from_metrics(
            tuple(metrics),
            time_estimate=avg_time,
            feasible=all_feasible,
        )

    def summary(self, data: ExpressPipelineInput, result: ExpressResult) -> str:
        """生成评估摘要。

        Args:
            data: 输入数据 / Input data
            result: 评估结果 / Evaluation result

        Returns:
            str: 摘要文本 / Summary text
        """
        status = "通过" if result.is_passing(self.min_score) else "未通过"
        total_cost, _ = self.cost_objective.compute_total(data.cost_shipments)
        on_time = self.time_constraint.on_time_rate(data.time_shipments)
        return (
            f"快递效能评估: {status} | 得分: {result.score:.2f} | "
            f"预计 {result.time_estimate:.1f}h | "
            f"准时率 {on_time:.1%} | 成本 {total_cost:.0f}元"
        )
