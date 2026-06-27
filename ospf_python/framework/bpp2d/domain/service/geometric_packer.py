"""几何装箱器 / Geometric packer.

实现二维装箱的几何放置逻辑。
Implements geometric placement logic for 2D bin packing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.bpp2d.domain.item.error.bpp2d_errors import (
    Bpp2dErrors,
)
from ospf_python.framework.bpp2d.domain.item.model.packing_result import (
    PackingResult,
)
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import (
    Failed,
    Ok,
    Result,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp2d.domain.item.model.circle import (
        Circle,
    )
    from ospf_python.framework.bpp2d.domain.item.model.rectangle import (
        Rectangle,
    )


@dataclass(frozen=True)
class GeometricPacker:
    """几何装箱器 / Geometric packer.

    执行二维装箱的几何放置计算，包括边界检测和
    重叠检测。
    Performs geometric placement calculations for 2D
    bin packing, including boundary and overlap checks.

    Attributes:
        container_width: 容器宽度 / Container width.
        container_height: 容器高度 / Container height.
    """

    container_width: float
    """容器宽度 / Container width."""

    container_height: float
    """容器高度 / Container height."""

    @staticmethod
    def create(
        *,
        container_width: float,
        container_height: float,
    ) -> GeometricPacker:
        """创建几何装箱器 / Create geometric packer.

        Args:
            container_width: 容器宽度 / Container width.
            container_height: 容器高度 / Container height.

        Returns:
            几何装箱器实例 / GeometricPacker instance.
        """
        return GeometricPacker(
            container_width=container_width,
            container_height=container_height,
        )

    def place_rectangle(
        self,
        rectangle: Rectangle,
        x: float,
        y: float,
        *,
        rotate: bool = False,
    ) -> Result[PackingResult, str, Err[str]]:
        """放置矩形物品 / Place a rectangle item.

        验证放置位置并返回装箱结果。
        Validates placement and returns packing result.

        Args:
            rectangle: 矩形物品 / Rectangle item.
            x: 放置 x 坐标 / Placement x.
            y: 放置 y 坐标 / Placement y.
            rotate: 是否旋转 / Whether to rotate.

        Returns:
            装箱结果或错误 / Packing result or error.
        """
        w = rectangle.height if rotate else rectangle.width
        h = rectangle.width if rotate else rectangle.height

        if x < 0.0 or y < 0.0:
            return Failed(
                Err(
                    _code=Bpp2dErrors.INVALID_POSITION.value,
                    _message=(
                        f"位置不能为负: ({x}, {y}) / "
                        f"Position cannot be negative: "
                        f"({x}, {y})"
                    ),
                )
            )

        if x + w > self.container_width:
            return Failed(
                Err(
                    _code=(Bpp2dErrors.BOUNDARY_VIOLATED.value),
                    _message=(
                        f"超出容器右边界: "
                        f"x({x}) + w({w}) > "
                        f"{self.container_width} / "
                        f"Exceeds right boundary: "
                        f"x({x}) + w({w}) > "
                        f"{self.container_width}"
                    ),
                )
            )

        if y + h > self.container_height:
            return Failed(
                Err(
                    _code=(Bpp2dErrors.BOUNDARY_VIOLATED.value),
                    _message=(
                        f"超出容器上边界: "
                        f"y({y}) + h({h}) > "
                        f"{self.container_height} / "
                        f"Exceeds top boundary: "
                        f"y({y}) + h({h}) > "
                        f"{self.container_height}"
                    ),
                )
            )

        return Ok(
            PackingResult.create(
                item_key=rectangle.item_key,
                x=x,
                y=y,
                placed_width=w,
                placed_height=h,
                rotated=rotate,
            )
        )

    def place_circle(
        self,
        circle: Circle,
        x: float,
        y: float,
    ) -> Result[PackingResult, str, Err[str]]:
        """放置圆形物品 / Place a circle item.

        验证放置位置并返回装箱结果。
        Validates placement and returns packing result.

        Args:
            circle: 圆形物品 / Circle item.
            x: 圆心 x 坐标 / Center x coordinate.
            y: 圆心 y 坐标 / Center y coordinate.

        Returns:
            装箱结果或错误 / Packing result or error.
        """
        r = circle.radius

        if x - r < 0.0 or y - r < 0.0:
            return Failed(
                Err(
                    _code=Bpp2dErrors.INVALID_POSITION.value,
                    _message=(
                        f"圆形超出左/下边界: "
                        f"center({x},{y}), r({r}) / "
                        f"Circle exceeds left/bottom: "
                        f"center({x},{y}), r({r})"
                    ),
                )
            )

        if x + r > self.container_width:
            return Failed(
                Err(
                    _code=(Bpp2dErrors.BOUNDARY_VIOLATED.value),
                    _message=(
                        f"圆形超出右边界: "
                        f"x({x}) + r({r}) > "
                        f"{self.container_width} / "
                        f"Circle exceeds right: "
                        f"x({x}) + r({r}) > "
                        f"{self.container_width}"
                    ),
                )
            )

        if y + r > self.container_height:
            return Failed(
                Err(
                    _code=(Bpp2dErrors.BOUNDARY_VIOLATED.value),
                    _message=(
                        f"圆形超出上边界: "
                        f"y({y}) + r({r}) > "
                        f"{self.container_height} / "
                        f"Circle exceeds top: "
                        f"y({y}) + r({r}) > "
                        f"{self.container_height}"
                    ),
                )
            )

        return Ok(
            PackingResult.create(
                item_key=circle.item_key,
                x=x - r,
                y=y - r,
                placed_width=circle.diameter,
                placed_height=circle.diameter,
            )
        )

    def check_no_overlap(
        self,
        placed: tuple[PackingResult, ...],
    ) -> Result[None, str, Err[str]]:
        """检查已放置物品无重叠 / Check no overlap among placed.

        Args:
            placed: 已放置物品结果 / Placed item results.

        Returns:
            无重叠返回成功，否则返回失败。
            Success if no overlap, failure otherwise.
        """
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                if placed[i].overlaps_with(placed[j]):
                    return Failed(
                        Err(
                            _code=(Bpp2dErrors.OVERLAP_DETECTED.value),
                            _message=(
                                f"物品 {placed[i].item_key} "
                                f"与 "
                                f"{placed[j].item_key} "
                                f"重叠 / "
                                f"Items "
                                f"{placed[i].item_key} "
                                f"and "
                                f"{placed[j].item_key} "
                                f"overlap"
                            ),
                        )
                    )
        return Ok(None)

    @property
    def container_area(self) -> float:
        """容器面积 / Container area.

        Returns:
            宽度乘以高度 / Width times height.
        """
        return self.container_width * self.container_height
