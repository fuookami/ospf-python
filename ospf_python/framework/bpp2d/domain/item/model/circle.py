"""圆形物品模型 / Circle item model.

定义二维装箱中的圆形物品。
Defines circular items for 2D bin packing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Circle:
    """圆形物品 / Circle item.

    描述二维装箱中需要放置的圆形物品。
    Describes a circular item to be placed in 2D
    bin packing.

    Attributes:
        item_key: 物品唯一标识 / Unique item identifier.
        radius: 物品半径 / Item radius.
        weight: 物品重量 / Item weight.
    """

    item_key: str
    """物品唯一标识 / Unique item identifier."""

    radius: float
    """物品半径 / Item radius."""

    weight: float = 0.0
    """物品重量，默认 0 / Item weight, default 0."""

    @staticmethod
    def create(
        *,
        item_key: str,
        radius: float,
        weight: float = 0.0,
    ) -> Circle:
        """创建圆形物品 / Create circle item.

        Args:
            item_key: 物品唯一标识 / Unique item identifier.
            radius: 物品半径 / Item radius.
            weight: 物品重量，默认 0 / Weight, default 0.

        Returns:
            圆形物品实例 / Circle instance.
        """
        return Circle(
            item_key=item_key,
            radius=radius,
            weight=weight,
        )

    @property
    def diameter(self) -> float:
        """物品直径 / Item diameter.

        Returns:
            半径乘以 2 / Radius times 2.
        """
        return 2.0 * self.radius

    @property
    def area(self) -> float:
        """物品面积 / Item area.

        Returns:
            pi 乘以半径的平方 / Pi times radius squared.
        """
        return math.pi * self.radius * self.radius

    @property
    def circumference(self) -> float:
        """物品周长 / Item circumference.

        Returns:
            2 乘以 pi 乘以半径 / 2 times pi times radius.
        """
        return 2.0 * math.pi * self.radius

    @property
    def bounding_box_width(self) -> float:
        """包围盒宽度 / Bounding box width.

        Returns:
            直径 / Diameter.
        """
        return self.diameter

    @property
    def bounding_box_height(self) -> float:
        """包围盒高度 / Bounding box height.

        Returns:
            直径 / Diameter.
        """
        return self.diameter

    def fits_in(
        self,
        container_width: float,
        container_height: float,
    ) -> bool:
        """检查是否能放入容器 / Check if fits in container.

        圆形物品在任何方向上尺寸相同，只需检查直径。
        Circular items have the same size in all directions,
        so only the diameter needs checking.

        Args:
            container_width: 容器宽度 / Container width.
            container_height: 容器高度 / Container height.

        Returns:
            能放入返回 True / True if fits.
        """
        return self.diameter <= container_width and self.diameter <= container_height

    def overlaps_with(
        self,
        other: Circle,
        self_x: float = 0.0,
        self_y: float = 0.0,
        other_x: float = 0.0,
        other_y: float = 0.0,
    ) -> bool:
        """检查与另一圆形是否重叠 / Check overlap with another.

        基于圆心距离判断是否重叠。
        Determines overlap based on center-to-center distance.

        Args:
            other: 另一个圆形物品 / Another circle item.
            self_x: 自身 X 坐标，默认 0 / Self X, default 0.
            self_y: 自身 Y 坐标，默认 0 / Self Y, default 0.
            other_x: 另一圆形 X 坐标，默认 0 / Other X, default 0.
            other_y: 另一圆形 Y 坐标，默认 0 / Other Y, default 0.

        Returns:
            重叠返回 True / True if circles overlap.
        """
        dx = self_x - other_x
        dy = self_y - other_y
        center_dist_sq = dx * dx + dy * dy
        radius_sum = self.radius + other.radius
        return center_dist_sq < radius_sum * radius_sum

    def distance_to(
        self,
        other: Circle,
        self_x: float = 0.0,
        self_y: float = 0.0,
        other_x: float = 0.0,
        other_y: float = 0.0,
    ) -> float:
        """计算到另一圆形的最小距离 / Calc min distance to other.

        圆心距离减去两半径之和。
        Center-to-center distance minus sum of radii.

        Args:
            other: 另一个圆形物品 / Another circle item.
            self_x: 自身 X 坐标，默认 0 / Self X, default 0.
            self_y: 自身 Y 坐标，默认 0 / Self Y, default 0.
            other_x: 另一圆形 X 坐标，默认 0 / Other X, default 0.
            other_y: 另一圆形 Y 坐标，默认 0 / Other Y, default 0.

        Returns:
            最小距离（可能为负表示重叠）/
            Min distance (negative if overlap).
        """
        dx = self_x - other_x
        dy = self_y - other_y
        center_dist = math.sqrt(dx * dx + dy * dy)
        return center_dist - (self.radius + other.radius)
