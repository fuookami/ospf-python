"""约束上下文 / Constraint context.

管理 BPP1D 约束的注册与查询。
Manages registration and lookup of BPP1D constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
        Constraint,
    )


@dataclass(frozen=True)
class ConstraintContext:
    """约束上下文 / Constraint context.

    持有已注册约束的字典，支持注册和查询操作。
    Holds a dictionary of registered constraints, supporting
    registration and lookup operations.

    Attributes:
        constraints: 已注册约束映射（键 -> 约束）/
            Registered constraints mapping (key -> constraint).
    """

    constraints: dict[str, Constraint] = field(
        default_factory=dict,
    )
    """已注册约束映射 / Registered constraints mapping."""

    @staticmethod
    def create(
        *,
        constraints: dict[str, Constraint] | None = None,
    ) -> ConstraintContext:
        """创建约束上下文 / Create constraint context.

        Args:
            constraints: 初始约束映射，默认空 /
                Initial constraints mapping, default empty.

        Returns:
            约束上下文实例 / ConstraintContext instance.
        """
        return ConstraintContext(
            constraints=dict(constraints) if constraints else {},
        )

    def register(
        self,
        constraint: Constraint,
    ) -> ConstraintContext:
        """注册约束 / Register constraint.

        Args:
            constraint: 要注册的约束 / Constraint to register.

        Returns:
            包含新约束的上下文 / Context with the new constraint.
        """
        new_constraints = dict(self.constraints)
        new_constraints[constraint.constraint_key] = constraint
        return ConstraintContext(constraints=new_constraints)

    def register_many(
        self,
        constraints: tuple[Constraint, ...],
    ) -> ConstraintContext:
        """批量注册约束 / Register multiple constraints.

        Args:
            constraints: 要注册的约束元组 / Constraints to register.

        Returns:
            包含所有新约束的上下文 /
            Context with all new constraints.
        """
        result = self
        for constraint in constraints:
            result = result.register(constraint)
        return result

    def get(
        self,
        constraint_key: str,
    ) -> Constraint | None:
        """查询约束 / Lookup constraint.

        Args:
            constraint_key: 约束键 / Constraint key.

        Returns:
            约束实例或 None / Constraint instance or None.
        """
        return self.constraints.get(constraint_key)

    def get_all(self) -> tuple[Constraint, ...]:
        """获取所有约束 / Get all constraints.

        Returns:
            所有已注册约束的元组。
            Tuple of all registered constraints.
        """
        return tuple(self.constraints.values())

    def get_by_item(
        self,
        item_key: str,
    ) -> tuple[Constraint, ...]:
        """按物品键查询约束 / Lookup constraints by item key.

        Args:
            item_key: 物品键 / Item key.

        Returns:
            包含该物品键的所有约束。
            All constraints containing the item key.
        """
        return tuple(c for c in self.constraints.values() if item_key in c.item_keys)

    @property
    def count(self) -> int:
        """约束数量 / Constraint count.

        Returns:
            已注册约束的数量。
            Number of registered constraints.
        """
        return len(self.constraints)
