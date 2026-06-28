"""重量约束模型 / Weight constraint model.

定义二维装箱中的重量约束。
Defines weight constraints for 2D bin packing.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.bpp2d.domain.constraint.model.constraint_base import (
    ConstraintBase,
    ConstraintType,
)


@dataclass(frozen=True)
class WeightConstraint(ConstraintBase):
    """重量约束 / Weight constraint.

    限制容器中物品的总重量。
    Limits the total weight of items in a container.

    Attributes:
        constraint_key: 约束标识 / Constraint identifier.
        item_keys: 受约束物品键 / Constrained item keys.
        max_weight: 最大允许重量 / Maximum allowed weight.
    """

    constraint_key: str
    """约束标识 / Constraint identifier."""

    item_keys: tuple[str, ...] = ()
    """受约束物品键 / Constrained item keys."""

    max_weight: float = 0.0
    """最大允许重量，默认 0 / Max weight, default 0."""

    @staticmethod
    def create(
        *,
        constraint_key: str,
        item_keys: tuple[str, ...] = (),
        max_weight: float = 0.0,
    ) -> WeightConstraint:
        """创建重量约束 / Create weight constraint.

        Args:
            constraint_key: 约束标识 / Constraint identifier.
            item_keys: 受约束物品键 / Constrained item keys.
            max_weight: 最大重量 / Maximum weight.

        Returns:
            重量约束实例 / WeightConstraint instance.
        """
        return WeightConstraint(
            constraint_key=constraint_key,
            item_keys=item_keys,
            max_weight=max_weight,
        )

    @property
    def constraint_type(self) -> ConstraintType:
        """获取约束类型 / Get constraint type.

        Returns:
            重量类型 / Weight type.
        """
        return ConstraintType.WEIGHT

    def applies_to(self, item_key: str) -> bool:
        """检查是否适用于指定物品 / Check if applies to item.

        当 item_keys 为空时，适用于所有物品。
        When item_keys is empty, applies to all items.

        Args:
            item_key: 物品键 / Item key.

        Returns:
            适用于该物品返回 True / True if applies.
        """
        if not self.item_keys:
            return True  # reason: empty item_keys means applies to all items
        return item_key in self.item_keys

    def check_weight(
        self,
        current_weight: float,
        additional_weight: float = 0.0,
    ) -> bool:
        """检查重量是否满足约束 / Check weight satisfies.

        验证当前重量加上新增重量不超出限制。
        Verifies current plus additional weight does not
        exceed the limit.

        Args:
            current_weight: 当前总重量 / Current total weight.
            additional_weight: 新增重量，默认 0 /
                Additional weight, default 0.

        Returns:
            满足约束返回 True / True if satisfied.
        """
        return current_weight + additional_weight <= self.max_weight

    def remaining_capacity(
        self,
        current_weight: float,
    ) -> float:
        """计算剩余容量 / Calculate remaining capacity.

        Args:
            current_weight: 当前总重量 / Current total weight.

        Returns:
            剩余可承载重量 / Remaining weight capacity.
        """
        return max(0.0, self.max_weight - current_weight)
