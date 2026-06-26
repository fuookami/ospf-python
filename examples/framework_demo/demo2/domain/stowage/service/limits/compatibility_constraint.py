"""兼容性约束 / Compatibility constraint.

确保不兼容的货物不会被放置在同一货舱中。
Ensures that incompatible cargo items are not placed in
the same compartment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.compatibility_limit import (
        CompatibilityLimit,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )


@dataclass(frozen=True)
class CompatibilityViolation:
    """兼容性违反记录 / Compatibility violation record.

    记录不兼容货物被分配到同一货舱的信息。
    Records incompatible items assigned to the same compartment.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        item_a: 货物类型 A / Cargo type A.
        item_b: 货物类型 B / Cargo type B.
        violated_limit: 被违反的限制 / Violated limit.
    """

    compartment_id: str = ""
    """舱室标识 / Compartment identifier."""

    item_a: str = ""
    """货物类型 A / Cargo type A."""

    item_b: str = ""
    """货物类型 B / Cargo type B."""

    violated_limit: CompatibilityLimit = None  # type: ignore[assignment]
    """被违反的限制 / Violated limit."""


@dataclass(frozen=True)
class CompatibilityConstraint:
    """兼容性约束 / Compatibility constraint.

    验证同一货舱中的货物类型之间不存在不兼容关系。
    遍历所有货舱的货物分配，检查每对货物是否违反兼容性规则。
    Validates that no incompatible cargo type pairs exist within
    the same compartment. Iterates over all compartment assignments,
    checking each pair against compatibility rules.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "compatibility"
    """约束名称前缀 / Constraint name prefix."""

    def check_assignments(
        self,
        *,
        limits: tuple[CompatibilityLimit, ...],
        items: tuple[StowageItem, ...],
        assignments: dict[str, tuple[str, ...]],
    ) -> tuple[CompatibilityViolation, ...]:
        """检查所有货舱的兼容性约束。

        Check compatibility constraints for all compartments.

        Args:
            limits: 兼容性限制列表。/ Compatibility limits.
            items: 货物列表。/ Item list.
            assignments: 货物到货舱的分配映射。/
                Item-to-compartment assignment mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        item_map = {item.item_id: item for item in items}
        incompatible = {
            (lim.item_a, lim.item_b): lim for lim in limits if lim.is_incompatible
        }
        violations: list[CompatibilityViolation] = []
        for comp_id, assigned_ids in assignments.items():
            types_in_comp = tuple(
                item_map[sid].item_id for sid in assigned_ids if sid in item_map
            )
            for i, type_a in enumerate(types_in_comp):
                for type_b in types_in_comp[i + 1 :]:
                    key_ab = (type_a, type_b)
                    key_ba = (type_b, type_a)
                    if key_ab in incompatible:
                        violations.append(
                            CompatibilityViolation(
                                compartment_id=comp_id,
                                item_a=type_a,
                                item_b=type_b,
                                violated_limit=incompatible[key_ab],
                            )
                        )
                    elif key_ba in incompatible:
                        violations.append(
                            CompatibilityViolation(
                                compartment_id=comp_id,
                                item_a=type_b,
                                item_b=type_a,
                                violated_limit=incompatible[key_ba],
                            )
                        )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        limits: tuple[CompatibilityLimit, ...],
        items: tuple[StowageItem, ...],
        assignments: dict[str, tuple[str, ...]],
    ) -> bool:
        """检查兼容性约束是否可行。

        Check whether compatibility constraints are feasible.

        Args:
            limits: 兼容性限制列表。/ Compatibility limits.
            items: 货物列表。/ Item list.
            assignments: 分配映射。/ Assignment mapping.

        Returns:
            所有货舱内货物均兼容时返回 True。
            True if all items within each compartment are compatible.
        """
        return (
            len(
                self.check_assignments(
                    limits=limits,
                    items=items,
                    assignments=assignments,
                )
            )
            == 0
        )

    def incompatible_pairs_for(
        self,
        *,
        limits: tuple[CompatibilityLimit, ...],
        item_type: str,
    ) -> tuple[CompatibilityLimit, ...]:
        """获取指定货物类型的所有不兼容配对。

        Get all incompatible pairs for a specific cargo type.

        Args:
            limits: 兼容性限制列表。/ Compatibility limits.
            item_type: 货物类型。/ Cargo type.

        Returns:
            不兼容限制元组。/ Tuple of incompatible limits.
        """
        return tuple(
            lim
            for lim in limits
            if lim.is_incompatible and lim.involves_item(item_type)
        )
