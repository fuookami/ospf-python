"""深度边界层方向策略 / Depth boundary layer orientation policy.

定义层放置时深度方向的选择策略。
Defines the strategy for selecting depth orientation during
layer placement.
"""

from __future__ import annotations

import abc


class DepthBoundaryLayerOrientationPolicy(abc.ABC):
    """深度边界层方向策略 / Depth boundary layer orientation policy.

    根据容器和物品的深度约束确定层的放置方向。
    Determines layer placement orientation based on container
    and item depth constraints.
    """

    @abc.abstractmethod
    def determine_orientation(
        self,
        container_depth: float,
        layer_depth: float,
    ) -> bool:
        """确定层方向 / Determine layer orientation.

        Args:
            container_depth: 容器深度 / The container depth.
            layer_depth: 层深度 / The layer depth.

        Returns:
            是否需要旋转 / Whether rotation is needed.
        """
        ...

    @abc.abstractmethod
    def is_compatible(
        self,
        container_depth: float,
        layer_depth: float,
    ) -> bool:
        """检查兼容性 / Check compatibility.

        Args:
            container_depth: 容器深度 / The container depth.
            layer_depth: 层深度 / The layer depth.

        Returns:
            层与容器深度兼容返回 True / True if layer depth
            is compatible with container.
        """
        ...
