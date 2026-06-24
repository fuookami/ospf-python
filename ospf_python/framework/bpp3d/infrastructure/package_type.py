"""包裹类型 / Package type.

BPP3D 中包裹的类型定义。
Package type definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PackageType:
    """包裹类型 / Package type.

    描述 BPP3D 中包裹的基本属性。
    Describes basic attributes of a package in BPP3D.

    Attributes:
        name: 类型名称 / Type name.
        width: 包裹宽度 / Package width.
        height: 包裹高度 / Package height.
        depth: 包裹深度 / Package depth.
    """

    name: str
    """类型名称 / Type name."""

    width: float
    """包裹宽度 / Package width."""

    height: float
    """包裹高度 / Package height."""

    depth: float
    """包裹深度 / Package depth."""

    @staticmethod
    def create(
        *,
        name: str,
        width: float,
        height: float,
        depth: float,
    ) -> PackageType:
        """创建包裹类型 / Create package type.

        Args:
            name: 类型名称 / Type name.
            width: 包裹宽度 / Package width.
            height: 包裹高度 / Package height.
            depth: 包裹深度 / Package depth.

        Returns:
            包裹类型实例 / Package type instance.
        """
        return PackageType(
            name=name,
            width=width,
            height=height,
            depth=depth,
        )

    @property
    def volume(self) -> float:
        """包裹体积 / Package volume.

        Returns:
            宽 x 高 x 深 / Width x Height x Depth.
        """
        return self.width * self.height * self.depth
