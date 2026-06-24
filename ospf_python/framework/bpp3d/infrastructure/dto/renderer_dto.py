"""渲染器数据传输对象 / Renderer data transfer object.

BPP3D 渲染器的 DTO 定义。
Renderer DTO definition for BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.placement import (
        Placement,
    )


@dataclass(frozen=True)
class RendererDTO:
    """渲染器数据传输对象 / Renderer DTO.

    用于将装箱结果传递给渲染器。
    Used to pass packing results to the renderer.

    Attributes:
        item_id: 物品标识 / Item identifier.
        placement: 放置位置 / Placement position.
        width: 渲染宽度 / Render width.
        height: 渲染高度 / Render height.
        depth: 渲染深度 / Render depth.
    """

    item_id: str
    """物品标识 / Item identifier."""

    placement: Placement
    """放置位置 / Placement position."""

    width: float
    """渲染宽度 / Render width."""

    height: float
    """渲染高度 / Render height."""

    depth: float
    """渲染深度 / Render depth."""

    @staticmethod
    def create(
        *,
        item_id: str,
        placement: Placement,
        width: float,
        height: float,
        depth: float,
    ) -> RendererDTO:
        """创建渲染器 DTO / Create renderer DTO.

        Args:
            item_id: 物品标识 / Item identifier.
            placement: 放置位置 / Placement.
            width: 渲染宽度 / Render width.
            height: 渲染高度 / Render height.
            depth: 渲染深度 / Render depth.

        Returns:
            渲染器 DTO 实例 / RendererDTO instance.
        """
        return RendererDTO(
            item_id=item_id,
            placement=placement,
            width=width,
            height=height,
            depth=depth,
        )
