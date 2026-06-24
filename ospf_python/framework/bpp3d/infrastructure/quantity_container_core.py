"""数量容器核心 / Quantity container core.

BPP3D 中带数量的容器核心定义。
Quantity-aware container core definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.container import (
        Container,
    )


@dataclass(frozen=True)
class QuantityContainerCore:
    """数量容器核心 / Quantity container core.

    将容器与可用数量关联。
    Associates a container with available quantity.

    Attributes:
        container: 容器定义 / Container definition.
        quantity: 可用数量 / Available quantity.
    """

    container: Container
    """容器定义 / Container definition."""

    quantity: int
    """可用数量 / Available quantity."""

    @staticmethod
    def create(
        *,
        container: Container,
        quantity: int = 1,
    ) -> QuantityContainerCore:
        """创建数量容器 / Create quantity container.

        Args:
            container: 容器定义 / Container definition.
            quantity: 可用数量，默认 1 / Quantity, default 1.

        Returns:
            数量容器核心实例 / QuantityContainerCore instance.
        """
        return QuantityContainerCore(
            container=container,
            quantity=quantity,
        )

    @property
    def volume(self) -> float:
        """容器体积 / Container volume.

        Returns:
            容器宽 x 高 x 深 / Container W x H x D.
        """
        return self.container.volume
