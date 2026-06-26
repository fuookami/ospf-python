"""快递指标模型。

Express metric model for measuring delivery performance.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressMetric:
    """快递单项指标。

    Single express delivery metric capturing one dimension of
    delivery performance such as timeliness, cost, or reliability.

    Attributes:
        metric_name: 指标名称 / Metric name
        value: 当前测量值 / Current measured value
        target: 目标值 / Target value
    """

    metric_name: str
    value: float
    target: float

    def achievement_ratio(self) -> float:
        """计算目标达成率。

        Returns:
            float: 达成率 / Achievement ratio
        """
        if self.target == 0.0:
            return 1.0
        return self.value / self.target

    def is_met(self) -> bool:
        """判断是否达标。

        Returns:
            bool: 是否达到目标 / Whether target is met
        """
        return self.value >= self.target

    def gap(self) -> float:
        """计算与目标的差距。

        Returns:
            float: 差距值 / Gap to target
        """
        return max(self.target - self.value, 0.0)
