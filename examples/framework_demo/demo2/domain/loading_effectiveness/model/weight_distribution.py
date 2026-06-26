"""重量分布模型。

Weight distribution model for tracking balance across compartments.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightDistribution:
    """各舱室重量分布。

    Captures the weight distribution across loading compartments and
    computes lateral and longitudinal balance metrics.

    Attributes:
        compartments: 各舱室重量映射 / Mapping of compartment_id to weight (kg)
        lateral_balance: 横向平衡系数 (0-1) / Lateral balance coefficient (0-1)
        longitudinal_balance: 纵向平衡系数 (0-1) / Longitudinal balance coefficient (0-1)
    """

    compartments: dict[str, float]
    lateral_balance: float
    longitudinal_balance: float

    @staticmethod
    def from_compartment_weights(
        weights: dict[str, float],
        lateral_groups: tuple[frozenset[str], frozenset[str]],
        longitudinal_groups: tuple[frozenset[str], frozenset[str]],
    ) -> WeightDistribution:
        """根据舱室重量和分组计算分布。

        Computes weight distribution from compartment weights and
        lateral/longitudinal grouping definitions.

        Args:
            weights: 各舱室重量 / Compartment weights in kg
            lateral_groups: 左右分组 / Left-right compartment groups
            longitudinal_groups: 前后分组 / Front-rear compartment groups

        Returns:
            WeightDistribution: 计算的分布 / Computed distribution
        """
        lateral = _compute_balance(weights, lateral_groups)
        longitudinal = _compute_balance(weights, longitudinal_groups)
        return WeightDistribution(
            compartments=dict(weights),
            lateral_balance=lateral,
            longitudinal_balance=longitudinal,
        )

    def total_weight(self) -> float:
        """计算总重量。

        Returns:
            float: 所有舱室总重量 / Total weight across all compartments
        """
        return sum(self.compartments.values())

    def is_balanced(self, tolerance: float = 0.1) -> bool:
        """判断重量是否平衡。

        Args:
            tolerance: 允许偏差 / Acceptable imbalance tolerance

        Returns:
            bool: 是否在平衡范围内 / Whether within balance tolerance
        """
        return self.lateral_balance >= (
            1.0 - tolerance
        ) and self.longitudinal_balance >= (1.0 - tolerance)


def _compute_balance(
    weights: dict[str, float],
    groups: tuple[frozenset[str], frozenset[str]],
) -> float:
    """计算两组之间的平衡系数。

    Computes a balance coefficient between two groups of compartments.
    A value of 1.0 means perfect balance; 0.0 means all weight on one side.

    Args:
        weights: 各舱室重量 / Compartment weights
        groups: 两组舱室ID / Two groups of compartment IDs

    Returns:
        float: 平衡系数 / Balance coefficient
    """
    group_a, group_b = groups
    weight_a = sum(weights.get(cid, 0.0) for cid in group_a)
    weight_b = sum(weights.get(cid, 0.0) for cid in group_b)
    total = weight_a + weight_b
    if total == 0.0:
        return 1.0
    smaller = min(weight_a, weight_b)
    return (2.0 * smaller) / total
