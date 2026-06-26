"""堆码约束。

Stacking constraint enforcing heavy-below-light rules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StackingItem:
    """堆码物品信息。

    Information about an item relevant to stacking decisions.

    Attributes:
        item_id: 物品标识 / Item identifier
        weight: 物品重量（千克）/ Item weight (kg)
        fragility: 易碎等级 (0=坚固, 1=极碎) / Fragility level (0=sturdy, 1=very fragile)
        stackable: 是否可堆码 / Whether the item can be stacked upon
    """

    item_id: str
    weight: float
    fragility: float
    stackable: bool


@dataclass(frozen=True)
class StackingConstraint:
    """堆码约束。

    Enforces stacking rules: heavy items must be placed below lighter items,
    fragile items cannot have heavy items stacked on top, and non-stackable
    items cannot have anything placed above them.

    Attributes:
        max_weight_on_fragile: 碎物品上最大压力 / Max weight allowed on fragile items (kg)
        weight_ratio_limit: 上下层重量比上限 / Max weight ratio of upper to lower item
    """

    max_weight_on_fragile: float
    weight_ratio_limit: float

    def evaluate(
        self,
        stack: tuple[StackingItem, ...],
    ) -> tuple[bool, list[str]]:
        """评估堆码方案是否满足约束。

        Evaluates a vertical stack from bottom to top.

        Args:
            stack: 从底到顶的物品序列 / Items ordered bottom to top

        Returns:
            tuple: (是否满足, 违规原因列表) / (satisfied, list of violation reasons)
        """
        violations: list[str] = []
        for i in range(len(stack) - 1):
            lower = stack[i]
            upper = stack[i + 1]

            if not lower.stackable:
                violations.append(
                    f"物品 {lower.item_id} 不可堆码，上方不能放置 {upper.item_id}"
                )

            if lower.fragility > 0.5 and upper.weight > self.max_weight_on_fragile:
                violations.append(
                    f"易碎物品 {lower.item_id} 上方 "
                    f"{upper.item_id} 重量 {upper.weight:.1f}kg "
                    f"超过限制 {self.max_weight_on_fragile:.1f}kg"
                )

            if lower.weight > 0.0:
                ratio = upper.weight / lower.weight
                if ratio > self.weight_ratio_limit:
                    violations.append(
                        f"上层 {upper.item_id} 与下层 "
                        f"{lower.item_id} 重量比 {ratio:.2f} "
                        f"超过限制 {self.weight_ratio_limit:.2f}"
                    )

        return (len(violations) == 0, violations)

    def is_valid_placement(
        self,
        existing_stack: tuple[StackingItem, ...],
        new_item: StackingItem,
    ) -> bool:
        """判断新物品能否放在栈顶。

        Args:
            existing_stack: 当前堆码 / Current stack
            new_item: 待放物品 / Item to place on top

        Returns:
            bool: 是否可放置 / Whether placement is valid
        """
        if not existing_stack:
            return True
        extended = (*existing_stack, new_item)
        ok, _ = self.evaluate(extended)
        return ok
