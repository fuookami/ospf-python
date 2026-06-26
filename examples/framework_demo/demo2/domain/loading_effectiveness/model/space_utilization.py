"""空间利用率模型。

Space utilization model for tracking volume usage in loading operations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpaceUtilization:
    """空间利用率统计。

    Tracks total available volume, used volume, and computes the utilization
    ratio for a loading compartment or overall container.

    Attributes:
        total_volume: 总可用体积（立方米）/ Total available volume (m³)
        used_volume: 已使用体积（立方米）/ Used volume (m³)
        ratio: 利用率比率 / Utilization ratio
    """

    total_volume: float
    used_volume: float
    ratio: float

    @staticmethod
    def compute(total_volume: float, used_volume: float) -> SpaceUtilization:
        """根据总量和使用量计算空间利用率。

        Computes space utilization from total and used volumes.

        Args:
            total_volume: 总可用体积 / Total available volume
            used_volume: 已使用体积 / Used volume

        Returns:
            SpaceUtilization: 计算结果 / Computed utilization
        """
        safe_total = total_volume if total_volume > 0.0 else 1.0
        clamped_used = max(0.0, min(used_volume, total_volume))
        return SpaceUtilization(
            total_volume=total_volume,
            used_volume=clamped_used,
            ratio=clamped_used / safe_total,
        )

    def remaining_volume(self) -> float:
        """计算剩余可用体积。

        Returns:
            float: 剩余体积 / Remaining volume in m³
        """
        return max(self.total_volume - self.used_volume, 0.0)

    def is_fully_utilized(self, threshold: float = 0.95) -> bool:
        """判断是否已充分装载。

        Args:
            threshold: 充分装载阈值 / Full utilization threshold

        Returns:
            bool: 是否充分装载 / Whether fully utilized
        """
        return self.ratio >= threshold
