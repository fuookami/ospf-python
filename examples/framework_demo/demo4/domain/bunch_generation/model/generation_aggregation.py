"""Generation aggregation for comparing strategy results.

生成聚合：比较策略结果 / Generation aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .generation_strategy import GenerationStrategy

if TYPE_CHECKING:
    from .generation_result import GenerationResult


@dataclass(frozen=True)
class GenerationAggregation:
    """Aggregation of generation results from multiple strategies.

    多策略生成结果的聚合。
    """

    results: tuple[GenerationResult, ...]
    best_strategy: GenerationStrategy

    @classmethod
    def from_results(
        cls,
        results: tuple[GenerationResult, ...],
    ) -> GenerationAggregation:
        """Create aggregation and determine the best strategy.

        创建聚合并确定最佳策略。
        """
        if not results:
            return cls(
                results=results,
                best_strategy=GenerationStrategy.GREEDY,
            )
        best = max(results, key=lambda r: r.score)
        return cls(
            results=results,
            best_strategy=best.strategy,
        )

    @property
    def best_result(self) -> GenerationResult | None:
        """The generation result with the highest score.

        分数最高的生成结果。
        """
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.score)

    @property
    def strategy_count(self) -> int:
        """Number of strategies evaluated.

        已评估的策略数量。
        """
        return len(self.results)

    @property
    def score_range(self) -> float:
        """Difference between highest and lowest scores.

        最高分和最低分之间的差异。
        """
        if len(self.results) < 2:
            return 0.0
        scores = [r.score for r in self.results]
        return max(scores) - min(scores)
