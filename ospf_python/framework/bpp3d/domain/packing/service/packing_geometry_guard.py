"""装箱几何保护 / Packing geometry guard.

保护装箱操作的几何完整性。
Protects geometric integrity of packing operations.
"""

from __future__ import annotations

import abc


class PackingGeometryGuard(abc.ABC):
    """装箱几何保护 / Packing geometry guard.

    在装箱前验证几何约束。
    Validates geometric constraints before packing.
    """

    @abc.abstractmethod
    def validate_placement(
        self,
        item: object,
        position: object,
        container: object,
    ) -> bool:
        """验证放置 / Validate placement.

        Args:
            item: 待放置物品 / The item to place.
            position: 放置位置 / The placement position.
            container: 目标容器 / The target container.

        Returns:
            放置有效返回 True / True if placement is valid.
        """
        ...

    @abc.abstractmethod
    def get_violations(
        self,
        item: object,
        position: object,
        container: object,
    ) -> tuple[str, ...]:
        """获取违规信息 / Get violation messages.

        Args:
            item: 待放置物品 / The item to place.
            position: 放置位置 / The placement position.
            container: 目标容器 / The target container.

        Returns:
            违规信息列表 / The list of violation messages.
        """
        ...
