"""层放置适配器 / Layer placement adapter.

适配层放置算法的调用接口。
Adapts the calling interface for layer placement algorithms.
"""

from __future__ import annotations

import abc


class LayerPlacementAdapter(abc.ABC):
    """层放置适配器 / Layer placement adapter.

    将层放置算法适配为统一的应用层接口。
    Adapts layer placement algorithms into a unified
    application-layer interface.
    """

    @abc.abstractmethod
    def place_layer(
        self,
        layer: object,
        container: object,
        position: object,
    ) -> bool:
        """放置层 / Place layer.

        将层放置到容器的指定位置。
        Places a layer at the specified position in a container.

        Args:
            layer: 待放置的层 / The layer to place.
            container: 目标容器 / The target container.
            position: 放置位置 / The placement position.

        Returns:
            放置成功返回 True / True if placement succeeded.
        """
        ...

    @abc.abstractmethod
    def can_place(
        self,
        layer: object,
        container: object,
        position: object,
    ) -> bool:
        """检查是否可放置 / Check if placement is possible.

        Args:
            layer: 待放置的层 / The layer to place.
            container: 目标容器 / The target container.
            position: 放置位置 / The placement position.

        Returns:
            可放置返回 True / True if placement is possible.
        """
        ...
