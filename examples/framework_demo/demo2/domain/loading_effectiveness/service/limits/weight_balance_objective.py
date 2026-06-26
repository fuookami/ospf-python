"""重量平衡优化目标。

Weight balance objective for minimizing imbalance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.weight_distribution import WeightDistribution

if TYPE_CHECKING:
    from ...model.compartment_loading import CompartmentLoading


@dataclass(frozen=True)
class WeightBalanceObjective:
    """重量平衡优化目标。

    Minimizes weight imbalance across compartments by computing
    a balance score from lateral and longitudinal distribution.

    Attributes:
        lateral_groups: 左右舱室分组 / Left-right compartment groups
        longitudinal_groups: 前后舱室分组 / Front-rear compartment groups
        weight: 目标权重 / Objective weight in overall scoring
    """

    lateral_groups: tuple[frozenset[str], frozenset[str]]
    longitudinal_groups: tuple[frozenset[str], frozenset[str]]
    weight: float

    def compute(
        self,
        compartments: tuple[CompartmentLoading, ...],
    ) -> tuple[WeightDistribution, float]:
        """计算重量平衡得分。

        Computes weight distribution and a weighted balance score.
        Score of 1.0 = perfect balance, 0.0 = completely imbalanced.

        Args:
            compartments: 各舱室装载状态 / Compartment loading states

        Returns:
            tuple: (重量分布, 加权得分) / (WeightDistribution, weighted score)
        """
        weights = {c.compartment_id: c.weight for c in compartments}
        distribution = WeightDistribution.from_compartment_weights(
            weights,
            self.lateral_groups,
            self.longitudinal_groups,
        )
        balance_score = (
            distribution.lateral_balance + distribution.longitudinal_balance
        ) / 2.0
        weighted = balance_score * self.weight
        return (distribution, weighted)

    def worst_axis(
        self,
        distribution: WeightDistribution,
    ) -> tuple[str, float]:
        """识别最不平衡的轴向。

        Args:
            distribution: 重量分布 / Weight distribution

        Returns:
            tuple: (轴向名称, 不平衡度) / (axis name, imbalance value)
        """
        lateral_imbalance = 1.0 - distribution.lateral_balance
        longitudinal_imbalance = 1.0 - distribution.longitudinal_balance
        if lateral_imbalance >= longitudinal_imbalance:
            return ("lateral", lateral_imbalance)
        return ("longitudinal", longitudinal_imbalance)

    def rebalance_suggestion(
        self,
        distribution: WeightDistribution,
    ) -> str:
        """生成再平衡建议。

        Args:
            distribution: 重量分布 / Weight distribution

        Returns:
            str: 建议描述 / Rebalance suggestion
        """
        axis, imbalance = self.worst_axis(distribution)
        if imbalance < 0.05:
            return "重量分布已平衡，无需调整"
        direction = "左/右" if axis == "lateral" else "前/后"
        return (
            f"建议将部分货物从较重一侧移至较轻一侧"
            f"（{direction}），当前不平衡度 "
            f"{imbalance:.1%}"
        )
