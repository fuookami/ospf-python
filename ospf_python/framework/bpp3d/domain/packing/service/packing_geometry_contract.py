"""装箱几何契约 / Packing geometry contract.

定义装箱操作的几何约束契约。
Defines geometric constraint contracts for packing operations.
"""

from __future__ import annotations

import abc


class PackingGeometryContract(abc.ABC):
    """装箱几何契约 / Packing geometry contract.

    验证装箱操作满足几何约束。
    Validates that packing operations satisfy geometric
    constraints.
    """

    @abc.abstractmethod
    def check_overlap(
        self,
        item1: object,
        item2: object,
    ) -> bool:
        """检查重叠 / Check overlap.

        Args:
            item1: 物品 1 / Item 1.
            item2: 物品 2 / Item 2.

        Returns:
            存在重叠返回 True / True if overlap exists.
        """
        ...

    @abc.abstractmethod
    def check_boundary(
        self,
        item: object,
        container: object,
    ) -> bool:
        """检查边界 / Check boundary.

        Args:
            item: 物品 / The item.
            container: 容器 / The container.

        Returns:
            在边界内返回 True / True if within boundary.
        """
        ...

    @abc.abstractmethod
    def check_support(
        self,
        item: object,
        below_items: tuple[object, ...],
    ) -> bool:
        """检查支撑 / Check support.

        Args:
            item: 物品 / The item.
            below_items: 下方物品 / Items below.

        Returns:
            有足够支撑返回 True / True if adequately supported.
        """
        ...
