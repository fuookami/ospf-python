"""保守半径包络 / Conservative radius envelope.

用于 BPP3D 中圆柱体物品的保守半径近似。
Conservative radius approximation for cylindrical
items in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConservativeRadiusEnvelope:
    """保守半径包络。

    包络半径用于安全近似圆柱体在放置时的有效半径。
    Conservative radius envelope for safe approximation of
    effective cylinder radius during placement.

    Attributes:
        radius: 实际半径 / Actual radius.
        envelope_radius: 包络半径 / Envelope radius.
    """

    radius: float
    """实际半径 / Actual radius."""

    envelope_radius: float
    """包络半径 / Envelope radius."""

    @staticmethod
    def create(
        *,
        radius: float,
        envelope_radius: float,
    ) -> ConservativeRadiusEnvelope:
        """创建保守半径包络 / Create conservative radius envelope.

        Args:
            radius: 实际半径 / Actual radius.
            envelope_radius: 包络半径 / Envelope radius.

        Returns:
            保守半径包络实例 / ConservativeRadiusEnvelope.
        """
        return ConservativeRadiusEnvelope(
            radius=radius,
            envelope_radius=envelope_radius,
        )

    @property
    def safety_margin(self) -> float:
        """安全裕度 / Safety margin.

        Returns:
            包络半径与实际半径的差值 / Difference between
            envelope and actual radius.
        """
        return self.envelope_radius - self.radius
