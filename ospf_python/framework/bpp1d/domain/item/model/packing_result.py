"""装箱结果 / Packing result.

BPP1D 中单个物品的装箱结果。
Packing result for a single item in BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.item.model.item import Item


@dataclass(frozen=True)
class PackingResult:
    """装箱结果 / Packing result.

    描述一个物品被装入箱子的结果。
    Describes the result of packing an item into a bin.

    Attributes:
        item: 被装入的物品 / The packed item.
        bin_key: 目标箱子键 / Target bin key.
        position: 物品在箱子中的位置 / Item position in bin.
    """

    item: Item
    """被装入的物品 / The packed item."""

    bin_key: str
    """目标箱子键 / Target bin key."""

    position: float = 0.0
    """物品在箱子中的位置，默认 0 / Position in bin, default 0."""

    @staticmethod
    def create(
        *,
        item: Item,
        bin_key: str,
        position: float = 0.0,
    ) -> PackingResult:
        """创建装箱结果 / Create packing result.

        Args:
            item: 被装入的物品 / The packed item.
            bin_key: 目标箱子键 / Target bin key.
            position: 位置，默认 0 / Position, default 0.

        Returns:
            装箱结果实例 / PackingResult instance.
        """
        return PackingResult(
            item=item,
            bin_key=bin_key,
            position=position,
        )

    @property
    def end_position(self) -> float:
        """结束位置 / End position.

        Returns:
            位置加物品宽度。
            Position plus item width.
        """
        return self.position + self.item.width
