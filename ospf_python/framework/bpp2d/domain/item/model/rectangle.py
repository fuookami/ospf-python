"""矩形物品模型 / Rectangle item model.

定义二维装箱中的矩形物品。
Defines rectangular items for 2D bin packing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rectangle:
    """矩形物品 / Rectangle item.

    描述二维装箱中需要放置的矩形物品。
    Describes a rectangular item to be placed in 2D
    bin packing.

    Attributes:
        item_key: 物品唯一标识 / Unique item identifier.
        width: 物品宽度 / Item width.
        height: 物品高度 / Item height.
        weight: 物品重量 / Item weight.
        can_rotate: 是否允许旋转 / Whether rotation
            is allowed.
    """

    item_key: str
    """物品唯一标识 / Unique item identifier."""

    width: float
    """物品宽度 / Item width."""

    height: float
    """物品高度 / Item height."""

    weight: float = 0.0
    """物品重量，默认 0 / Item weight, default 0."""

    can_rotate: bool = False
    """是否允许旋转，默认否 / Rotation allowed, default no."""

    @staticmethod
    def create(
        *,
        item_key: str,
        width: float,
        height: float,
        weight: float = 0.0,
        can_rotate: bool = False,
    ) -> Rectangle:
        """创建矩形物品 / Create rectangle item.

        Args:
            item_key: 物品唯一标识 / Unique item identifier.
            width: 物品宽度 / Item width.
            height: 物品高度 / Item height.
            weight: 物品重量，默认 0 / Weight, default 0.
            can_rotate: 是否允许旋转，默认否 /
                Rotation allowed, default no.

        Returns:
            矩形物品实例 / Rectangle instance.
        """
        return Rectangle(
            item_key=item_key,
            width=width,
            height=height,
            weight=weight,
            can_rotate=can_rotate,
        )

    @property
    def area(self) -> float:
        """物品面积 / Item area.

        Returns:
            宽度乘以高度 / Width times height.
        """
        return self.width * self.height

    @property
    def perimeter(self) -> float:
        """物品周长 / Item perimeter.

        Returns:
            2 乘以（宽度加高度）/ 2 times (width + height).
        """
        return 2.0 * (self.width + self.height)

    @property
    def aspect_ratio(self) -> float:
        """宽高比 / Aspect ratio.

        Returns:
            宽度除以高度 / Width divided by height.
        """
        if self.height == 0.0:
            return float("inf")
        return self.width / self.height

    def rotated(self) -> Rectangle:
        """获取旋转后的矩形 / Get rotated rectangle.

        交换宽度和高度，返回新的矩形实例。
        Swaps width and height, returns a new instance.

        Returns:
            旋转后的矩形 / Rotated rectangle.
        """
        return Rectangle(
            item_key=self.item_key,
            width=self.height,
            height=self.width,
            weight=self.weight,
            can_rotate=self.can_rotate,
        )

    def fits_in(
        self,
        container_width: float,
        container_height: float,
    ) -> bool:
        """检查是否能放入容器 / Check if fits in container.

        考虑旋转的情况下检查物品是否可以放入容器。
        Checks whether the item can fit, considering rotation.

        Args:
            container_width: 容器宽度 / Container width.
            container_height: 容器高度 / Container height.

        Returns:
            能放入返回 True / True if fits.
        """
        fits_normal = self.width <= container_width and self.height <= container_height
        fits_rotated = bool(
            self.can_rotate
            and (self.height <= container_width and self.width <= container_height)
        )
        return fits_normal or fits_rotated
