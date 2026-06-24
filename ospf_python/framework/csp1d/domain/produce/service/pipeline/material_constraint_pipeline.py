"""CSP1D 材料约束管线。

管理材料使用量和可用性约束。
Material constraint pipeline for production.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialConstraintPipeline:
    """材料约束管线 / Material constraint pipeline.

    管理材料使用量约束，确保生产计划不超过
    材料库存。在 MILP 中对应材料使用量
    <= 库存的约束族。
    Manages material usage constraints, ensuring
    production plans do not exceed material inventory.
    Corresponds to material usage <= inventory
    constraint family in MILP.

    Attributes:
        enforce_inventory: 是否强制库存约束。
            Whether to enforce inventory constraints.
        allow_substitution: 是否允许材料替代。
            Whether material substitution is allowed.
    """

    enforce_inventory: bool = True
    """强制库存 / Enforce inventory."""

    allow_substitution: bool = False
    """允许替代 / Allow substitution."""

    def apply[T](self, aggregation: T) -> T:
        """应用材料约束。

        Apply material constraints.

        Args:
            aggregation: 生产聚合。
                Production aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def is_within_inventory(
        self,
        *,
        used: float,
        available: float,
    ) -> bool:
        """检查是否在库存范围内。

        Check if within inventory.

        Args:
            used: 已使用量。
                Used quantity.
            available: 可用量。
                Available quantity.

        Returns:
            在范围内返回 True / True if within range.
        """
        if not self.enforce_inventory:
            return True
        return used <= available + 1e-8

    def remaining_inventory(
        self,
        *,
        used: float,
        available: float,
    ) -> float:
        """计算剩余库存。

        Compute remaining inventory.

        Args:
            used: 已使用量。
                Used quantity.
            available: 可用量。
                Available quantity.

        Returns:
            剩余库存（非负）。
            Remaining inventory (non-negative).
        """
        if not self.enforce_inventory:
            return available
        return max(0.0, available - used)

    def can_substitute(
        self,
        *,
        original_material: str,
        substitute_material: str,
        substitution_rules: frozenset[tuple[str, str]],
    ) -> bool:
        """检查材料替代是否允许。

        Check if material substitution is allowed.

        Args:
            original_material: 原材料标识。
                Original material key.
            substitute_material: 替代材料标识。
                Substitute material key.
            substitution_rules: 替代规则集合，
                每项为 (原材料, 替代材料)。
                Substitution rules, each item is
                (original, substitute).

        Returns:
            允许返回 True / True if allowed.
        """
        if not self.allow_substitution:
            return False
        return (original_material, substitute_material) in substitution_rules
