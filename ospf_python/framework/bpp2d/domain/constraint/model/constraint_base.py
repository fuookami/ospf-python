"""约束基类 / Constraint base class.

定义二维装箱约束的基础接口。
Defines the base interface for 2D bin packing constraints.
"""

from __future__ import annotations

import abc
import enum


class ConstraintType(enum.Enum):
    """约束类型 / Constraint type.

    描述 BPP2D 中可用的约束类型。
    Describes available constraint types in BPP2D.

    Attributes:
        value: 约束类型字符串标识 /
            Constraint type string identifier.
    """

    GEOMETRIC = "geometric"
    """几何约束 / Geometric constraint."""

    WEIGHT = "weight"
    """重量约束 / Weight constraint."""


class ConstraintBase(abc.ABC):
    """约束基类 / Constraint base class.

    所有二维装箱约束的抽象基类。
    Abstract base class for all 2D bin packing constraints.

    Attributes:
        constraint_key: 约束标识 / Constraint identifier.
        constraint_type: 约束类型 / Constraint type.
        item_keys: 受约束物品键 / Constrained item keys.
    """

    @property
    @abc.abstractmethod
    def constraint_key(self) -> str:
        """获取约束标识 / Get constraint identifier."""

    @property
    @abc.abstractmethod
    def constraint_type(self) -> ConstraintType:
        """获取约束类型 / Get constraint type."""

    @property
    @abc.abstractmethod
    def item_keys(self) -> tuple[str, ...]:
        """获取受约束物品键 / Get constrained item keys."""

    @abc.abstractmethod
    def applies_to(self, item_key: str) -> bool:
        """检查是否适用于指定物品 / Check if applies to item.

        Args:
            item_key: 物品键 / Item key.

        Returns:
            适用于该物品返回 True / True if applies.
        """
