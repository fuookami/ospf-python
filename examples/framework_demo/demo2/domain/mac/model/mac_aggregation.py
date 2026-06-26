"""MAC 结果聚合 / MAC result aggregation.

管理多个 MAC 计算结果的聚合查询。
Aggregation query for multiple MAC calculation results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.mac.model.mac_result import (
        MACResult,
    )


@dataclass(frozen=True)
class MACAggregation:
    """MAC 结果聚合 / MAC result aggregation.

    将同一机型的多个 MAC 计算结果聚合为一个集合，
    提供便捷的查询和筛选方法。
    Aggregates multiple MAC results for the same aircraft
    type into a collection with convenient query and
    filter methods.

    Attributes:
        results: MAC 结果元组 / Tuple of MAC results.
        aircraft_type: 机型代码 / Aircraft type code.
    """

    results: tuple[MACResult, ...]
    """MAC 结果元组 / Tuple of MAC results."""

    aircraft_type: str
    """机型代码 / Aircraft type code."""

    @staticmethod
    def create(
        *,
        results: tuple[MACResult, ...],
        aircraft_type: str,
    ) -> MACAggregation:
        """创建 MAC 聚合 / Create MAC aggregation.

        Args:
            results: MAC 结果元组 / Tuple of MAC results.
            aircraft_type: 机型代码 / Aircraft type code.

        Returns:
            MAC 聚合实例 / MAC aggregation instance.
        """
        return MACAggregation(
            results=results,
            aircraft_type=aircraft_type,
        )

    @staticmethod
    def empty(*, aircraft_type: str) -> MACAggregation:
        """创建空聚合 / Create empty aggregation.

        Args:
            aircraft_type: 机型代码 / Aircraft type code.

        Returns:
            空的 MAC 聚合 / Empty MAC aggregation.
        """
        return MACAggregation(
            results=(),
            aircraft_type=aircraft_type,
        )

    @property
    def count(self) -> int:
        """结果数量 / Number of results.

        Returns:
            MAC 结果数量 / MAC result count.
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
    def primary(self) -> MACResult | None:
        """获取主 MAC 结果 / Get primary MAC result.

        返回第一个结果作为主结果。
        Returns the first result as the primary.

        Returns:
            主 MAC 结果或 None / Primary MAC result or None.
        """
        if not self.results:
            return None
        return self.results[0]

    def largest_mac(self) -> MACResult | None:
        """获取最大 MAC 值 / Get largest MAC value.

        Returns:
            MAC 值最大的结果或 None /
            Result with largest MAC value or None.
        """
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.mac_value)

    def containing_station(self, fuselage_station: float) -> tuple[MACResult, ...]:
        """查找包含指定站位的 MAC 结果。

        Find MAC results containing the specified station.

        Args:
            fuselage_station: 机身站位 (m) / Fuselage station (m).

        Returns:
            包含该站位的 MAC 结果元组 /
            Tuple of MAC results containing the station.
        """
        return tuple(r for r in self.results if r.contains_station(fuselage_station))

    def add(self, result: MACResult) -> MACAggregation:
        """添加结果（返回新聚合）/ Add result (returns new aggregation).

        Args:
            result: 待添加的 MAC 结果 / MAC result to add.

        Returns:
            包含新结果的新聚合 / New aggregation with added result.
        """
        return MACAggregation(
            results=self.results + (result,),
            aircraft_type=self.aircraft_type,
        )
