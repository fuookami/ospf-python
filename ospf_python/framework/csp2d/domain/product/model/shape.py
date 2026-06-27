"""产品形状模型 / Product shape model.

CSP2D 中的产品形状定义。
Product shape definition in CSP2D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Shape:
    """产品形状 / Product shape.

    描述需要切割的产品形状，包括尺寸和旋转约束。
    Describes a product shape to be cut,
    including dimensions and rotation constraints.

    Attributes:
        shape_key: 形状唯一键 / Shape unique key.
        name: 形状名称 / Shape name.
        width: 形状宽度 / Shape width.
        height: 形状高度 / Shape height.
        rotatable: 是否可旋转 / Whether rotatable.
    """

    shape_key: str
    """形状唯一键 / Shape unique key."""

    name: str
    """形状名称 / Shape name."""

    width: float
    """形状宽度 / Shape width."""

    height: float
    """形状高度 / Shape height."""

    rotatable: bool
    """是否可旋转 / Whether rotatable."""

    @staticmethod
    def create(
        *,
        shape_key: str,
        name: str,
        width: float,
        height: float,
        rotatable: bool = True,
    ) -> Shape:
        """创建形状 / Create shape.

        Args:
            shape_key: 形状唯一键 / Shape unique key.
            name: 形状名称 / Shape name.
            width: 形状宽度 / Shape width.
            height: 形状高度 / Shape height.
            rotatable: 是否可旋转，默认 True /
                Whether rotatable, default True.

        Returns:
            形状实例 / Shape instance.
        """
        return Shape(
            shape_key=shape_key,
            name=name,
            width=width,
            height=height,
            rotatable=rotatable,
        )

    @property
    def area(self) -> float:
        """形状面积 / Shape area.

        Returns:
            宽 x 高 / Width x Height.
        """
        return self.width * self.height

    @property
    def perimeter(self) -> float:
        """形状周长 / Shape perimeter.

        Returns:
            2 x (宽 + 高) / 2 x (Width + Height).
        """
        return 2.0 * (self.width + self.height)

    @property
    def min_dimension(self) -> float:
        """最小边长 / Minimum dimension.

        Returns:
            宽和高中较小值 / Min of width and height.
        """
        return min(self.width, self.height)

    @property
    def max_dimension(self) -> float:
        """最大边长 / Maximum dimension.

        Returns:
            宽和高中较大值 / Max of width and height.
        """
        return max(self.width, self.height)

    def rotations(self) -> tuple[Shape, ...]:
        """获取所有可行旋转 / Get all feasible rotations.

        不可旋转时仅返回自身；
        可旋转时返回原方向和旋转后方向。
        Returns only self when not rotatable; otherwise
        returns original and rotated orientations.

        Returns:
            可行形状元组 / Tuple of feasible shapes.
        """
        if not self.rotatable:
            return (self,)
        rotated = Shape(
            shape_key=self.shape_key,
            name=self.name,
            width=self.height,
            height=self.width,
            rotatable=self.rotatable,
        )
        if self.width == self.height:
            return (self,)
        return (self, rotated)

    def fits_in(self, width: float, height: float) -> bool:
        """检查是否能放入指定容器 / Check if fits in given container.

        考虑所有可行旋转方向。
        Considers all feasible rotations.

        Args:
            width: 容器宽度 / Container width.
            height: 容器高度 / Container height.

        Returns:
            是否能放入 / Whether fits in container.
        """
        if width <= 0.0 or height <= 0.0:
            return False
        for rotation in self.rotations():
            if rotation.width <= width and rotation.height <= height:
                return True
        return False
