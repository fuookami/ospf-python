"""重量均衡调整明细 / Weight equalization adjustment detail.

定义单个舱室的重量调整数据。
Defines weight adjustment data for a single compartment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EqualizationAdjustment:
    """重量均衡调整 / Weight equalization adjustment.

    记录一个舱室从当前重量到目标重量的调整建议。
    Records the adjustment recommendation for a single
    compartment from its current weight to the target weight.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        current_kg: 当前重量 (kg) / Current weight (kg).
        target_kg: 目标重量 (kg) / Target weight (kg).
        delta_kg: 调整量 (kg)，正数为增加 /
            Adjustment delta (kg), positive = add.
        axis: 调整轴向 (lateral/longitudinal) /
            Adjustment axis (lateral/longitudinal).
    """

    compartment_id: str
    current_kg: float
    target_kg: float
    delta_kg: float
    axis: str = "lateral"

    @staticmethod
    def compute(
        *,
        compartment_id: str,
        current_kg: float,
        target_kg: float,
        axis: str = "lateral",
    ) -> EqualizationAdjustment:
        """计算并创建调整 / Compute and create adjustment.

        Args:
            compartment_id: 舱室标识 / Compartment identifier.
            current_kg: 当前重量 / Current weight (kg).
            target_kg: 目标重量 / Target weight (kg).
            axis: 调整轴向 / Adjustment axis.

        Returns:
            调整明细 / Adjustment detail.
        """
        return EqualizationAdjustment(
            compartment_id=compartment_id,
            current_kg=current_kg,
            target_kg=target_kg,
            delta_kg=target_kg - current_kg,
            axis=axis,
        )

    @property
    def is_increase(self) -> bool:
        """是否增重 / Is weight increase.

        Returns:
            调整量为正时返回 True。
            True if delta is positive.
        """
        return self.delta_kg > 0.0

    @property
    def is_decrease(self) -> bool:
        """是否减重 / Is weight decrease.

        Returns:
            调整量为负时返回 True。
            True if delta is negative.
        """
        return self.delta_kg < 0.0

    @property
    def is_no_change(self) -> bool:
        """是否无变化 / No change.

        Returns:
            调整量为零时返回 True。
            True if delta is zero.
        """
        return self.delta_kg == 0.0

    @property
    def absolute_delta(self) -> float:
        """绝对调整量 / Absolute delta.

        Returns:
            调整量的绝对值 / Absolute value of delta.
        """
        return abs(self.delta_kg)

    @property
    def percentage_change(self) -> float:
        """调整百分比 / Percentage change.

        Returns:
            相对于当前重量的百分比变化，当前为零时返回 0.0。
            Percentage change relative to current weight;
            0.0 if current is zero.
        """
        if self.current_kg == 0.0:
            return 0.0
        return (self.delta_kg / self.current_kg) * 100.0

    @property
    def is_lateral(self) -> bool:
        """是否横向调整 / Is lateral adjustment."""
        return self.axis == "lateral"

    @property
    def is_longitudinal(self) -> bool:
        """是否纵向调整 / Is longitudinal adjustment."""
        return self.axis == "longitudinal"
