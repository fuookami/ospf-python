"""层聚合 / Layer aggregation.

管理层的聚合操作。
Manages layer aggregation operations.
"""

from __future__ import annotations

import abc


class LayerAggregation(abc.ABC):
    """层聚合 / Layer aggregation.

    将多个相似层聚合为一个表示。
    Aggregates multiple similar layers into one representation.
    """

    @abc.abstractmethod
    def aggregate(self, layers: tuple[object, ...]) -> object:
        """聚合层 / Aggregate layers.

        Args:
            layers: 待聚合的层 / Layers to aggregate.

        Returns:
            聚合结果 / The aggregation result.
        """
        ...

    @abc.abstractmethod
    def can_aggregate(self, layers: tuple[object, ...]) -> bool:
        """检查是否可聚合 / Check if aggregable.

        Args:
            layers: 待检查的层 / Layers to check.

        Returns:
            可聚合返回 True / True if aggregable.
        """
        ...
