"""分段线性半径近似配置 / PWL radius approximation config.

配置圆柱体半径的分段线性近似参数。
Configures piecewise linear approximation parameters
for cylinder radius.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PwlRadiusApproximationConfig:
    """分段线性半径近似配置。

    控制圆柱体半径平方近似的精度和分段数。
    Controls precision and segment count of piecewise
    linear approximation for cylinder radius squared.

    Attributes:
        segment_count: 分段数 / Number of segments.
        tolerance: 近似容差 / Approximation tolerance.
    """

    segment_count: int
    """分段数 / Number of segments."""

    tolerance: float
    """近似容差 / Approximation tolerance."""

    @staticmethod
    def create(
        *,
        segment_count: int = 8,
        tolerance: float = 1e-6,
    ) -> PwlRadiusApproximationConfig:
        """创建 PWL 配置 / Create PWL config.

        Args:
            segment_count: 分段数，默认 8 / Segments, default 8.
            tolerance: 近似容差，默认 1e-6 / Tolerance, default 1e-6.

        Returns:
            PWL 配置实例 / PWL config instance.
        """
        return PwlRadiusApproximationConfig(
            segment_count=segment_count,
            tolerance=tolerance,
        )
