"""装箱效能结果模型。

Loading effectiveness result model for final evaluation output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .loading_metric import LoadingMetric


@dataclass(frozen=True)
class LoadingEffectivenessResult:
    """装箱效能评估结果。

    Encapsulates the final effectiveness evaluation including an
    overall score, individual metrics, and feasibility status.

    Attributes:
        score: 总体效能得分 (0-1) / Overall effectiveness score (0-1)
        metrics: 各项指标列表 / List of individual loading metrics
        feasible: 方案是否可行 / Whether the loading plan is feasible
    """

    score: float
    metrics: tuple[LoadingMetric, ...]
    feasible: bool

    @staticmethod
    def from_metrics(
        metrics: tuple[LoadingMetric, ...],
        *,
        feasible: bool = True,
    ) -> LoadingEffectivenessResult:
        """从指标列表计算总分并创建结果。

        Computes the overall score from weighted metric scores.

        Args:
            metrics: 指标列表 / List of metrics
            feasible: 是否可行 / Feasibility flag

        Returns:
            LoadingEffectivenessResult: 计算结果 / Computed result
        """
        total_weight = sum(m.weight for m in metrics)
        if total_weight == 0.0:
            score = 0.0
        else:
            score = sum(m.weighted_score() for m in metrics) / total_weight
        return LoadingEffectivenessResult(
            score=score,
            metrics=metrics,
            feasible=feasible,
        )

    def metric_by_name(self, name: str) -> LoadingMetric | None:
        """按名称查找指标。

        Args:
            name: 指标名称 / Metric name

        Returns:
            LoadingMetric | None: 找到的指标或None / Found metric or None
        """
        for m in self.metrics:
            if m.metric_name == name:
                return m
        return None

    def underperforming_metrics(self) -> tuple[LoadingMetric, ...]:
        """获取未达标指标。

        Returns:
            tuple: 未达到目标的指标 / Metrics below their target
        """
        return tuple(m for m in self.metrics if m.achievement_ratio() < 1.0)

    def is_passing(self, min_score: float = 0.6) -> bool:
        """判断是否通过效能评估。

        Args:
            min_score: 最低通过分数 / Minimum passing score

        Returns:
            bool: 是否通过 / Whether passing
        """
        return self.feasible and self.score >= min_score
