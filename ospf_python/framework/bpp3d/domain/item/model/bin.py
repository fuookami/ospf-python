"""箱子定义 / Bin definition.

BPP3D 中的箱子（容器实例）定义。
Bin (container instance) definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.container import (
        Container,
    )


@dataclass(frozen=True)
class Bin:
    """箱子 / Bin.

    描述 BPP3D 中的箱子实例，关联容器类型。
    Describes a bin instance in BPP3D, associated
    with a container type.

    Attributes:
        bin_id: 箱子标识 / Bin identifier.
        container: 容器类型 / Container type.
    """

    bin_id: str
    """箱子标识 / Bin identifier."""

    container: Container
    """容器类型 / Container type."""

    @staticmethod
    def create(
        *,
        bin_id: str,
        container: Container,
    ) -> Bin:
        """创建箱子 / Create bin.

        Args:
            bin_id: 箱子标识 / Bin identifier.
            container: 容器类型 / Container type.

        Returns:
            箱子实例 / Bin instance.
        """
        return Bin(
            bin_id=bin_id,
            container=container,
        )

    @property
    def volume(self) -> float:
        """箱子体积 / Bin volume.

        Returns:
            容器体积 / Container volume.
        """
        return self.container.volume
