"""重量均衡聚合模型 / Weight equalization aggregation model.

收集多次均衡评估结果并提供统计分析。
Collects multiple equalization evaluation results
and provides statistical analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .equalization_result import EqualizationResult


@dataclass(frozen=True)
class EqualizationAggregation:
    """重量均衡聚合 / Weight equalization aggregation.

    聚合多次均衡评估结果，提供均衡率、平均不平衡度和
    总调整量等汇总统计。
    Aggregates multiple equalization evaluation results,
    providing summary statistics such as balance rate,
    average imbalance, and total adjustments.

    Attributes:
        results: 评估结果元组 / Tuple of evaluation results.
    """

    results: tuple[EqualizationResult, ...]

    @staticmethod
    def from_results(
        results: tuple[EqualizationResult, ...],
    ) -> EqualizationAggregation:
        """从结果列表创建聚合 / Create aggregation from results.

        Args:
            results: 评估结果列表 / Evaluation results.

        Returns:
            聚合实例 / Aggregation instance.
        """
        return EqualizationAggregation(results=results)

    @property
    def result_count(self) -> int:
        """结果数量 / Result count."""
        return len(self.results)

    @property
    def balanced_count(self) -> int:
        """均衡数量 / Balanced count."""
        return sum(1 for r in self.results if r.is_balanced)

    @property
    def balance_rate(self) -> float:
        """均衡率 / Balance rate.

        Returns:
            均衡结果占总结果的比例，无结果时返回 0.0。
            Ratio of balanced results; 0.0 if no results.
        """
        if not self.results:
            return 0.0
        return self.balanced_count / len(self.results)

    @property
    def average_imbalance(self) -> float:
        """平均不平衡度 / Average imbalance.

        Returns:
            所有结果的平均最大不平衡度，无结果时返回 0.0。
            Average max imbalance; 0.0 if no results.
        """
        if not self.results:
            return 0.0
        return sum(r.max_imbalance for r in self.results) / len(self.results)

    @property
    def worst_imbalance(self) -> float:
        """最差不平衡度 / Worst imbalance.

        Returns:
            所有结果中的最大不平衡度。
            Maximum imbalance across all results.
        """
        if not self.results:
            return 0.0
        return max(r.max_imbalance for r in self.results)

    @property
    def total_adjustments(self) -> int:
        """总调整数量 / Total adjustment count."""
        return sum(r.adjustment_count for r in self.results)

    @property
    def total_delta(self) -> float:
        """总调整量 / Total delta.

        Returns:
            所有结果的总绝对调整量之和。
            Sum of total deltas across all results.
        """
        return sum(r.total_delta for r in self.results)

    @property
    def all_violations(self) -> tuple[str, ...]:
        """所有违规 / All violations.

        Returns:
            去重后的全部违规描述。
            Deduplicated violation descriptions.
        """
        seen: dict[str, None] = {}
        for r in self.results:
            for v in r.violations:
                seen.setdefault(v, None)
        return tuple(seen.keys())

    @property
    def is_fully_balanced(self) -> bool:
        """是否全部均衡 / Is fully balanced.

        Returns:
            所有结果均均衡时返回 True。
            True if all results are balanced.
        """
        return all(r.is_balanced for r in self.results)

    def worst_result(self) -> EqualizationResult | None:
        """获取最差结果 / Get worst result.

        Returns:
            不平衡度最高的结果，无结果时返回 None。
            Result with highest imbalance, or None.
        """
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.max_imbalance)

    def best_result(self) -> EqualizationResult | None:
        """获取最佳结果 / Get best result.

        Returns:
            不平衡度最低的结果，无结果时返回 None。
            Result with lowest imbalance, or None.
        """
        if not self.results:
            return None
        return min(self.results, key=lambda r: r.max_imbalance)
