"""模式定义 / Schema definition.

BPP3D 中的装箱方案模式。
Packing scheme schema in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Schema:
    """装箱方案模式 / Packing scheme schema.

    描述一个完整的装箱方案。
    Describes a complete packing scheme.

    Attributes:
        schema_id: 方案标识 / Schema identifier.
        bin_count: 使用箱子数 / Number of bins used.
        total_items: 总装箱物品数 / Total items packed.
    """

    schema_id: str
    """方案标识 / Schema identifier."""

    bin_count: int
    """使用箱子数 / Number of bins used."""

    total_items: int = 0
    """总装箱物品数 / Total items packed."""

    @staticmethod
    def create(
        *,
        schema_id: str,
        bin_count: int,
        total_items: int = 0,
    ) -> Schema:
        """创建方案模式 / Create schema.

        Args:
            schema_id: 方案标识 / Schema identifier.
            bin_count: 箱子数 / Bin count.
            total_items: 总物品数，默认 0 /
                Total items, default 0.

        Returns:
            方案模式实例 / Schema instance.
        """
        return Schema(
            schema_id=schema_id,
            bin_count=bin_count,
            total_items=total_items,
        )

    @property
    def average_items_per_bin(self) -> float:
        """每箱平均物品数 / Average items per bin.

        Returns:
            总物品除以箱子数 / Total items over bin count.
        """
        if self.bin_count == 0:
            return 0.0
        return self.total_items / self.bin_count
