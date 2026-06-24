"""块定义 / Block definition.

BPP3D 中的块（物品组合）定义。
Block (item combination) definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Block:
    """块 / Block.

    描述 BPP3D 中的块，由多个相同物品组成。
    Describes a block in BPP3D, composed of multiple
    identical items.

    Attributes:
        block_id: 块标识 / Block identifier.
        item_key: 物品键 / Item key.
        count: 物品数量 / Item count.
    """

    block_id: str
    """块标识 / Block identifier."""

    item_key: str
    """物品键 / Item key."""

    count: int
    """物品数量 / Item count."""

    @staticmethod
    def create(
        *,
        block_id: str,
        item_key: str,
        count: int = 1,
    ) -> Block:
        """创建块 / Create block.

        Args:
            block_id: 块标识 / Block identifier.
            item_key: 物品键 / Item key.
            count: 物品数量，默认 1 / Count, default 1.

        Returns:
            块实例 / Block instance.
        """
        return Block(
            block_id=block_id,
            item_key=item_key,
            count=count,
        )
