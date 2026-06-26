"""软安全聚合模型 / Soft security aggregation model.

收集多次评估结果并提供统计分析。
Collects multiple evaluation results and provides
statistical analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .soft_security_measure import SoftSecurityMeasure
    from .soft_security_result import SoftSecurityResult


@dataclass(frozen=True)
class SoftSecurityAggregation:
    """软安全聚合 / Soft security aggregation.

    聚合多次软安全评估结果，提供合规率、平均评分和
    总成本等汇总统计。
    Aggregates multiple soft security evaluation results,
    providing summary statistics such as compliance rate,
    average score, and total cost.

    Attributes:
        results: 评估结果元组 / Tuple of evaluation results.
        measures: 已纳入措施元组 /
            Tuple of incorporated measures.
    """

    results: tuple[SoftSecurityResult, ...]
    measures: tuple[SoftSecurityMeasure, ...] = ()

    @staticmethod
    def from_results(
        results: tuple[SoftSecurityResult, ...],
    ) -> SoftSecurityAggregation:
        """从结果列表创建聚合 / Create aggregation from results.

        Args:
            results: 评估结果列表 / Evaluation results.

        Returns:
            聚合实例 / Aggregation instance.
        """
        return SoftSecurityAggregation(results=results)

    @property
    def result_count(self) -> int:
        """结果数量 / Result count."""
        return len(self.results)

    @property
    def compliant_count(self) -> int:
        """合规数量 / Compliant count."""
        return sum(1 for r in self.results if r.compliant)

    @property
    def compliance_rate(self) -> float:
        """合规率 / Compliance rate.

        Returns:
            合规结果占总结果的比例，无结果时返回 0.0。
            Ratio of compliant results; 0.0 if no results.
        """
        if not self.results:
            return 0.0
        return self.compliant_count / len(self.results)

    @property
    def average_score(self) -> float:
        """平均评分 / Average score.

        Returns:
            所有结果的平均安全评分，无结果时返回 0.0。
            Average security score; 0.0 if no results.
        """
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)

    @property
    def total_cost(self) -> float:
        """总成本 / Total cost."""
        return sum(r.total_cost for r in self.results)

    @property
    def total_measure_count(self) -> int:
        """总措施数 / Total measure count."""
        return sum(r.measure_count for r in self.results)

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
    def is_fully_compliant(self) -> bool:
        """是否全部合规 / Is fully compliant.

        Returns:
            所有结果均合规时返回 True。
            True if all results are compliant.
        """
        return all(r.compliant for r in self.results)

    def worst_result(self) -> SoftSecurityResult | None:
        """获取最差结果 / Get worst result.

        Returns:
            评分最低的结果，无结果时返回 None。
            Result with the lowest score, or None.
        """
        if not self.results:
            return None
        return min(self.results, key=lambda r: r.score)

    def best_result(self) -> SoftSecurityResult | None:
        """获取最佳结果 / Get best result.

        Returns:
            评分最高的结果，无结果时返回 None。
            Result with the highest score, or None.
        """
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.score)
