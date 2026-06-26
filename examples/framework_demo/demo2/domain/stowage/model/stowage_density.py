"""装载密度 / Stowage density.

描述货舱的空间利用密度。
Describes the spatial utilization density of a compartment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StowageDensity:
    """装载密度 / Stowage density.

    记录单个货舱的容积使用情况和密度比率，
    用于评估空间利用效率。
    Records volume usage and density ratio for a single
    compartment, used to evaluate space utilization efficiency.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        volume_used: 已使用容积（立方米）/
            Volume used (cubic meters).
        density_ratio: 密度比率（0.0-1.0）/
            Density ratio (0.0-1.0).
    """

    compartment_id: str = ""
    """舱室标识 / Compartment identifier."""

    volume_used: float = 0.0
    """已使用容积（立方米）/ Volume used (cubic meters)."""

    density_ratio: float = 0.0
    """密度比率（0.0-1.0）/ Density ratio (0.0-1.0)."""

    @staticmethod
    def from_usage(
        *,
        compartment_id: str,
        volume_used: float,
        max_volume: float,
    ) -> StowageDensity:
        """从容积使用情况计算密度。

        Calculate density from volume usage.

        Args:
            compartment_id: 舱室标识。/ Compartment identifier.
            volume_used: 已使用容积。/ Volume used.
            max_volume: 最大容积。/ Maximum volume.

        Returns:
            密度实例。/ Density instance.
        """
        ratio = 0.0
        if max_volume > 0.0:
            ratio = min(1.0, volume_used / max_volume)
        return StowageDensity(
            compartment_id=compartment_id,
            volume_used=volume_used,
            density_ratio=ratio,
        )

    @property
    def is_full(self) -> bool:
        """是否已满。

        Whether the compartment is full.

        Returns:
            密度比率大于 0.95 时返回 True。
            True if density ratio exceeds 0.95.
        """
        return self.density_ratio > 0.95

    @property
    def is_underutilized(self) -> bool:
        """是否利用率过低。

        Whether the compartment is underutilized.

        Returns:
            密度比率小于 0.3 时返回 True。
            True if density ratio is below 0.3.
        """
        return self.density_ratio < 0.3

    def remaining_ratio(self) -> float:
        """计算剩余空间比率。

        Calculate remaining space ratio.

        Returns:
            1.0 减去密度比率，最小为 0.0。
            1.0 minus density ratio, minimum 0.0.
        """
        return max(0.0, 1.0 - self.density_ratio)

    def efficiency_score(self) -> float:
        """计算效率评分。

        Calculate efficiency score.

        Returns:
            0.0-1.0 的评分，0.7-0.9 为最佳区间。
            Score from 0.0-1.0, where 0.7-0.9 is optimal.
        """
        if self.density_ratio <= 0.0:
            return 0.0
        if self.density_ratio <= 0.8:
            return self.density_ratio
        return max(0.0, 1.0 - (self.density_ratio - 0.8) * 2.0)
