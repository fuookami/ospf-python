"""平衡限制 / Balance limit.

定义飞机重心力矩的平衡限制。
Defines balance limits for aircraft center of gravity moments.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BalanceLimit:
    """平衡限制 / Balance limit.

    描述飞机在指定轴上的力矩允许范围。
    Describes the allowable moment range on a specified axis.

    Attributes:
        axis: 力矩轴（LATERAL/LONGITUDINAL）/
            Moment axis (LATERAL/LONGITUDINAL).
        min_moment: 最小力矩（千克·米）/
            Minimum moment (kg*m).
        max_moment: 最大力矩（千克·米）/
            Maximum moment (kg*m).
    """

    axis: str = "LONGITUDINAL"
    """力矩轴 / Moment axis."""

    min_moment: float = 0.0
    """最小力矩（千克·米）/ Minimum moment (kg*m)."""

    max_moment: float = 0.0
    """最大力矩（千克·米）/ Maximum moment (kg*m)."""

    @staticmethod
    def create(
        *,
        axis: str,
        min_moment: float,
        max_moment: float,
    ) -> BalanceLimit:
        """创建平衡限制。

        Create balance limit.

        Args:
            axis: 力矩轴。/ Moment axis.
            min_moment: 最小力矩。/ Minimum moment.
            max_moment: 最大力矩。/ Maximum moment.

        Returns:
            限制实例。/ Limit instance.
        """
        return BalanceLimit(
            axis=axis,
            min_moment=min_moment,
            max_moment=max_moment,
        )

    @property
    def is_lateral(self) -> bool:
        """是否为横向力矩限制。

        Whether this is a lateral moment limit.

        Returns:
            轴为 LATERAL 时返回 True。
            True if axis is LATERAL.
        """
        return self.axis == "LATERAL"

    @property
    def is_longitudinal(self) -> bool:
        """是否为纵向力矩限制。

        Whether this is a longitudinal moment limit.

        Returns:
            轴为 LONGITUDINAL 时返回 True。
            True if axis is LONGITUDINAL.
        """
        return self.axis == "LONGITUDINAL"

    @property
    def moment_range(self) -> float:
        """力矩允许范围。

        Allowable moment range.

        Returns:
            最大力矩减最小力矩。
            Max moment minus min moment.
        """
        return self.max_moment - self.min_moment

    @property
    def center_moment(self) -> float:
        """力矩中心值。

        Center moment value.

        Returns:
            最大和最小力矩的平均值。
            Average of max and min moments.
        """
        return (self.max_moment + self.min_moment) / 2.0

    def allows_moment(self, moment: float) -> bool:
        """检查力矩是否在限制内。

        Check whether moment is within limit.

        Args:
            moment: 当前力矩（千克·米）。/ Current moment (kg*m).

        Returns:
            力矩在允许范围内时返回 True。
            True if moment is within allowable range.
        """
        return self.min_moment <= moment <= self.max_moment

    def violation_amount(self, moment: float) -> float:
        """计算力矩违反量。

        Calculate moment violation amount.

        Args:
            moment: 当前力矩（千克·米）。/ Current moment (kg*m).

        Returns:
            违反量（非负），在限制内时返回 0.0。
            Violation amount (non-negative), 0.0 if within limit.
        """
        if moment < self.min_moment:
            return self.min_moment - moment
        if moment > self.max_moment:
            return moment - self.max_moment
        return 0.0
