"""地板载荷定义 / Floor loading definition.

定义货舱各区域的地板载荷限制。
Defines the floor loading limits for each cargo area.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FloorLoading:
    """地板载荷 / Floor loading.

    描述货舱某一区域地板的单位面积最大承载能力
    及当前载荷，用于防止地板结构超载。
    Describes the per-square-meter maximum load capacity
    and current load of a cargo area floor, used to prevent
    floor structural overload.

    Attributes:
        area_id: 区域标识 / Area identifier.
        max_load_per_sqm: 最大单位面积载荷(kg/m^2) /
            Max load per square meter (kg/m^2).
        current_load: 当前单位面积载荷(kg/m^2) /
            Current load per square meter (kg/m^2).
    """

    area_id: str
    max_load_per_sqm: float
    current_load: float

    @staticmethod
    def create(
        *,
        area_id: str,
        max_load_per_sqm: float,
        current_load: float = 0.0,
    ) -> FloorLoading:
        """创建地板载荷 / Create floor loading.

        Args:
            area_id: 区域标识 / Area identifier.
            max_load_per_sqm: 最大单位面积载荷(kg/m^2) /
                Max load per square meter (kg/m^2).
            current_load: 当前载荷，默认 0 / Current load, default 0.

        Returns:
            地板载荷实例 / FloorLoading instance.
        """
        return FloorLoading(
            area_id=area_id,
            max_load_per_sqm=max_load_per_sqm,
            current_load=current_load,
        )

    @property
    def remaining_capacity(self) -> float:
        """剩余承载容量 / Remaining load capacity.

        Returns:
            最大载荷与当前载荷之差(kg/m^2)，最小为 0。
            Difference between max and current (kg/m^2),
            floored at 0.
        """
        return max(0.0, self.max_load_per_sqm - self.current_load)

    @property
    def utilization_ratio(self) -> float:
        """利用率 / Utilization ratio.

        Returns:
            当前载荷占最大载荷的比例，上限 1.0。
            Ratio of current to max load, capped at 1.0.
        """
        if self.max_load_per_sqm <= 0.0:
            return 0.0
        return min(1.0, self.current_load / self.max_load_per_sqm)

    def can_accommodate(self, load: float) -> bool:
        """检查是否能容纳额外载荷。

        Check whether additional load can be accommodated.

        Args:
            load: 额外载荷(kg/m^2)。/ Additional load (kg/m^2).

        Returns:
            若剩余容量足够则返回 True。
            True if remaining capacity is sufficient.
        """
        return load <= self.remaining_capacity

    def with_load(self, additional: float) -> FloorLoading:
        """创建增加载荷后的副本。

        Create a copy with additional load recorded.

        Args:
            additional: 新增载荷(kg/m^2)。/ Additional load (kg/m^2).

        Returns:
            载荷更新后的新实例。
            New instance with updated current load.
        """
        return FloorLoading(
            area_id=self.area_id,
            max_load_per_sqm=self.max_load_per_sqm,
            current_load=self.current_load + additional,
        )

    def margin(self) -> float:
        """计算余量 / Calculate margin.

        Returns:
            距最大载荷的余量(kg/m^2)，负值表示超限。
            Margin to max load (kg/m^2); negative means exceeding.
        """
        return self.max_load_per_sqm - self.current_load

    def load_for_area(self, area_sqm: float) -> float:
        """计算面积上的总载荷 / Calculate total load for area.

        Args:
            area_sqm: 面积(m^2)。/ Area (m^2).

        Returns:
            当前单位面积载荷乘以面积(kg)。
            Current per-sqm load times area (kg).
        """
        return self.current_load * area_sqm
