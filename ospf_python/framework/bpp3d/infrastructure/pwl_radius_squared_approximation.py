"""分段线性半径平方近似 / PWL radius squared approximation.

对圆柱体半径平方进行分段线性近似。
Piecewise linear approximation of cylinder radius squared.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.pwl_radius_approximation_config import (
        PwlRadiusApproximationConfig,
    )


@dataclass(frozen=True)
class PwlRadiusSquaredApproximation:
    """分段线性半径平方近似。

    使用分段线性函数近似半径平方值，用于线性化
    圆柱体体积约束。
    Uses piecewise linear function to approximate radius
    squared for linearizing cylinder volume constraints.

    Attributes:
        config: PWL 近似配置 / PWL approximation config.
        breakpoints: 断点列表 / Breakpoint list.
        slopes: 各段斜率 / Segment slopes.
    """

    config: PwlRadiusApproximationConfig
    """PWL 近似配置 / PWL approximation config."""

    breakpoints: tuple[float, ...]
    """断点列表 / Breakpoint list."""

    slopes: tuple[float, ...]
    """各段斜率 / Segment slopes."""

    @staticmethod
    def create(
        *,
        config: PwlRadiusApproximationConfig,
        breakpoints: tuple[float, ...],
        slopes: tuple[float, ...],
    ) -> PwlRadiusSquaredApproximation:
        """创建近似实例 / Create approximation instance.

        Args:
            config: PWL 配置 / PWL config.
            breakpoints: 断点列表 / Breakpoint list.
            slopes: 斜率列表 / Slope list.

        Returns:
            近似实例 / Approximation instance.
        """
        return PwlRadiusSquaredApproximation(
            config=config,
            breakpoints=breakpoints,
            slopes=slopes,
        )

    @property
    def segment_count(self) -> int:
        """分段数 / Segment count.

        Returns:
            断点数减一 / Number of breakpoints minus one.
        """
        return len(self.breakpoints) - 1
