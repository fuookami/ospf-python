"""装箱指标模型。

Loading metric model for measuring individual aspects of loading performance.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadingMetric:
    """单项装箱指标。

    Single loading metric capturing one dimension of loading performance,
    such as weight utilization, volume utilization, or balance score.

    Attributes:
        metric_name: 指标名称 / Name of the metric
        value: 当前测量值 / Current measured value
        weight: 指标权重 / Weight of the metric in overall scoring
        target: 目标值 / Target value for the metric
    """

    metric_name: str
    value: float
    weight: float
    target: float

    def achievement_ratio(self) -> float:
        """计算目标达成率。

        Calculates how close the current value is to the target.

        Returns:
            float: 达成率，范围 [0, 1+] / Achievement ratio, range [0, 1+]
        """
        if self.target == 0.0:
            return 1.0
        return self.value / self.target

    def weighted_score(self) -> float:
        """计算加权得分。

        Calculates the weighted score contribution of this metric.

        Returns:
            float: 加权得分 / Weighted score contribution
        """
        ratio = self.achievement_ratio()
        capped = min(ratio, 1.0)
        return capped * self.weight

    def gap_to_target(self) -> float:
        """计算与目标的差距。

        Calculates the absolute gap between current value and target.

        Returns:
            float: 差距值（正值表示未达标）/ Gap value (positive means below target)
        """
        return max(self.target - self.value, 0.0)
