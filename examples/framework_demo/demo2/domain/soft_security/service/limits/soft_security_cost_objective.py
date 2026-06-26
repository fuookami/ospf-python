"""软安全成本优化目标 / Soft security cost objective.

在满足安全要求的前提下最小化安全措施总成本。
Minimizes total security measure cost while meeting
security requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.soft_security_measure import MeasureType, SoftSecurityMeasure


@dataclass(frozen=True)
class CostWeight:
    """成本权重 / Cost weight.

    按措施类型设置成本优化权重。
    Sets cost optimization weight by measure type.

    Attributes:
        measure_type: 措施类型 / Measure type.
        weight: 成本权重系数 / Cost weight factor.
    """

    measure_type: MeasureType
    weight: float = 1.0


@dataclass(frozen=True)
class SoftSecurityCostObjective:
    """软安全成本优化目标 / Soft security cost objective.

    计算所有安全措施的加权总成本，支持按措施类型分配
    不同的权重系数，供优化器最小化。
    Computes the weighted total cost of all security measures,
    supporting different weight factors per measure type,
    for minimization by the optimizer.

    Attributes:
        cost_weights: 各类型成本权重 /
            Cost weights per measure type.
        target_cost: 目标成本上限 /
            Target cost ceiling.
        weight: 目标在总评分中的权重 /
            Objective weight in overall scoring.
    """

    cost_weights: tuple[CostWeight, ...] = ()
    target_cost: float = 10000.0
    weight: float = 0.1

    def compute(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> tuple[float, float]:
        """计算加权总成本和得分。

        Compute weighted total cost and score.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            tuple: (加权总成本, 加权得分) /
                (weighted total cost, weighted score).
        """
        weight_map = {cw.measure_type: cw.weight for cw in self.cost_weights}
        active = [m for m in measures if m.active]
        total = sum(m.cost * weight_map.get(m.measure_type, 1.0) for m in active)
        if self.target_cost <= 0.0:
            score = 0.0
        else:
            ratio = min(total / self.target_cost, 2.0)
            score = max(0.0, 1.0 - ratio) * self.weight
        return (total, score)

    def cost_breakdown(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> dict[MeasureType, float]:
        """按类型分解成本 / Cost breakdown by type.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            措施类型到成本的映射。
            Mapping of measure type to cost.
        """
        weight_map = {cw.measure_type: cw.weight for cw in self.cost_weights}
        breakdown: dict[MeasureType, float] = {}
        for m in measures:
            if not m.active:
                continue
            weighted = m.cost * weight_map.get(m.measure_type, 1.0)
            breakdown[m.measure_type] = breakdown.get(m.measure_type, 0.0) + weighted
        return breakdown

    def cost_gap(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> float:
        """计算与目标成本的差距 / Compute gap to target cost.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            正数表示超出目标，负数表示低于目标。
            Positive = over target, negative = under target.
        """
        total, _ = self.compute(measures)
        return total - self.target_cost

    def efficiency_ranking(
        self,
        measures: tuple[SoftSecurityMeasure, ...],
    ) -> tuple[SoftSecurityMeasure, ...]:
        """按成本效率排序 / Rank by cost efficiency.

        Args:
            measures: 所有安全措施 / All security measures.

        Returns:
            按成本效率降序排列的措施。
            Measures sorted by cost efficiency descending.
        """
        active = [m for m in measures if m.active]
        return tuple(sorted(active, key=lambda m: m.cost_efficiency, reverse=True))
