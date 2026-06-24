"""物料装箱器 / Material packer.

执行物料到容器的装箱操作。
Executes packing operations from materials to containers.
"""

from __future__ import annotations

import abc


class MaterialPacker(abc.ABC):
    """物料装箱器 / Material packer.

    将物料装入容器并生成装箱方案。
    Packs materials into containers and generates packing
    solutions.
    """

    @abc.abstractmethod
    def pack(
        self,
        material: object,
        container: object,
    ) -> bool:
        """装箱 / Pack.

        Args:
            material: 待装物料 / The material to pack.
            container: 目标容器 / The target container.

        Returns:
            装箱成功返回 True / True if packing succeeded.
        """
        ...

    @abc.abstractmethod
    def can_pack(
        self,
        material: object,
        container: object,
    ) -> bool:
        """检查是否可装箱 / Check if packable.

        Args:
            material: 待装物料 / The material to pack.
            container: 目标容器 / The target container.

        Returns:
            可装箱返回 True / True if packable.
        """
        ...

    @abc.abstractmethod
    def get_remaining_space(self, container: object) -> object:
        """获取剩余空间 / Get remaining space.

        Args:
            container: 容器 / The container.

        Returns:
            剩余空间 / The remaining space.
        """
        ...
