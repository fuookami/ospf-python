"""重量限制 / Weight limit.

定义货舱在不同飞行阶段的重量限制。
Defines weight limits for compartments across flight phases.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightLimit:
    """重量限制 / Weight limit.

    描述特定货舱在指定飞行阶段的最大承载重量。
    Describes the maximum weight capacity of a compartment
    during a specific flight phase.

    Attributes:
        compartment: 舱室标识 / Compartment identifier.
        max_weight: 最大重量（千克）/ Maximum weight (kg).
        flight_phase: 飞行阶段（GROUND/TAKEOFF/CRUISE/LANDING）/
            Flight phase (GROUND/TAKEOFF/CRUISE/LANDING).
    """

    compartment: str = ""
    """舱室标识 / Compartment identifier."""

    max_weight: float = 0.0
    """最大重量（千克）/ Maximum weight (kg)."""

    flight_phase: str = "GROUND"
    """飞行阶段 / Flight phase."""

    @staticmethod
    def create(
        *,
        compartment: str,
        max_weight: float,
        flight_phase: str = "GROUND",
    ) -> WeightLimit:
        """创建重量限制。

        Create weight limit.

        Args:
            compartment: 舱室标识。/ Compartment identifier.
            max_weight: 最大重量（千克）。/ Maximum weight (kg).
            flight_phase: 飞行阶段，默认 GROUND。/
                Flight phase, default GROUND.

        Returns:
            限制实例。/ Limit instance.
        """
        return WeightLimit(
            compartment=compartment,
            max_weight=max_weight,
            flight_phase=flight_phase,
        )

    @property
    def is_ground_phase(self) -> bool:
        """是否为地面阶段。

        Whether this is the ground phase.

        Returns:
            飞行阶段为 GROUND 时返回 True。
            True if flight phase is GROUND.
        """
        return self.flight_phase == "GROUND"

    @property
    def is_flight_phase(self) -> bool:
        """是否为飞行阶段。

        Whether this is a flight phase.

        Returns:
            飞行阶段不是 GROUND 时返回 True。
            True if flight phase is not GROUND.
        """
        return self.flight_phase != "GROUND"

    def allows_weight(self, weight: float) -> bool:
        """检查重量是否在限制内。

        Check whether weight is within limit.

        Args:
            weight: 当前重量（千克）。/ Current weight (kg).

        Returns:
            重量不超过限制时返回 True。
            True if weight does not exceed limit.
        """
        return weight <= self.max_weight

    def remaining(self, current_weight: float) -> float:
        """计算剩余重量容量。

        Calculate remaining weight capacity.

        Args:
            current_weight: 当前重量（千克）。/ Current weight (kg).

        Returns:
            剩余容量（千克），最小为 0.0。
            Remaining capacity (kg), minimum 0.0.
        """
        return max(0.0, self.max_weight - current_weight)

    def utilization(self, current_weight: float) -> float:
        """计算重量利用率。

        Calculate weight utilization ratio.

        Args:
            current_weight: 当前重量（千克）。/ Current weight (kg).

        Returns:
            利用率（0.0-1.0），最大重量为零时返回 0.0。
            Utilization ratio (0.0-1.0), or 0.0 if max weight is zero.
        """
        if self.max_weight <= 0.0:
            return 0.0
        return min(1.0, current_weight / self.max_weight)
