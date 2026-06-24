"""模式定义 / Pattern definition.

BPP3D 中的装箱模式定义。
Packing pattern definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pattern:
    """装箱模式 / Packing pattern.

    描述一种可行的装箱排列模式。
    Describes a feasible packing arrangement pattern.

    Attributes:
        pattern_id: 模式标识 / Pattern identifier.
        item_keys: 物品键列表 / Item key list.
        efficiency: 装箱效率 / Packing efficiency.
    """

    pattern_id: str
    """模式标识 / Pattern identifier."""

    item_keys: tuple[str, ...]
    """物品键列表 / Item key list."""

    efficiency: float = 0.0
    """装箱效率 / Packing efficiency."""

    @staticmethod
    def create(
        *,
        pattern_id: str,
        item_keys: tuple[str, ...] = (),
        efficiency: float = 0.0,
    ) -> Pattern:
        """创建模式 / Create pattern.

        Args:
            pattern_id: 模式标识 / Pattern identifier.
            item_keys: 物品键列表，默认空 /
                Item keys, default empty.
            efficiency: 效率，默认 0 / Efficiency, default 0.

        Returns:
            模式实例 / Pattern instance.
        """
        return Pattern(
            pattern_id=pattern_id,
            item_keys=item_keys,
            efficiency=efficiency,
        )

    @property
    def item_count(self) -> int:
        """物品数量 / Item count.

        Returns:
            物品键列表长度 / Length of item key list.
        """
        return len(self.item_keys)
