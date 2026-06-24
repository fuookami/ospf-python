"""装载顺序计算器 / Loading order calculator.

BPP3D 中物品装载顺序的计算。
Loading order calculation for items in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadingOrderCalculator:
    """装载顺序计算器。

    计算物品在容器中的最优装载顺序。
    Calculates optimal loading order for items
    in a container.

    Attributes:
        prioritize_large: 优先大物品 / Prioritize large items.
    """

    prioritize_large: bool = True
    """优先大物品 / Prioritize large items."""

    @staticmethod
    def create(
        *,
        prioritize_large: bool = True,
    ) -> LoadingOrderCalculator:
        """创建计算器 / Create calculator.

        Args:
            prioritize_large: 优先大物品，默认 True /
                Prioritize large, default True.

        Returns:
            装载顺序计算器 / LoadingOrderCalculator.
        """
        return LoadingOrderCalculator(
            prioritize_large=prioritize_large,
        )

    def get_sort_key(
        self,
        width: float,
        height: float,
        depth: float,
    ) -> float:
        """获取排序键 / Get sort key.

        Args:
            width: 宽度 / Width.
            height: 高度 / Height.
            depth: 深度 / Depth.

        Returns:
            排序键值 / Sort key value.
        """
        volume = width * height * depth
        if self.prioritize_large:
            return -volume
        return volume
