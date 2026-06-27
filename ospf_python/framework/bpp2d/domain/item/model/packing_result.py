"""装箱结果模型 / Packing result model.

定义二维装箱中单个物品的放置结果。
Defines placement result for a single item in 2D
bin packing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PackingResult:
    """装箱结果 / Packing result.

    描述一个物品在二维容器中的放置结果。
    Describes the result of placing an item in a 2D
    container.

    Attributes:
        item_key: 物品标识 / Item identifier.
        x: 放置位置 x 坐标 / Placement x coordinate.
        y: 放置位置 y 坐标 / Placement y coordinate.
        placed_width: 放置后宽度 / Placed width.
        placed_height: 放置后高度 / Placed height.
        rotated: 是否旋转放置 / Whether placed rotated.
    """

    item_key: str
    """物品标识 / Item identifier."""

    x: float
    """放置位置 x 坐标 / Placement x coordinate."""

    y: float
    """放置位置 y 坐标 / Placement y coordinate."""

    placed_width: float
    """放置后宽度 / Placed width."""

    placed_height: float
    """放置后高度 / Placed height."""

    rotated: bool = False
    """是否旋转放置，默认否 / Rotated, default no."""

    @staticmethod
    def create(
        *,
        item_key: str,
        x: float,
        y: float,
        placed_width: float,
        placed_height: float,
        rotated: bool = False,
    ) -> PackingResult:
        """创建装箱结果 / Create packing result.

        Args:
            item_key: 物品标识 / Item identifier.
            x: x 坐标 / X coordinate.
            y: y 坐标 / Y coordinate.
            placed_width: 放置宽度 / Placed width.
            placed_height: 放置高度 / Placed height.
            rotated: 是否旋转，默认否 / Rotated, default no.

        Returns:
            装箱结果实例 / PackingResult instance.
        """
        return PackingResult(
            item_key=item_key,
            x=x,
            y=y,
            placed_width=placed_width,
            placed_height=placed_height,
            rotated=rotated,
        )

    @property
    def right(self) -> float:
        """右边界坐标 / Right boundary coordinate.

        Returns:
            x 坐标加放置宽度 / X plus placed width.
        """
        return self.x + self.placed_width

    @property
    def top(self) -> float:
        """上边界坐标 / Top boundary coordinate.

        Returns:
            y 坐标加放置高度 / Y plus placed height.
        """
        return self.y + self.placed_height

    @property
    def area(self) -> float:
        """放置面积 / Placement area.

        Returns:
            放置宽度乘以放置高度 /
            Placed width times placed height.
        """
        return self.placed_width * self.placed_height

    @property
    def center_x(self) -> float:
        """中心 x 坐标 / Center x coordinate.

        Returns:
            x 坐标加放置宽度的一半 /
            X plus half of placed width.
        """
        return self.x + self.placed_width / 2.0

    @property
    def center_y(self) -> float:
        """中心 y 坐标 / Center y coordinate.

        Returns:
            y 坐标加放置高度的一半 /
            Y plus half of placed height.
        """
        return self.y + self.placed_height / 2.0

    def overlaps_with(self, other: PackingResult) -> bool:
        """检查与另一结果是否重叠 / Check overlap with another.

        使用轴对齐包围盒检测重叠。
        Uses axis-aligned bounding box for overlap detection.

        Args:
            other: 另一个装箱结果 / Another packing result.

        Returns:
            存在重叠返回 True / True if overlap exists.
        """
        if self.right <= other.x or other.right <= self.x:
            return False
        return not (self.top <= other.y or other.top <= self.y)

    def contains_point(
        self,
        px: float,
        py: float,
    ) -> bool:
        """检查是否包含指定点 / Check if contains a point.

        Args:
            px: 点的 x 坐标 / Point x coordinate.
            py: 点的 y 坐标 / Point y coordinate.

        Returns:
            包含该点返回 True / True if contains the point.
        """
        return self.x <= px < self.right and self.y <= py < self.top
