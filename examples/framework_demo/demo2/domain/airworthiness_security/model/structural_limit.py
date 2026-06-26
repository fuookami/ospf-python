"""结构限制定义 / Structural limit definition.

定义飞机各部件的结构承载限制。
Defines the structural load-bearing limits for each
aircraft component.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LimitType(Enum):
    """限制类型 / Limit type.

    描述结构限制的类别。
    Describes the category of a structural limit.
    """

    WEIGHT = "weight"
    """重量限制 / Weight limit."""

    FORCE = "force"
    """力限制 / Force limit."""

    MOMENT = "moment"
    """力矩限制 / Moment limit."""

    PRESSURE = "pressure"
    """压力限制 / Pressure limit."""

    TORQUE = "torque"
    """扭矩限制 / Torque limit."""


@dataclass(frozen=True)
class StructuralLimit:
    """结构限制 / Structural limit.

    描述飞机某一部件在指定限制类型下的最大承载值，
    用于装箱方案的结构安全性校验。
    Describes the maximum load-bearing value for a specific
    aircraft component under a given limit type, used for
    structural safety verification of packing solutions.

    Attributes:
        component: 部件标识 / Component identifier.
        limit_type: 限制类型 / Limit type.
        value: 限制值(与类型对应单位) / Limit value (unit per type).
    """

    component: str
    limit_type: LimitType
    value: float

    @staticmethod
    def create(
        *,
        component: str,
        limit_type: LimitType,
        value: float,
    ) -> StructuralLimit:
        """创建结构限制 / Create structural limit.

        Args:
            component: 部件标识 / Component identifier.
            limit_type: 限制类型 / Limit type.
            value: 限制值 / Limit value.

        Returns:
            结构限制实例 / StructuralLimit instance.
        """
        return StructuralLimit(
            component=component,
            limit_type=limit_type,
            value=value,
        )

    def is_within_limit(self, current: float) -> bool:
        """检查当前值是否在限制内。

        Check whether the current value is within the limit.

        Args:
            current: 当前值。/ Current value.

        Returns:
            若当前值不超过限制则返回 True。
            True if current value does not exceed the limit.
        """
        return current <= self.value

    def margin(self, current: float) -> float:
        """计算余量 / Calculate margin.

        Args:
            current: 当前值。/ Current value.

        Returns:
            距限制值的余量，负值表示超限。
            Margin to limit value; negative means exceeding.
        """
        return self.value - current

    def utilization(self, current: float) -> float:
        """计算利用率 / Calculate utilization.

        Args:
            current: 当前值。/ Current value.

        Returns:
            当前值占限制值的比例，上限 1.0。
            Ratio of current to limit, capped at 1.0.
        """
        if self.value <= 0.0:
            return 0.0
        return min(1.0, current / self.value)

    def scaled(self, factor: float) -> StructuralLimit:
        """按因子缩放限制值 / Scale limit value by factor.

        Args:
            factor: 缩放因子。/ Scale factor.

        Returns:
            限制值缩放后的新实例。
            New instance with scaled limit value.
        """
        return StructuralLimit(
            component=self.component,
            limit_type=self.limit_type,
            value=self.value * factor,
        )
