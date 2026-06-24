"""物品上下文 / Item context.

BPP3D 物品域的上下文信息。
Context information for BPP3D item domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.container import (
        Container,
    )


@dataclass(frozen=True)
class ItemContext:
    """物品上下文 / Item context.

    描述物品装箱问题的上下文信息。
    Describes context information for item packing.

    Attributes:
        container: 目标容器 / Target container.
        max_items: 最大物品数 / Maximum item count.
    """

    container: Container
    """目标容器 / Target container."""

    max_items: int
    """最大物品数 / Maximum item count."""

    @staticmethod
    def create(
        *,
        container: Container,
        max_items: int = 1000,
    ) -> ItemContext:
        """创建物品上下文 / Create item context.

        Args:
            container: 目标容器 / Target container.
            max_items: 最大物品数，默认 1000 /
                Max items, default 1000.

        Returns:
            物品上下文实例 / ItemContext instance.
        """
        return ItemContext(
            container=container,
            max_items=max_items,
        )
