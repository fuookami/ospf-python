"""载荷最大化聚合 / Payload maximization aggregation.

聚合所有载荷计算结果。
Aggregates all payload calculation results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .payload_result import PayloadResult


@dataclass(frozen=True)
class PayloadAggregation:
    """载荷最大化聚合 / Payload maximization aggregation.

    将多个载荷计算结果聚合为单一数据结构，
    提供便捷的查询和筛选方法。
    Aggregates multiple payload calculation results into
    a single data structure with convenient query and
    filter methods.

    Attributes:
        results: 载荷结果元组 / Tuple of payload results.
    """

    results: tuple[PayloadResult, ...]

    @staticmethod
    def empty() -> PayloadAggregation:
        """创建空聚合 / Create empty aggregation.

        Returns:
            空的载荷聚合 / Empty payload aggregation.
        """
        return PayloadAggregation(results=())

    @property
    def count(self) -> int:
        """结果数量 / Number of results.

        Returns:
            载荷结果数量 / Payload result count.
        """
        return len(self.results)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether aggregation is empty.

        Returns:
            无结果时为 True / True if no results.
        """
        return len(self.results) == 0

    @property
    def best_result(self) -> PayloadResult | None:
        """获取最优结果 / Get best result.

        返回最大载荷的可行结果。
        Returns the feasible result with the largest payload.

        Returns:
            最优结果或 None / Best result or None.
        """
        feasible = tuple(r for r in self.results if r.feasible)
        if not feasible:
            return None
        return max(feasible, key=lambda r: r.max_payload)

    @property
    def worst_result(self) -> PayloadResult | None:
        """获取最差结果 / Get worst result.

        Returns:
            最小载荷的结果或 None / Result with smallest payload.
        """
        if not self.results:
            return None
        return min(self.results, key=lambda r: r.max_payload)

    @property
    def all_feasible(self) -> bool:
        """是否全部可行 / Whether all results are feasible.

        Returns:
            所有结果均可行时返回 True。
            True if all results are feasible.
        """
        return all(r.feasible for r in self.results)

    @property
    def limiting_factors(self) -> tuple[str, ...]:
        """获取所有限制因素 / Get all limiting factors.

        Returns:
            去重后的限制因素元组。
            Tuple of unique limiting factors.
        """
        return tuple(dict.fromkeys(r.limiting_factor for r in self.results))

    def add(self, result: PayloadResult) -> PayloadAggregation:
        """添加结果（返回新聚合）/ Add result (new aggregation).

        Args:
            result: 待添加的载荷结果 / Payload result to add.

        Returns:
            包含新结果的新聚合 / New aggregation with added result.
        """
        return PayloadAggregation(
            results=self.results + (result,),
        )

    def filter_feasible(self) -> PayloadAggregation:
        """筛选可行结果 / Filter feasible results.

        Returns:
            仅包含可行结果的新聚合。
            New aggregation with only feasible results.
        """
        return PayloadAggregation(
            results=tuple(r for r in self.results if r.feasible),
        )
