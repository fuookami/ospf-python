"""顺序限制 / Sequence limit.

定义货物装载的顺序约束。
Defines loading sequence constraints for cargo items.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SequenceLimit:
    """顺序限制 / Sequence limit.

    描述两种货物的装载顺序关系，item_a 必须在 item_b
    之前或之后装载。
    Describes the loading sequence relationship between two
    cargo types; item_a must be loaded before or after item_b.

    Attributes:
        item_a: 先装载的货物类型 / First cargo type.
        item_b: 后装载的货物类型 / Second cargo type.
        order: 顺序（BEFORE/AFTER）/ Order (BEFORE/AFTER).
    """

    item_a: str = ""
    """先装载的货物类型 / First cargo type."""

    item_b: str = ""
    """后装载的货物类型 / Second cargo type."""

    order: str = "BEFORE"
    """顺序（BEFORE/AFTER）/ Order (BEFORE/AFTER)."""

    @staticmethod
    def before(
        *,
        first: str,
        second: str,
    ) -> SequenceLimit:
        """创建"先于"顺序限制。

        Create "before" sequence limit.

        Args:
            first: 先装载的货物类型。/ First cargo type.
            second: 后装载的货物类型。/ Second cargo type.

        Returns:
            顺序限制实例。/ Sequence limit instance.
        """
        return SequenceLimit(
            item_a=first,
            item_b=second,
            order="BEFORE",
        )

    @staticmethod
    def after(
        *,
        first: str,
        second: str,
    ) -> SequenceLimit:
        """创建"后于"顺序限制。

        Create "after" sequence limit.

        Args:
            first: 后装载的货物类型。/ Later cargo type.
            second: 先装载的货物类型。/ Earlier cargo type.

        Returns:
            顺序限制实例。/ Sequence limit instance.
        """
        return SequenceLimit(
            item_a=first,
            item_b=second,
            order="AFTER",
        )

    @property
    def is_before(self) -> bool:
        """是否为"先于"顺序。

        Whether this is a "before" sequence.

        Returns:
            顺序为 BEFORE 时返回 True。
            True if order is BEFORE.
        """
        return self.order == "BEFORE"

    @property
    def is_after(self) -> bool:
        """是否为"后于"顺序。

        Whether this is an "after" sequence.

        Returns:
            顺序为 AFTER 时返回 True。
            True if order is AFTER.
        """
        return self.order == "AFTER"

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

    def predecessor(self) -> str:
        """获取先装载的货物类型。

        Get the predecessor cargo type.

        Returns:
            先装载的类型标识。/ Predecessor type identifier.
        """
        if self.is_before:
            return self.item_a
        return self.item_b

    def successor(self) -> str:
        """获取后装载的货物类型。

        Get the successor cargo type.

        Returns:
            后装载的类型标识。/ Successor type identifier.
        """
        if self.is_before:
            return self.item_b
        return self.item_a

    def is_satisfied(
        self,
        position_a: int,
        position_b: int,
    ) -> bool:
        """检查顺序是否满足。

        Check whether the sequence is satisfied.

        Args:
            position_a: 货物 A 的装载顺序位置。/
                Loading position of item A.
            position_b: 货物 B 的装载顺序位置。/
                Loading position of item B.

        Returns:
            顺序满足时返回 True。
            True if the sequence is satisfied.
        """
        if self.is_before:
            return position_a < position_b
        return position_a > position_b
