"""数量几何核心 / Quantity geometry core.

BPP3D 中带数量的几何形状核心定义。
Quantity-aware geometry core definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.packing_shape import (
        PackingShape,
    )


@dataclass(frozen=True)
class QuantityGeometryCore:
    """数量几何核心 / Quantity geometry core.

    将几何形状类型与尺寸和数量关联。
    Associates geometry shape type with dimensions
    and quantity.

    Attributes:
        shape: 装箱形状类型 / Packing shape type.
        dimensions: 尺寸元组 / Dimension tuple.
        quantity: 需求数量 / Demand quantity.
    """

    shape: PackingShape
    """装箱形状类型 / Packing shape type."""

    dimensions: tuple[float, ...]
    """尺寸元组 / Dimension tuple."""

    quantity: int
    """需求数量 / Demand quantity."""

    @staticmethod
    def create(
        *,
        shape: PackingShape,
        dimensions: tuple[float, ...],
        quantity: int = 1,
    ) -> QuantityGeometryCore:
        """创建数量几何核心 / Create quantity geometry core.

        Args:
            shape: 装箱形状 / Packing shape.
            dimensions: 尺寸元组 / Dimension tuple.
            quantity: 需求数量，默认 1 / Quantity, default 1.

        Returns:
            数量几何核心实例 / QuantityGeometryCore instance.
        """
        return QuantityGeometryCore(
            shape=shape,
            dimensions=dimensions,
            quantity=quantity,
        )

    @property
    def dimension_count(self) -> int:
        """维度数量 / Dimension count.

        Returns:
            尺寸元组长度 / Length of dimension tuple.
        """
        return len(self.dimensions)
