"""冗余分析聚合 / Redundancy analysis aggregation.

聚合所有冗余分析结果。
Aggregates all redundancy analysis results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .redundancy_component import RedundancyComponent
    from .redundancy_result import RedundancyResult


@dataclass(frozen=True)
class RedundancyAggregation:
    """冗余分析聚合 / Redundancy analysis aggregation.

    将多个系统的冗余分析结果聚合为单一数据结构，
    提供便捷的查询和筛选方法。
    Aggregates redundancy analysis results from multiple
    systems into a single data structure with convenient
    query and filter methods.

    Attributes:
        results: 冗余结果元组 / Tuple of redundancy results.
        components: 组件元组 / Tuple of components.
    """

    results: tuple[RedundancyResult, ...]
    components: tuple[RedundancyComponent, ...] = ()

    @staticmethod
    def empty() -> RedundancyAggregation:
        """创建空聚合 / Create empty aggregation.

        Returns:
            空的冗余聚合 / Empty redundancy aggregation.
        """
        return RedundancyAggregation(
            results=(),
            components=(),
        )

    @property
    def count(self) -> int:
        """结果数量 / Number of results.

        Returns:
            冗余结果数量 / Redundancy result count.
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
    def all_compliant(self) -> bool:
        """是否全部合规 / Whether all are compliant.

        Returns:
            所有结果均合规时返回 True。
            True if all results are compliant.
        """
        return all(r.compliant for r in self.results)

    @property
    def non_compliant_results(
        self,
    ) -> tuple[RedundancyResult, ...]:
        """获取不合规结果 / Get non-compliant results.

        Returns:
            不合规结果元组 / Tuple of non-compliant results.
        """
        return tuple(r for r in self.results if not r.compliant)

    @property
    def critical_components(self) -> tuple[str, ...]:
        """获取所有关键组件标识 / Get all critical component IDs.

        Returns:
            去重后的关键组件标识元组。
            Tuple of unique critical component identifiers.
        """
        ids: list[str] = []
        seen: set[str] = set()
        for r in self.results:
            for comp_id in r.critical_components:
                if comp_id not in seen:
                    seen.add(comp_id)
                    ids.append(comp_id)
        return tuple(ids)

    @property
    def min_redundancy_level(self) -> int:
        """最小冗余等级 / Minimum redundancy level.

        Returns:
            所有结果中的最低冗余等级。
            Minimum redundancy level across all results.
        """
        if not self.results:
            return 0
        return min(r.redundancy_level for r in self.results)

    @property
    def total_violations(self) -> int:
        """总违规数 / Total violation count.

        Returns:
            所有结果的违规总数。
            Total violations across all results.
        """
        return sum(r.violation_count for r in self.results)

    def find_by_system(
        self,
        system_id: str,
    ) -> RedundancyResult | None:
        """按系统标识查找结果。

        Find result by system identifier.

        Args:
            system_id: 系统标识 / System identifier.

        Returns:
            匹配的结果，未找到返回 None。
            Matching result, or None if not found.
        """
        for r in self.results:
            if r.system_id == system_id:
                return r
        return None

    def find_component(
        self,
        component_id: str,
    ) -> RedundancyComponent | None:
        """按标识查找组件。

        Find component by identifier.

        Args:
            component_id: 组件标识 / Component identifier.

        Returns:
            匹配的组件，未找到返回 None。
            Matching component, or None if not found.
        """
        for c in self.components:
            if c.component_id == component_id:
                return c
        return None

    def add(
        self,
        result: RedundancyResult,
    ) -> RedundancyAggregation:
        """添加结果（返回新聚合）/ Add result (new aggregation).

        Args:
            result: 冗余结果 / Redundancy result.

        Returns:
            包含新结果的新聚合 / New aggregation with added result.
        """
        return RedundancyAggregation(
            results=self.results + (result,),
            components=self.components,
        )
