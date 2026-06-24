"""包裹属性 / Package attribute.

BPP3D 中包裹的属性定义。
Package attribute definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PackageAttribute:
    """包裹属性 / Package attribute.

    描述包裹的附加属性。
    Describes additional attributes of a package.

    Attributes:
        package_id: 包裹标识 / Package identifier.
        attribute_name: 属性名称 / Attribute name.
        attribute_value: 属性值 / Attribute value.
    """

    package_id: str
    """包裹标识 / Package identifier."""

    attribute_name: str
    """属性名称 / Attribute name."""

    attribute_value: str
    """属性值 / Attribute value."""

    @staticmethod
    def create(
        *,
        package_id: str,
        attribute_name: str,
        attribute_value: str = "",
    ) -> PackageAttribute:
        """创建包裹属性 / Create package attribute.

        Args:
            package_id: 包裹标识 / Package identifier.
            attribute_name: 属性名称 / Attribute name.
            attribute_value: 属性值，默认空 /
                Value, default empty.

        Returns:
            包裹属性实例 / PackageAttribute instance.
        """
        return PackageAttribute(
            package_id=package_id,
            attribute_name=attribute_name,
            attribute_value=attribute_value,
        )
