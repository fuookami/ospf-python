"""物品高度组合器 / Item height combinator.

BPP3D 中物品高度的组合计算。
Combination calculation for item heights in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ItemHeightCombinator:
    """物品高度组合器。

    计算物品在容器中的高度组合方案。
    Calculates height combination schemes for items
    in a container.

    Attributes:
        container_height: 容器高度 / Container height.
        tolerance: 高度容差 / Height tolerance.
    """

    container_height: float
    """容器高度 / Container height."""

    tolerance: float = 1e-6
    """高度容差 / Height tolerance."""

    @staticmethod
    def create(
        *,
        container_height: float,
        tolerance: float = 1e-6,
    ) -> ItemHeightCombinator:
        """创建组合器 / Create combinator.

        Args:
            container_height: 容器高度 / Container height.
            tolerance: 容差，默认 1e-6 / Tolerance, default 1e-6.

        Returns:
            高度组合器实例 / ItemHeightCombinator.
        """
        return ItemHeightCombinator(
            container_height=container_height,
            tolerance=tolerance,
        )

    def fits_height(self, item_height: float) -> bool:
        """判断物品高度是否适合容器 / Check if item fits.

        Args:
            item_height: 物品高度 / Item height.

        Returns:
            是否适合 / Whether it fits.
        """
        return item_height <= self.container_height + self.tolerance

    def remaining_height(
        self,
        used_height: float,
    ) -> float:
        """计算剩余高度 / Calculate remaining height.

        Args:
            used_height: 已用高度 / Used height.

        Returns:
            剩余高度 / Remaining height.
        """
        return max(0.0, self.container_height - used_height)
