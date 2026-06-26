"""兼容性限制 / Compatibility limit.

定义货物之间的兼容性规则。
Defines compatibility rules between cargo items.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompatibilityLimit:
    """兼容性限制 / Compatibility limit.

    描述两种货物是否可以放置在同一货舱中。
    Describes whether two types of cargo can be placed
    in the same compartment.

    Attributes:
        item_a: 货物类型 A / Cargo type A.
        item_b: 货物类型 B / Cargo type B.
        compatible: 是否兼容 / Whether compatible.
    """

    item_a: str = ""
    """货物类型 A / Cargo type A."""

    item_b: str = ""
    """货物类型 B / Cargo type B."""

    compatible: bool = True
    """是否兼容 / Whether compatible."""

    @staticmethod
    def compatible_pair(
        *,
        item_a: str,
        item_b: str,
    ) -> CompatibilityLimit:
        """创建兼容配对。

        Create compatible pair.

        Args:
            item_a: 货物类型 A。/ Cargo type A.
            item_b: 货物类型 B。/ Cargo type B.

        Returns:
            兼容限制实例。/ Compatibility limit instance.
        """
        return CompatibilityLimit(
            item_a=item_a,
            item_b=item_b,
            compatible=True,
        )

    @staticmethod
    def incompatible_pair(
        *,
        item_a: str,
        item_b: str,
    ) -> CompatibilityLimit:
        """创建不兼容配对。

        Create incompatible pair.

        Args:
            item_a: 货物类型 A。/ Cargo type A.
            item_b: 货物类型 B。/ Cargo type B.

        Returns:
            不兼容限制实例。/ Incompatibility limit instance.
        """
        return CompatibilityLimit(
            item_a=item_a,
            item_b=item_b,
            compatible=False,
        )

    @property
    def is_incompatible(self) -> bool:
        """是否不兼容。

        Whether the pair is incompatible.

        Returns:
            不兼容时返回 True。
            True if the pair is incompatible.
        """
        return not self.compatible

    def involves_item(self, item_type: str) -> bool:
        """检查是否涉及指定货物类型。

        Check whether it involves a specific cargo type.

        Args:
            item_type: 货物类型。/ Cargo type.

        Returns:
            涉及该类型时返回 True。
            True if it involves the type.
        """
        return item_type in (self.item_a, self.item_b)

    def other_item(self, item_type: str) -> str:
        """获取配对中的另一货物类型。

        Get the other cargo type in the pair.

        Args:
            item_type: 已知货物类型。/ Known cargo type.

        Returns:
            另一货物类型，不匹配时返回空字符串。
            The other type, or empty string if not matched.
        """
        if item_type == self.item_a:
            return self.item_b
        if item_type == self.item_b:
            return self.item_a
        return ""

    def applies_to(
        self,
        type_a: str,
        type_b: str,
    ) -> bool:
        """检查是否适用于指定类型对。

        Check whether it applies to a specific type pair.

        Args:
            type_a: 货物类型 A。/ Cargo type A.
            type_b: 货物类型 B。/ Cargo type B.

        Returns:
            适用于该类型对时返回 True。
            True if it applies to the type pair.
        """
        pair = {type_a, type_b}
        return pair == {self.item_a, self.item_b}
