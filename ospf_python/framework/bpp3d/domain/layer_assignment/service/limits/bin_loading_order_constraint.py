"""箱装载顺序约束 / Bin loading order constraint.

确保层按正确顺序装载。
Ensures layers are loaded in the correct order.
"""

from __future__ import annotations

import abc


class BinLoadingOrderConstraint(abc.ABC):
    """箱装载顺序约束 / Bin loading order constraint.

    验证层的装载顺序满足物理约束。
    Validates that layer loading order satisfies physical
    constraints.
    """

    @abc.abstractmethod
    def is_valid_order(
        self,
        layers: tuple[object, ...],
    ) -> bool:
        """检查顺序有效性 / Check order validity.

        Args:
            layers: 按顺序排列的层 / Layers in order.

        Returns:
            顺序有效返回 True / True if order is valid.
        """
        ...

    @abc.abstractmethod
    def sort_layers(
        self,
        layers: tuple[object, ...],
    ) -> tuple[object, ...]:
        """排序层 / Sort layers.

        Args:
            layers: 待排序的层 / Layers to sort.

        Returns:
            排序后的层 / Sorted layers.
        """
        ...
