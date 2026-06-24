"""需求约束 / Demand constraint.

确保满足物品需求量。
Ensures item demand quantities are met.
"""

from __future__ import annotations

import abc


class DemandConstraint(abc.ABC):
    """需求约束 / Demand constraint.

    验证层分配方案满足需求约束。
    Validates that layer assignment solutions satisfy
    demand constraints.
    """

    @abc.abstractmethod
    def is_satisfied(
        self,
        supplied: int,
        demanded: int,
    ) -> bool:
        """检查约束满足 / Check constraint satisfaction.

        Args:
            supplied: 已供应量 / The supplied quantity.
            demanded: 需求量 / The demanded quantity.

        Returns:
            约束满足返回 True / True if constraint satisfied.
        """
        ...

    @abc.abstractmethod
    def get_shortfall(
        self,
        supplied: int,
        demanded: int,
    ) -> int:
        """计算缺口 / Calculate shortfall.

        Args:
            supplied: 已供应量 / The supplied quantity.
            demanded: 需求量 / The demanded quantity.

        Returns:
            缺口数量（非负） / Shortfall quantity (non-negative).
        """
        ...
