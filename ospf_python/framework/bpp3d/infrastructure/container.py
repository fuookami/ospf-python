"""容器定义 / Container definition.

BPP3D 中的三维容器（箱子）尺寸定义。
Three-dimensional container (bin) dimensions in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Container:
    """三维容器 / Three-dimensional container.

    描述 BPP3D 问题中可用容器的宽、高、深尺寸。
    Describes width, height, and depth of a container
    available in the BPP3D problem.

    Attributes:
        width: 容器宽度 / Container width.
        height: 容器高度 / Container height.
        depth: 容器深度 / Container depth.
    """

    width: float
    """容器宽度 / Container width."""

    height: float
    """容器高度 / Container height."""

    depth: float
    """容器深度 / Container depth."""

    @staticmethod
    def create(
        *,
        width: float,
        height: float,
        depth: float,
    ) -> Container:
        """创建容器 / Create container.

        Args:
            width: 容器宽度 / Container width.
            height: 容器高度 / Container height.
            depth: 容器深度 / Container depth.

        Returns:
            容器实例 / Container instance.
        """
        return Container(
            width=width,
            height=height,
            depth=depth,
        )

    @property
    def volume(self) -> float:
        """容器体积 / Container volume.

        Returns:
            宽 x 高 x 深 / Width x Height x Depth.
        """
        return self.width * self.height * self.depth
