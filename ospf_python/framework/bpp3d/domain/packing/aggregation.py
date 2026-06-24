"""装箱聚合 / Packing aggregation.

管理装箱方案的聚合操作。
Manages packing solution aggregation operations.
"""

from __future__ import annotations

import abc


class PackingAggregation(abc.ABC):
    """装箱聚合 / Packing aggregation.

    将多个装箱方案聚合为统一表示。
    Aggregates multiple packing solutions into a unified
    representation.
    """

    @abc.abstractmethod
    def aggregate(
        self,
        solutions: tuple[object, ...],
    ) -> object:
        """聚合方案 / Aggregate solutions.

        Args:
            solutions: 待聚合的方案 / Solutions to aggregate.

        Returns:
            聚合结果 / The aggregation result.
        """
        ...

    @abc.abstractmethod
    def can_aggregate(
        self,
        solutions: tuple[object, ...],
    ) -> bool:
        """检查是否可聚合 / Check if aggregable.

        Args:
            solutions: 待检查的方案 / Solutions to check.

        Returns:
            可聚合返回 True / True if aggregable.
        """
        ...
