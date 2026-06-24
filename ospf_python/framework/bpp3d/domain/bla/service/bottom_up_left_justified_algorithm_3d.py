"""三维自底向上左对齐算法 / 3D bottom-up left-justified algorithm.

扩展二维 BLA 算法以支持三维装箱。
Extends the 2D BLA algorithm to support three-dimensional
bin packing.
"""

from __future__ import annotations

import abc


class BottomUpLeftJustifiedAlgorithm3D(abc.ABC):
    """三维自底向上左对齐算法 / 3D bottom-up left-justified algorithm.

    在三维空间中按自底向上、左对齐策略放置物品。
    Places items in 3D space using a bottom-up,
    left-justified strategy.
    """

    @abc.abstractmethod
    def pack(self, items: tuple[object, ...]) -> object:
        """执行三维装箱 / Execute 3D packing.

        Args:
            items: 待装箱物品 / Items to pack.

        Returns:
            三维装箱方案 / The 3D packing solution.
        """
        ...

    @abc.abstractmethod
    def find_feasible_position(
        self,
        item: object,
    ) -> object | None:
        """查找可行位置 / Find feasible position.

        Args:
            item: 待放置物品 / The item to place.

        Returns:
            可行位置或 None / Feasible position or None.
        """
        ...
