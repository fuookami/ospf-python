"""箱子定义 / Bin definition.

BPP1D 中的一维箱子定义。
One-dimensional bin definition in BPP1D.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.item.model.item import Item


@dataclass(frozen=True)
class Bin:
    """箱子 / Bin.

    描述 BPP1D 中用于装物品的箱子。
    Describes a bin used to pack items in BPP1D.

    Attributes:
        bin_key: 箱子键 / Bin key.
        capacity: 箱子容量 / Bin capacity.
        items: 已装入物品 / Packed items.
    """

    bin_key: str
    """箱子键 / Bin key."""

    capacity: float
    """箱子容量 / Bin capacity."""

    items: tuple[Item, ...] = field(
        default_factory=tuple,
    )
    """已装入物品 / Packed items."""

    @staticmethod
    def create(
        *,
        bin_key: str,
        capacity: float,
        items: tuple[Item, ...] = (),
    ) -> Bin:
        """创建箱子 / Create bin.

        Args:
            bin_key: 箱子键 / Bin key.
            capacity: 箱子容量 / Bin capacity.
            items: 已装入物品，默认空 / Packed items, default empty.

        Returns:
            箱子实例 / Bin instance.
        """
        return Bin(
            bin_key=bin_key,
            capacity=capacity,
            items=items,
        )

    @property
    def used_capacity(self) -> float:
        """已用容量 / Used capacity.

        Returns:
            所有已装入物品宽度之和。
            Sum of widths of all packed items.
        """
        return sum(item.width for item in self.items)

    @property
    def remaining_capacity(self) -> float:
        """剩余容量 / Remaining capacity.

        Returns:
            箱子容量减去已用容量。
            Bin capacity minus used capacity.
        """
        return max(0.0, self.capacity - self.used_capacity)

    @property
    def is_full(self) -> bool:
        """是否已满 / Whether full.

        Returns:
            剩余容量是否为零。
            Whether remaining capacity is zero.
        """
        return self.remaining_capacity <= 1e-9

    @property
    def total_weight(self) -> float:
        """总重量 / Total weight.

        Returns:
            所有已装入物品重量之和。
            Sum of weights of all packed items.
        """
        return sum(item.weight for item in self.items)

    @property
    def item_count(self) -> int:
        """物品数量 / Item count.

        Returns:
            已装入物品的数量。
            Number of packed items.
        """
        return len(self.items)
