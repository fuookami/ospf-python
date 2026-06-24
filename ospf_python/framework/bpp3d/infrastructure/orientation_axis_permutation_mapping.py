"""方向轴置换映射 / Orientation axis permutation mapping.

将方向枚举映射到轴置换索引。
Maps orientation enum to axis permutation indices.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.bpp3d.infrastructure.orientation import (
    Orientation,
)


@dataclass(frozen=True)
class OrientationAxisPermutationMapping:
    """方向轴置换映射。

    每个方向对应一个三元组 (x_idx, y_idx, z_idx)，
    表示原始尺寸到该方向的轴映射。
    Each orientation maps to a triple (x_idx, y_idx, z_idx)
    indicating the axis mapping from original dimensions.

    Attributes:
        x_index: X 轴对应原始维度索引 / X axis original index.
        y_index: Y 轴对应原始维度索引 / Y axis original index.
        z_index: Z 轴对应原始维度索引 / Z axis original index.
    """

    x_index: int
    """X 轴对应原始维度索引 / X axis original index."""

    y_index: int
    """Y 轴对应原始维度索引 / Y axis original index."""

    z_index: int
    """Z 轴对应原始维度索引 / Z axis original index."""

    @staticmethod
    def from_orientation(
        orientation: Orientation,
    ) -> OrientationAxisPermutationMapping:
        """从方向枚举创建映射 / Create mapping from orientation.

        Args:
            orientation: 放置方向 / Placement orientation.

        Returns:
            轴置换映射实例 / Axis permutation mapping.
        """
        mapping = {
            Orientation.XYZ: (0, 1, 2),
            Orientation.XZY: (0, 2, 1),
            Orientation.YXZ: (1, 0, 2),
            Orientation.YZX: (1, 2, 0),
            Orientation.ZXY: (2, 0, 1),
            Orientation.ZYX: (2, 1, 0),
        }
        x, y, z = mapping[orientation]
        return OrientationAxisPermutationMapping(
            x_index=x,
            y_index=y,
            z_index=z,
        )
