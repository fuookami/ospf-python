"""二维板材模型 / 2D sheet material model.

CSP2D 中的二维板材定义。
Sheet material definition in CSP2D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sheet:
    """二维板材 / 2D sheet material.

    描述可用于二维切割的板材，包括尺寸、成本和纹理方向。
    Describes a sheet material available for 2D cutting,
    including dimensions, cost, and grain direction.

    Attributes:
        name: 板材名称 / Sheet name.
        width: 板材宽度 / Sheet width.
        height: 板材高度 / Sheet height.
        cost: 板材单价 / Sheet unit cost.
        grain_direction: 纹理方向（True=纵向） /
            Grain direction (True=vertical).
    """

    name: str
    """板材名称 / Sheet name."""

    width: float
    """板材宽度 / Sheet width."""

    height: float
    """板材高度 / Sheet height."""

    cost: float
    """板材单价 / Sheet unit cost."""

    grain_direction: bool | None = None
    """纹理方向 / Grain direction."""

    @staticmethod
    def create(
        *,
        name: str,
        width: float,
        height: float,
        cost: float = 0.0,
        grain_direction: bool | None = None,
    ) -> Sheet:
        """创建板材 / Create sheet.

        Args:
            name: 板材名称 / Sheet name.
            width: 板材宽度 / Sheet width.
            height: 板材高度 / Sheet height.
            cost: 板材单价，默认 0.0 / Sheet cost, default 0.0.
            grain_direction: 纹理方向 / Grain direction.

        Returns:
            板材实例 / Sheet instance.
        """
        return Sheet(
            name=name,
            width=width,
            height=height,
            cost=cost,
            grain_direction=grain_direction,
        )

    @property
    def area(self) -> float:
        """板材面积 / Sheet area.

        Returns:
            宽 x 高 / Width x Height.
        """
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        """宽高比 / Aspect ratio.

        Returns:
            宽度除以高度 / Width divided by height.
        """
        if self.height == 0.0:
            return float("inf")
        return self.width / self.height

    def can_fit(self, width: float, height: float) -> bool:
        """检查是否能放下指定尺寸 / Check if given size fits.

        考虑纹理方向约束时旋转检查。
        Checks both orientations when grain direction
        is not constrained.

        Args:
            width: 所需宽度 / Required width.
            height: 所需高度 / Required height.

        Returns:
            是否能放下 / Whether the size fits.
        """
        if width <= 0.0 or height <= 0.0:
            return False
        if self.grain_direction is True:
            return width <= self.width and height <= self.height
        if self.grain_direction is False:
            fits_normal = width <= self.width and height <= self.height
            fits_rotated = width <= self.height and height <= self.width
            return fits_normal or fits_rotated
        fits_normal = width <= self.width and height <= self.height
        fits_rotated = width <= self.height and height <= self.width
        return fits_normal or fits_rotated

    def rotate(self) -> Sheet:
        """旋转板材 / Rotate sheet.

        交换宽高，翻转纹理方向。
        Swaps width and height, flips grain direction.

        Returns:
            旋转后的新板材实例 / New rotated sheet instance.
        """
        new_grain: bool | None = None
        if self.grain_direction is not None:
            new_grain = not self.grain_direction
        return Sheet(
            name=self.name,
            width=self.height,
            height=self.width,
            cost=self.cost,
            grain_direction=new_grain,
        )
