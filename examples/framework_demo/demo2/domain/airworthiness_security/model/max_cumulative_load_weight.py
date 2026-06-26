"""最大累积载荷重量 / Max cumulative load weight.

定义各站位的累积载荷重量上限。
Defines the cumulative load weight upper bound at each
station position.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaxCumulativeLoadWeight:
    """最大累积载荷重量 / Max cumulative load weight.

    描述飞机纵轴上某一站位的累积载荷重量限制，
    用于保证沿机身方向的载荷分布满足结构强度要求。
    Describes the cumulative load weight limit at a station
    along the aircraft longitudinal axis, ensuring that the
    load distribution meets structural strength requirements.

    Attributes:
        position: 站位位置(m) / Station position (m).
        max_weight: 最大累积重量(kg) / Max cumulative weight (kg).
        cumulative: 当前已累积重量(kg) / Current cumulative weight (kg).
    """

    position: float
    max_weight: float
    cumulative: float

    @staticmethod
    def create(
        *,
        position: float,
        max_weight: float,
        cumulative: float = 0.0,
    ) -> MaxCumulativeLoadWeight:
        """创建累积载荷限制 / Create cumulative load limit.

        Args:
            position: 站位位置(m) / Station position (m).
            max_weight: 最大累积重量(kg) / Max cumulative weight (kg).
            cumulative: 当前累积重量，默认 0 / Current, default 0.

        Returns:
            累积载荷限制实例 / MaxCumulativeLoadWeight instance.
        """
        return MaxCumulativeLoadWeight(
            position=position,
            max_weight=max_weight,
            cumulative=cumulative,
        )

    @property
    def remaining_capacity(self) -> float:
        """剩余可用容量 / Remaining available capacity.

        Returns:
            最大重量与当前累积重量之差(kg)，最小为 0。
            Difference between max and current (kg), floored at 0.
        """
        return max(0.0, self.max_weight - self.cumulative)

    @property
    def utilization_ratio(self) -> float:
        """利用率 / Utilization ratio.

        Returns:
            当前累积重量占最大重量的比例，上限 1.0。
            Ratio of current to max weight, capped at 1.0.
        """
        if self.max_weight <= 0.0:
            return 0.0
        return min(1.0, self.cumulative / self.max_weight)

    def can_accommodate(self, weight: float) -> bool:
        """检查是否能容纳额外重量。

        Check whether additional weight can be accommodated.

        Args:
            weight: 额外重量(kg)。/ Additional weight (kg).

        Returns:
            若剩余容量足够则返回 True。
            True if remaining capacity is sufficient.
        """
        return weight <= self.remaining_capacity

    def with_additional(self, weight: float) -> MaxCumulativeLoadWeight:
        """创建增加重量后的副本。

        Create a copy with additional weight recorded.

        Args:
            weight: 新增重量(kg)。/ Additional weight (kg).

        Returns:
            累积重量更新后的新实例。
            New instance with updated cumulative weight.
        """
        return MaxCumulativeLoadWeight(
            position=self.position,
            max_weight=self.max_weight,
            cumulative=self.cumulative + weight,
        )

    def margin(self) -> float:
        """计算余量 / Calculate margin.

        Returns:
            距最大累积重量的余量(kg)，负值表示超限。
            Margin to max cumulative weight (kg);
            negative means exceeding.
        """
        return self.max_weight - self.cumulative
