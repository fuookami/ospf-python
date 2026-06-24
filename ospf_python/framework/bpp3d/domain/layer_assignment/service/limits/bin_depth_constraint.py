"""箱深度约束 / Bin depth constraint.

确保容器深度方向不超限。
Ensures container depth is not exceeded.
"""

from __future__ import annotations

import abc


class BinDepthConstraint(abc.ABC):
    """箱深度约束 / Bin depth constraint.

    验证层分配方案满足容器深度约束。
    Validates that layer assignment solutions satisfy
    container depth constraints.
    """

    @abc.abstractmethod
    def is_satisfied(
        self,
        layer_depth: float,
        container_depth: float,
    ) -> bool:
        """检查约束满足 / Check constraint satisfaction.

        Args:
            layer_depth: 层深度 / The layer depth.
            container_depth: 容器深度 / The container depth.

        Returns:
            约束满足返回 True / True if constraint satisfied.
        """
        ...

    @abc.abstractmethod
    def get_remaining_depth(
        self,
        used_depth: float,
        container_depth: float,
    ) -> float:
        """计算剩余深度 / Calculate remaining depth.

        Args:
            used_depth: 已用深度 / The used depth.
            container_depth: 容器深度 / The container depth.

        Returns:
            剩余深度（非负） / Remaining depth (non-negative).
        """
        ...
