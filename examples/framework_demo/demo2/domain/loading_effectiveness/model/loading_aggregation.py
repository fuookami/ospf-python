"""装载方案聚合模型。

Loading aggregation model for collecting and ranking multiple patterns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .loading_pattern import LoadingPattern


@dataclass(frozen=True)
class LoadingAggregation:
    """装载方案聚合。

    Aggregates multiple loading patterns and provides methods to
    find the best pattern and compute statistics.

    Attributes:
        patterns: 所有候选方案 / All candidate loading patterns
        best_score: 最佳方案得分 / Best pattern efficiency score
    """

    patterns: tuple[LoadingPattern, ...]
    best_score: float

    @staticmethod
    def from_patterns(patterns: tuple[LoadingPattern, ...]) -> LoadingAggregation:
        """从方案列表创建聚合。

        Creates an aggregation from a collection of patterns.

        Args:
            patterns: 候选方案列表 / Candidate patterns

        Returns:
            LoadingAggregation: 聚合结果 / Aggregated result
        """
        best = max((p.efficiency for p in patterns), default=0.0)
        return LoadingAggregation(patterns=patterns, best_score=best)

    def best_pattern(self) -> LoadingPattern | None:
        """获取最佳方案。

        Returns:
            LoadingPattern | None: 最佳方案，无方案时返回None / Best pattern or None
        """
        if not self.patterns:
            return None
        return max(self.patterns, key=lambda p: p.efficiency)

    def above_threshold(self, threshold: float) -> tuple[LoadingPattern, ...]:
        """筛选高于阈值的方案。

        Args:
            threshold: 效率阈值 / Efficiency threshold

        Returns:
            tuple: 符合条件的方案 / Patterns above threshold
        """
        return tuple(p for p in self.patterns if p.efficiency >= threshold)

    def average_efficiency(self) -> float:
        """计算平均效率。

        Returns:
            float: 平均效率，无方案时返回0 / Average efficiency or 0
        """
        if not self.patterns:
            return 0.0
        return sum(p.efficiency for p in self.patterns) / len(self.patterns)
