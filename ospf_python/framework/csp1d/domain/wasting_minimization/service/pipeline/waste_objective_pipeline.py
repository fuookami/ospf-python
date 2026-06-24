"""CSP1D 余料目标管线。

向余料模型添加最小化余料的优化目标。
Waste objective pipeline for waste minimization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WasteObjectivePipeline:
    """余料目标管线 / Waste objective pipeline.

    在余料模型中添加最小化余料的目标函数。
    在列生成中用于评估切割方案的 reduced cost。
    Adds waste minimization objective to the
    waste model. Used in column generation to
    evaluate reduced cost of cutting plans.

    Attributes:
        waste_weight: 余料惩罚权重。
            Waste penalty weight.
        utilization_bonus: 利用率奖励系数。
            Utilization bonus coefficient.
        min_utilization: 最低利用率阈值。
            Minimum utilization threshold.
    """

    waste_weight: float = 1.0
    """余料惩罚权重 / Waste penalty weight."""

    utilization_bonus: float = 0.0
    """利用率奖励 / Utilization bonus."""

    min_utilization: float = 0.0
    """最低利用率 / Min utilization."""

    def apply[T](self, aggregation: T) -> T:
        """应用余料目标。

        Apply waste objective.

        Args:
            aggregation: 余料聚合。
                Waste aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def compute_waste_cost(
        self,
        *,
        waste_length: float,
    ) -> float:
        """计算余料惩罚成本。

        Compute waste penalty cost.

        Args:
            waste_length: 余料长度。
                Waste length.

        Returns:
            余料惩罚成本。
            Waste penalty cost.
        """
        return waste_length * self.waste_weight

    def compute_utilization_bonus(
        self,
        *,
        utilization_ratio: float,
    ) -> float:
        """计算利用率奖励。

        Compute utilization bonus.

        Args:
            utilization_ratio: 利用率（0.0 ~ 1.0）。
                Utilization ratio (0.0 ~ 1.0).

        Returns:
            利用率奖励（负值表示减少成本）。
            Utilization bonus (negative means cost reduction).
        """
        if utilization_ratio < self.min_utilization:
            return 0.0
        return -utilization_ratio * self.utilization_bonus

    def compute_reduced_cost(
        self,
        *,
        waste_length: float,
        utilization_ratio: float,
        shadow_price: float,
    ) -> float:
        """计算切割方案的 reduced cost。

        Compute reduced cost of a cutting plan.

        Args:
            waste_length: 余料长度。
                Waste length.
            utilization_ratio: 利用率。
                Utilization ratio.
            shadow_price: 影子价格。
                Shadow price.

        Returns:
            reduced cost 值。
            Reduced cost value.
        """
        return (
            self.compute_waste_cost(
                waste_length=waste_length,
            )
            + self.compute_utilization_bonus(
                utilization_ratio=utilization_ratio,
            )
            - shadow_price
        )
