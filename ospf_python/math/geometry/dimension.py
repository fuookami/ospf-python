"""尺寸类型。

Dimension type for width, height, depth.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    """三维尺寸，不可变。

    Immutable 3D dimension.

    Attributes:
        width: 宽度。/ Width.
        height: 高度。/ Height.
        depth: 深度。/ Depth.
    """

    width: float
    height: float
    depth: float

    @staticmethod
    def cube(size: float) -> Dimension:
        """创建立方体尺寸。

        Create cube dimension.

        Args:
            size: 边长。/ Edge length.

        Returns:
            立方体尺寸。/ Cube dimension.
        """
        return Dimension(
            width=size,
            height=size,
            depth=size,
        )

    def volume(self) -> float:
        """计算体积。

        Compute volume.

        Returns:
            体积。/ Volume.
        """
        return self.width * self.height * self.depth
