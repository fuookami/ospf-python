"""快递效能结果模型。

Express result model for delivery evaluation output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .express_metric import ExpressMetric


@dataclass(frozen=True)
class ExpressResult:
    """快递效能评估结果。

    Encapsulates the express delivery effectiveness evaluation
    including score, time estimate, and feasibility.

    Attributes:
        score: 总体效能得分 (0-1) / Overall effectiveness score (0-1)
        time_estimate: 预计配送时间（小时）/ Estimated delivery time (hours)
        feasible: 方案是否可行 / Whether the plan is feasible
    """

    score: float
    time_estimate: float
    feasible: bool

    @staticmethod
    def from_metrics(
        metrics: tuple[ExpressMetric, ...],
        *,
        time_estimate: float,
        feasible: bool = True,
    ) -> ExpressResult:
        """从指标列表计算总分。

        Computes overall score from individual metrics.

        Args:
            metrics: 指标列表 / List of metrics
            time_estimate: 预计配送时间 / Estimated delivery hours
            feasible: 是否可行 / Feasibility flag

        Returns:
            ExpressResult: 计算结果 / Computed result
        """
        if not metrics:
            return ExpressResult(
                score=0.0,
                time_estimate=time_estimate,
                feasible=feasible,
            )
        met_count = sum(1 for m in metrics if m.is_met())
        score = met_count / len(metrics)
        return ExpressResult(
            score=score,
            time_estimate=time_estimate,
            feasible=feasible,
        )

    def metric_by_name(
        self, name: str, metrics: tuple[ExpressMetric, ...]
    ) -> ExpressMetric | None:
        """按名称查找指标。

        Args:
            name: 指标名称 / Metric name
            metrics: 指标列表 / Metric list

        Returns:
            ExpressMetric | None: 找到的指标 / Found metric or None
        """
        for m in metrics:
            if m.metric_name == name:
                return m
        return None

    def is_passing(self, min_score: float = 0.6) -> bool:
        """判断是否通过评估。

        Args:
            min_score: 最低通过分数 / Minimum passing score

        Returns:
            bool: 是否通过 / Whether passing
        """
        return self.feasible and self.score >= min_score
