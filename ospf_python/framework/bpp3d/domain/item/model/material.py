"""材质定义 / Material definition.

BPP3D 中物品的材质定义。
Material definition for items in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    """材质 / Material.

    描述物品的材质属性。
    Describes the material properties of an item.

    Attributes:
        material_id: 材质标识 / Material identifier.
        name: 材质名称 / Material name.
        density: 材质密度 / Material density.
    """

    material_id: str
    """材质标识 / Material identifier."""

    name: str
    """材质名称 / Material name."""

    density: float = 0.0
    """材质密度 / Material density."""

    @staticmethod
    def create(
        *,
        material_id: str,
        name: str,
        density: float = 0.0,
    ) -> Material:
        """创建材质 / Create material.

        Args:
            material_id: 材质标识 / Material identifier.
            name: 材质名称 / Material name.
            density: 材质密度，默认 0 / Density, default 0.

        Returns:
            材质实例 / Material instance.
        """
        return Material(
            material_id=material_id,
            name=name,
            density=density,
        )
