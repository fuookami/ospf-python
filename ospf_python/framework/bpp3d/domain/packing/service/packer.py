"""装箱器 / Packer.

通用装箱操作接口。
Generic packing operation interface.
"""

from __future__ import annotations

import abc


class Packer(abc.ABC):
    """装箱器 / Packer.

    提供通用的装箱操作接口。
    Provides a generic interface for packing operations.
    """

    @abc.abstractmethod
    def pack_item(
        self,
        item: object,
        container: object,
    ) -> bool:
        """装入物品 / Pack item.

        Args:
            item: 待装物品 / The item to pack.
            container: 目标容器 / The target container.

        Returns:
            装入成功返回 True / True if packing succeeded.
        """
        ...

    @abc.abstractmethod
    def unpack_item(
        self,
        item: object,
        container: object,
    ) -> bool:
        """取出物品 / Unpack item.

        Args:
            item: 待取物品 / The item to unpack.
            container: 来源容器 / The source container.

        Returns:
            取出成功返回 True / True if unpacking succeeded.
        """
        ...

    @abc.abstractmethod
    def get_packed_items(
        self,
        container: object,
    ) -> tuple[object, ...]:
        """获取已装物品 / Get packed items.

        Args:
            container: 容器 / The container.

        Returns:
            已装物品列表 / The list of packed items.
        """
        ...
