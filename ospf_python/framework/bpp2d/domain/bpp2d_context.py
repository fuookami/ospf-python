"""BPP2D 总上下文 / BPP2D aggregate context.

聚合物品与约束上下文，提供统一入口。
Aggregates item and constraint contexts, providing a
unified entry point.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.bpp2d.domain.constraint.constraint_context import (
    ConstraintContext,
)
from ospf_python.framework.bpp2d.domain.item.item_context import (
    ItemContext,
)


@dataclass(frozen=True)
class Bpp2dContext:
    """BPP2D 总上下文 / BPP2D aggregate context.

    聚合物品上下文和约束上下文，作为二维装箱域的
    统一入口。
    Aggregates item and constraint contexts as the
    unified entry point for the 2D bin packing domain.

    Attributes:
        item_context: 物品上下文 / Item context.
        constraint_context: 约束上下文 /
            Constraint context.
    """

    item_context: ItemContext
    """物品上下文 / Item context."""

    constraint_context: ConstraintContext
    """约束上下文 / Constraint context."""

    @staticmethod
    def create(
        *,
        item_context: ItemContext | None = None,
        constraint_context: ConstraintContext | None = None,
    ) -> Bpp2dContext:
        """创建 BPP2D 上下文 / Create BPP2D context.

        Args:
            item_context: 物品上下文，默认新建 /
                Item context, default new.
            constraint_context: 约束上下文，默认新建 /
                Constraint context, default new.

        Returns:
            BPP2D 上下文实例 / Bpp2dContext instance.
        """
        return Bpp2dContext(
            item_context=(item_context if item_context else ItemContext()),
            constraint_context=(
                constraint_context if constraint_context else ConstraintContext()
            ),
        )

    @property
    def item_count(self) -> int:
        """物品数量 / Item count.

        Returns:
            已注册物品数量 / Number of registered items.
        """
        return self.item_context.size

    @property
    def constraint_count(self) -> int:
        """约束数量 / Constraint count.

        Returns:
            已注册约束数量 / Number of constraints.
        """
        return self.constraint_context.size

    @property
    def is_ready(self) -> bool:
        """是否就绪 / Whether ready.

        至少有一个物品时视为就绪。
        Ready when at least one item is registered.

        Returns:
            就绪返回 True / True if ready.
        """
        return not self.item_context.is_empty

    @property
    def total_item_weight(self) -> float:
        """所有物品总重量 / Total weight of all items.

        Returns:
            物品上下文中的总重量 / Total weight in context.
        """
        return self.item_context.total_weight
