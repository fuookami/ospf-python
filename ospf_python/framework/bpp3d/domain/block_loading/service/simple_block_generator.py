"""简单块生成器 / Simple block generator.

生成单一物品类型的简单块。
Generates simple blocks of a single item type.
"""

from __future__ import annotations

import abc


class SimpleBlockGenerator(abc.ABC):
    """简单块生成器 / Simple block generator.

    根据单一物品类型生成规则块。
    Generates regular blocks from a single item type.
    """

    @abc.abstractmethod
    def generate(self, item: object) -> object:
        """生成简单块 / Generate simple block.

        Args:
            item: 物品模板 / The item template.

        Returns:
            生成的简单块 / The generated simple block.
        """
        ...

    @abc.abstractmethod
    def calculate_quantity(
        self,
        item: object,
        container: object,
    ) -> int:
        """计算可装载数量 / Calculate loadable quantity.

        Args:
            item: 物品模板 / The item template.
            container: 目标容器 / The target container.

        Returns:
            可装载数量 / The loadable quantity.
        """
        ...
