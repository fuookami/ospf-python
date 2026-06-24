"""包裹定义 / Package definition.

BPP3D 中的包裹定义。
Package definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.infrastructure.package_type import (
        PackageType,
    )


@dataclass(frozen=True)
class Package:
    """包裹 / Package.

    描述 BPP3D 中的包裹实例。
    Describes a package instance in BPP3D.

    Attributes:
        package_id: 包裹标识 / Package identifier.
        package_type: 包裹类型 / Package type.
        item_keys: 包含物品键 / Contained item keys.
    """

    package_id: str
    """包裹标识 / Package identifier."""

    package_type: PackageType
    """包裹类型 / Package type."""

    item_keys: tuple[str, ...] = ()
    """包含物品键 / Contained item keys."""

    @staticmethod
    def create(
        *,
        package_id: str,
        package_type: PackageType,
        item_keys: tuple[str, ...] = (),
    ) -> Package:
        """创建包裹 / Create package.

        Args:
            package_id: 包裹标识 / Package identifier.
            package_type: 包裹类型 / Package type.
            item_keys: 物品键列表，默认空 /
                Item keys, default empty.

        Returns:
            包裹实例 / Package instance.
        """
        return Package(
            package_id=package_id,
            package_type=package_type,
            item_keys=item_keys,
        )

    @property
    def volume(self) -> float:
        """包裹体积 / Package volume.

        Returns:
            类型体积 / Type volume.
        """
        return self.package_type.volume
