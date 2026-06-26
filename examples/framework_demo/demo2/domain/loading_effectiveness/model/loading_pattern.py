"""装载方案模型。

Loading pattern model representing a complete loading arrangement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadingPattern:
    """装载方案。

    Represents a complete loading pattern with item placements and
    an associated efficiency score.

    Attributes:
        pattern_id: 方案唯一标识 / Unique pattern identifier
        items: 装载物品ID列表 / List of loaded item IDs
        positions: 物品位置映射 / Mapping of item_id to (x, y, z) coordinates
        efficiency: 方案效率得分 (0-1) / Pattern efficiency score (0-1)
    """

    pattern_id: str
    items: tuple[str, ...]
    positions: dict[str, tuple[float, float, float]]
    efficiency: float

    def item_count(self) -> int:
        """计算装载物品数量。

        Returns:
            int: 物品数量 / Number of loaded items
        """
        return len(self.items)

    def is_valid(self) -> bool:
        """验证方案一致性。

        Checks that all items have assigned positions.

        Returns:
            bool: 方案是否有效 / Whether the pattern is valid
        """
        return all(item in self.positions for item in self.items)

    def bounding_box(
        self,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """计算方案的包围盒。

        Computes the axis-aligned bounding box of all item positions.

        Returns:
            tuple: (最小坐标, 最大坐标) / (min_coords, max_coords)
        """
        if not self.positions:
            return ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))

        xs = [p[0] for p in self.positions.values()]
        ys = [p[1] for p in self.positions.values()]
        zs = [p[2] for p in self.positions.values()]
        return (
            (min(xs), min(ys), min(zs)),
            (max(xs), max(ys), max(zs)),
        )
