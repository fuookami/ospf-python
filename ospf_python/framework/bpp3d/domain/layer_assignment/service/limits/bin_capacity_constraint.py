"""箱容量约束 / Bin capacity constraint.

确保容器不超过容量限制。
Ensures containers do not exceed capacity limits.
"""

from __future__ import annotations

import abc


class BinCapacityConstraint(abc.ABC):
    """箱容量约束 / Bin capacity constraint.

    验证层分配方案满足容器容量约束。
    Validates that layer assignment solutions satisfy
    container capacity constraints.
    """

    @abc.abstractmethod
    def is_satisfied(
        self,
        load: object,
        capacity: object,
    ) -> bool:
        """检查约束满足 / Check constraint satisfaction.

        Args:
            load: 当前负载 / The current load.
            capacity: 容器容量 / The container capacity.

        Returns:
            约束满足返回 True / True if constraint satisfied.
        """
        ...

    @abc.abstractmethod
    def get_violation(
        self,
        load: object,
        capacity: object,
    ) -> float:
        """计算违反量 / Calculate violation amount.

        Args:
            load: 当前负载 / The current load.
            capacity: 容器容量 / The container capacity.

        Returns:
            违反量（非负） / Violation amount (non-negative).
        """
        ...
