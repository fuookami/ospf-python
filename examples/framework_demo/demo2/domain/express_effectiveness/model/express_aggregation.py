"""快递结果聚合模型。

Express aggregation model for collecting and ranking delivery results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .express_result import ExpressResult


@dataclass(frozen=True)
class ExpressAggregation:
    """快递结果聚合。

    Aggregates multiple express evaluation results and provides
    methods to find the best option and compute statistics.

    Attributes:
        results: 所有评估结果 / All evaluation results
        best_score: 最佳得分 / Best score among results
    """

    results: tuple[ExpressResult, ...]
    best_score: float

    @staticmethod
    def from_results(results: tuple[ExpressResult, ...]) -> ExpressAggregation:
        """从结果列表创建聚合。

        Args:
            results: 评估结果列表 / Evaluation results

        Returns:
            ExpressAggregation: 聚合结果 / Aggregated result
        """
        best = max((r.score for r in results), default=0.0)
        return ExpressAggregation(results=results, best_score=best)

    def best_result(self) -> ExpressResult | None:
        """获取最佳结果。

        Returns:
            ExpressResult | None: 最佳结果 / Best result or None
        """
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.score)

    def fastest_feasible(self) -> ExpressResult | None:
        """获取最快的可行结果。

        Returns:
            ExpressResult | None: 最快可行结果 / Fastest feasible result
        """
        feasible = [r for r in self.results if r.feasible]
        if not feasible:
            return None
        return min(feasible, key=lambda r: r.time_estimate)

    def above_threshold(self, threshold: float) -> tuple[ExpressResult, ...]:
        """筛选高于阈值的结果。

        Args:
            threshold: 得分阈值 / Score threshold

        Returns:
            tuple: 符合条件的结果 / Results above threshold
        """
        return tuple(r for r in self.results if r.score >= threshold)

    def average_score(self) -> float:
        """计算平均得分。

        Returns:
            float: 平均得分 / Average score
        """
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)
