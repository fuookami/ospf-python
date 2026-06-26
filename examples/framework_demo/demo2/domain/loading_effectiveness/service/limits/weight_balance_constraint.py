"""重量平衡约束。

Weight balance constraint enforcing balance across compartments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...model.weight_distribution import WeightDistribution

if TYPE_CHECKING:
    from ...model.compartment_loading import CompartmentLoading


@dataclass(frozen=True)
class WeightBalanceConstraint:
    """重量平衡约束。

    Enforces that the weight distribution across compartments stays
    within specified lateral and longitudinal balance tolerances.

    Attributes:
        max_lateral_imbalance: 最大横向不平衡度 / Max lateral imbalance tolerance
        max_longitudinal_imbalance: 最大纵向不平衡度 / Max longitudinal imbalance tolerance
        lateral_groups: 左右舱室分组 / Left-right compartment groups
        longitudinal_groups: 前后舱室分组 / Front-rear compartment groups
    """

    max_lateral_imbalance: float
    max_longitudinal_imbalance: float
    lateral_groups: tuple[frozenset[str], frozenset[str]]
    longitudinal_groups: tuple[frozenset[str], frozenset[str]]

    def evaluate(
        self,
        compartments: tuple[CompartmentLoading, ...],
    ) -> tuple[bool, WeightDistribution]:
        """评估装载方案是否满足重量平衡约束。

        Evaluates whether the given compartment loadings satisfy the
        weight balance requirements.

        Args:
            compartments: 各舱室装载状态 / Compartment loading states

        Returns:
            tuple: (是否满足约束, 重量分布) / (constraint satisfied, weight distribution)
        """
        weights = {c.compartment_id: c.weight for c in compartments}
        distribution = WeightDistribution.from_compartment_weights(
            weights,
            self.lateral_groups,
            self.longitudinal_groups,
        )
        lateral_ok = distribution.lateral_balance >= (1.0 - self.max_lateral_imbalance)
        longitudinal_ok = distribution.longitudinal_balance >= (
            1.0 - self.max_longitudinal_imbalance
        )
        return (lateral_ok and longitudinal_ok, distribution)

    def imbalance_penalty(
        self,
        distribution: WeightDistribution,
    ) -> float:
        """计算不平衡惩罚值。

        Computes a penalty score for weight imbalance (0 = balanced,
        higher = more imbalanced).

        Args:
            distribution: 重量分布 / Weight distribution

        Returns:
            float: 惩罚值 / Penalty value
        """
        lateral_gap = max(
            self.max_lateral_imbalance - (1.0 - distribution.lateral_balance),
            0.0,
        )
        longitudinal_gap = max(
            self.max_longitudinal_imbalance - (1.0 - distribution.longitudinal_balance),
            0.0,
        )
        return lateral_gap + longitudinal_gap
