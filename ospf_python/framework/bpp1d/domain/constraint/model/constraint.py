"""约束定义 / Constraint definition.

BPP1D 中的装箱约束定义。
Packing constraint definition in BPP1D.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ConstraintType(enum.Enum):
    """约束类型 / Constraint type.

    描述 BPP1D 中可用的约束类型。
    Describes available constraint types in BPP1D.

    Attributes:
        WEIGHT_LIMIT: 重量限制 / Weight limit.
        ITEM_EXCLUSION: 物品互斥 / Item exclusion.
        ITEM_GROUPING: 物品分组 / Item grouping.
    """

    WEIGHT_LIMIT = "weight_limit"
    """重量限制 / Weight limit."""

    ITEM_EXCLUSION = "item_exclusion"
    """物品互斥 / Item exclusion."""

    ITEM_GROUPING = "item_grouping"
    """物品分组 / Item grouping."""


@dataclass(frozen=True)
class Constraint:
    """约束 / Constraint.

    描述 BPP1D 中的一个装箱约束。
    Describes a packing constraint in BPP1D.

    Attributes:
        constraint_key: 约束键 / Constraint key.
        constraint_type: 约束类型 / Constraint type.
        item_keys: 受约束的物品键 / Constrained item keys.
        max_value: 约束上界 / Constraint upper bound.
    """

    constraint_key: str
    """约束键 / Constraint key."""

    constraint_type: ConstraintType
    """约束类型 / Constraint type."""

    item_keys: tuple[str, ...] = ()
    """受约束的物品键 / Constrained item keys."""

    max_value: float = 0.0
    """约束上界 / Constraint upper bound."""

    @staticmethod
    def create(
        *,
        constraint_key: str,
        constraint_type: ConstraintType,
        item_keys: tuple[str, ...] = (),
        max_value: float = 0.0,
    ) -> Constraint:
        """创建约束 / Create constraint.

        Args:
            constraint_key: 约束键 / Constraint key.
            constraint_type: 约束类型 / Constraint type.
            item_keys: 受约束物品键，默认空 /
                Constrained item keys, default empty.
            max_value: 约束上界，默认 0 /
                Constraint upper bound, default 0.

        Returns:
            约束实例 / Constraint instance.
        """
        return Constraint(
            constraint_key=constraint_key,
            constraint_type=constraint_type,
            item_keys=item_keys,
            max_value=max_value,
        )

    @staticmethod
    def weight_limit(
        *,
        constraint_key: str,
        item_keys: tuple[str, ...],
        max_weight: float,
    ) -> Constraint:
        """创建重量限制约束 / Create weight limit constraint.

        Args:
            constraint_key: 约束键 / Constraint key.
            item_keys: 受约束物品键 / Constrained item keys.
            max_weight: 最大重量 / Maximum weight.

        Returns:
            重量限制约束 / Weight limit constraint.
        """
        return Constraint(
            constraint_key=constraint_key,
            constraint_type=ConstraintType.WEIGHT_LIMIT,
            item_keys=item_keys,
            max_value=max_weight,
        )

    @staticmethod
    def item_exclusion(
        *,
        constraint_key: str,
        item_keys: tuple[str, ...],
    ) -> Constraint:
        """创建物品互斥约束 / Create item exclusion constraint.

        Args:
            constraint_key: 约束键 / Constraint key.
            item_keys: 互斥物品键 / Exclusion item keys.

        Returns:
            物品互斥约束 / Item exclusion constraint.
        """
        return Constraint(
            constraint_key=constraint_key,
            constraint_type=ConstraintType.ITEM_EXCLUSION,
            item_keys=item_keys,
        )

    @property
    def is_weight_limit(self) -> bool:
        """是否为重量限制 / Whether weight limit.

        Returns:
            约束类型是否为重量限制。
            Whether constraint type is weight limit.
        """
        return self.constraint_type == ConstraintType.WEIGHT_LIMIT

    @property
    def is_item_exclusion(self) -> bool:
        """是否为物品互斥 / Whether item exclusion.

        Returns:
            约束类型是否为物品互斥。
            Whether constraint type is item exclusion.
        """
        return self.constraint_type == ConstraintType.ITEM_EXCLUSION

    @property
    def is_item_grouping(self) -> bool:
        """是否为物品分组 / Whether item grouping.

        Returns:
            约束类型是否为物品分组。
            Whether constraint type is item grouping.
        """
        return self.constraint_type == ConstraintType.ITEM_GROUPING
