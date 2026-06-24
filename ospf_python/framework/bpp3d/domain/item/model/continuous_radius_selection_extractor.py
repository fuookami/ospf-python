"""连续半径选择提取器 / Continuous radius selection extractor.

从优化解中提取圆柱体半径选择。
Extracts cylinder radius selection from optimization solution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuousRadiusSelectionExtractor:
    """连续半径选择提取器。

    从求解结果中提取圆柱体的半径选择值。
    Extracts the radius selection value of a cylinder
    from the solve result.

    Attributes:
        item_key: 物品键 / Item key.
        selected_radius: 选中的半径 / Selected radius.
    """

    item_key: str
    """物品键 / Item key."""

    selected_radius: float
    """选中的半径 / Selected radius."""

    @staticmethod
    def create(
        *,
        item_key: str,
        selected_radius: float,
    ) -> ContinuousRadiusSelectionExtractor:
        """创建提取器 / Create extractor.

        Args:
            item_key: 物品键 / Item key.
            selected_radius: 选中半径 / Selected radius.

        Returns:
            半径选择提取器 / Radius selection extractor.
        """
        return ContinuousRadiusSelectionExtractor(
            item_key=item_key,
            selected_radius=selected_radius,
        )
