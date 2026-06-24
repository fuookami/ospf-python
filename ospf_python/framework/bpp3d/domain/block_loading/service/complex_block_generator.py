"""复杂块生成器 / Complex block generator.

生成包含多种物品组合的复杂块。
Generates complex blocks containing multiple item combinations.
"""

from __future__ import annotations

import abc


class ComplexBlockGenerator(abc.ABC):
    """复杂块生成器 / Complex block generator.

    根据物品集合生成复杂的组合块。
    Generates complex combined blocks from item sets.
    """

    @abc.abstractmethod
    def generate(self, items: tuple[object, ...]) -> tuple[object, ...]:
        """生成复杂块 / Generate complex blocks.

        Args:
            items: 物品集合 / The item set.

        Returns:
            生成的复杂块列表 / The generated complex blocks.
        """
        ...

    @abc.abstractmethod
    def is_valid_combination(
        self,
        items: tuple[object, ...],
    ) -> bool:
        """检查组合有效性 / Check combination validity.

        Args:
            items: 物品组合 / The item combination.

        Returns:
            有效组合返回 True / True if valid combination.
        """
        ...
