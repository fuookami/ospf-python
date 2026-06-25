"""资源属性 / Resource attribute.

为资源提供可扩展的键值对属性，支持自定义业务元数据。
Provides extensible key-value attributes for resources,
supporting custom business metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResourceAttribute:
    """资源属性集合 / Resource attribute collection.

    存储资源的附加业务属性，以不可变键值对形式组织。
    Stores additional business attributes for a resource,
    organized as immutable key-value pairs.

    Attributes:
        resource_key: 所属资源标识 / Owner resource identifier.
        attributes: 属性映射 / Attribute mapping.
    """

    resource_key: str
    attributes: tuple[tuple[str, Any], ...] = ()

    def get(self, key: str) -> Any | None:
        """获取属性值。

        Get the attribute value by key.

        Args:
            key: 属性键名。/ Attribute key name.

        Returns:
            属性值，不存在时返回 None。
            Attribute value, or None if not found.
        """
        for k, v in self.attributes:
            if k == key:
                return v
        return None

    def has(self, key: str) -> bool:
        """检查是否包含指定属性。

        Check whether the attribute with the given key exists.

        Args:
            key: 属性键名。/ Attribute key name.

        Returns:
            若存在该属性则返回 True。
            True if the attribute exists.
        """
        return any(k == key for k, _ in self.attributes)

    def with_attribute(
        self,
        *,
        key: str,
        value: Any,
    ) -> ResourceAttribute:
        """创建添加了新属性的副本。

        Create a copy with an additional or updated attribute.

        Args:
            key: 属性键名。/ Attribute key name.
            value: 属性值。/ Attribute value.

        Returns:
            包含新属性的 ResourceAttribute 副本。
            A new ResourceAttribute instance with the attribute added.
        """
        updated = tuple((k, v) for k, v in self.attributes if k != key) + (
            (key, value),
        )
        return ResourceAttribute(
            resource_key=self.resource_key,
            attributes=updated,
        )

    def keys(self) -> tuple[str, ...]:
        """获取所有属性键名。

        Get all attribute key names.

        Returns:
            属性键名元组。/ Tuple of attribute key names.
        """
        return tuple(k for k, _ in self.attributes)

    def values(self) -> tuple[Any, ...]:
        """获取所有属性值。

        Get all attribute values.

        Returns:
            属性值元组。/ Tuple of attribute values.
        """
        return tuple(v for _, v in self.attributes)
