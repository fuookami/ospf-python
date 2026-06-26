"""容积限制 / Volume limit.

定义货舱的最大容积限制。
Defines volume limits for compartments.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeLimit:
    """容积限制 / Volume limit.

    描述特定货舱的最大承载容积。
    Describes the maximum volume capacity of a compartment.

    Attributes:
        compartment: 舱室标识 / Compartment identifier.
        max_volume: 最大容积（立方米）/
            Maximum volume (cubic meters).
    """

    compartment: str = ""
    """舱室标识 / Compartment identifier."""

    max_volume: float = 0.0
    """最大容积（立方米）/ Maximum volume (cubic meters)."""

    @staticmethod
    def create(
        *,
        compartment: str,
        max_volume: float,
    ) -> VolumeLimit:
        """创建容积限制。

        Create volume limit.

        Args:
            compartment: 舱室标识。/ Compartment identifier.
            max_volume: 最大容积（立方米）。/
                Maximum volume (cubic meters).

        Returns:
            限制实例。/ Limit instance.
        """
        return VolumeLimit(
            compartment=compartment,
            max_volume=max_volume,
        )

    def allows_volume(self, volume: float) -> bool:
        """检查容积是否在限制内。

        Check whether volume is within limit.

        Args:
            volume: 当前容积（立方米）。/ Current volume.

        Returns:
            容积不超过限制时返回 True。
            True if volume does not exceed limit.
        """
        return volume <= self.max_volume

    def remaining(self, current_volume: float) -> float:
        """计算剩余容积。

        Calculate remaining volume.

        Args:
            current_volume: 当前容积（立方米）。/ Current volume.

        Returns:
            剩余容积（立方米），最小为 0.0。
            Remaining volume (cubic meters), minimum 0.0.
        """
        return max(0.0, self.max_volume - current_volume)

    def utilization(self, current_volume: float) -> float:
        """计算容积利用率。

        Calculate volume utilization ratio.

        Args:
            current_volume: 当前容积（立方米）。/ Current volume.

        Returns:
            利用率（0.0-1.0），最大容积为零时返回 0.0。
            Utilization ratio (0.0-1.0), or 0.0 if max volume is zero.
        """
        if self.max_volume <= 0.0:
            return 0.0
        return min(1.0, current_volume / self.max_volume)
