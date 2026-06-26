"""装载平衡 / Stowage balance.

描述飞机装载后的力矩和平衡指数。
Describes moments and balance index after cargo loading.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StowageBalance:
    """装载平衡 / Stowage balance.

    记录装载方案的横向力矩、纵向力矩和平衡指数，
    用于评估飞机重心是否在安全范围内。
    Records lateral moment, longitudinal moment, and balance
    index of a stowage plan, used to evaluate whether the
    aircraft center of gravity is within safe limits.

    Attributes:
        lateral_moment: 横向力矩（千克·米）/
            Lateral moment (kg*m).
        longitudinal_moment: 纵向力矩（千克·米）/
            Longitudinal moment (kg*m).
        balance_index: 平衡指数 /
            Balance index.
    """

    lateral_moment: float = 0.0
    """横向力矩（千克·米）/ Lateral moment (kg*m)."""

    longitudinal_moment: float = 0.0
    """纵向力矩（千克·米）/ Longitudinal moment (kg*m)."""

    balance_index: float = 0.0
    """平衡指数 / Balance index."""

    @staticmethod
    def from_moments(
        *,
        lateral_moment: float,
        longitudinal_moment: float,
        total_weight: float,
    ) -> StowageBalance:
        """从力矩和总重量计算平衡。

        Calculate balance from moments and total weight.

        Args:
            lateral_moment: 横向力矩。/ Lateral moment.
            longitudinal_moment: 纵向力矩。/ Longitudinal moment.
            total_weight: 总重量。/ Total weight.

        Returns:
            平衡实例。/ Balance instance.
        """
        index = 0.0
        if total_weight > 0.0:
            index = longitudinal_moment / total_weight
        return StowageBalance(
            lateral_moment=lateral_moment,
            longitudinal_moment=longitudinal_moment,
            balance_index=index,
        )

    @property
    def is_lateral_balanced(self) -> bool:
        """横向是否平衡。

        Whether the load is laterally balanced.

        Returns:
            横向力矩绝对值小于阈值时返回 True。
            True if absolute lateral moment is below threshold.
        """
        return abs(self.lateral_moment) < 1000.0

    @property
    def is_longitudinal_balanced(self) -> bool:
        """纵向是否平衡。

        Whether the load is longitudinally balanced.

        Returns:
            纵向力矩绝对值小于阈值时返回 True。
            True if absolute longitudinal moment is below threshold.
        """
        return abs(self.longitudinal_moment) < 5000.0

    def lateral_offset(self, total_weight: float) -> float:
        """计算横向偏移量。

        Calculate lateral offset.

        Args:
            total_weight: 总重量（千克）。/ Total weight (kg).

        Returns:
            横向偏移（米），总重量为零时返回 0.0。
            Lateral offset (m), or 0.0 if total weight is zero.
        """
        if total_weight <= 0.0:
            return 0.0
        return self.lateral_moment / total_weight

    def longitudinal_offset(
        self,
        total_weight: float,
    ) -> float:
        """计算纵向偏移量。

        Calculate longitudinal offset.

        Args:
            total_weight: 总重量（千克）。/ Total weight (kg).

        Returns:
            纵向偏移（米），总重量为零时返回 0.0。
            Longitudinal offset (m), or 0.0 if total weight is zero.
        """
        if total_weight <= 0.0:
            return 0.0
        return self.longitudinal_moment / total_weight
