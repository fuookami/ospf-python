"""最大重量约束 / Maximum weight constraint.

确保每个货舱的装载重量不超过其最大承载限制。
Ensures that each compartment's loaded weight does not exceed
its maximum capacity limit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.stowage.model.weight_limit import (
    WeightLimit,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_compartment import (
        StowageCompartment,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )


@dataclass(frozen=True)
class WeightViolation:
    """重量违反记录 / Weight violation record.

    记录一个货舱的重量超限信息。
    Records weight excess information for a compartment.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        current_weight: 当前重量（千克）/ Current weight (kg).
        max_weight: 最大重量（千克）/ Maximum weight (kg).
        excess: 超出量（千克）/ Excess amount (kg).
    """

    compartment_id: str = ""
    """舱室标识 / Compartment identifier."""

    current_weight: float = 0.0
    """当前重量（千克）/ Current weight (kg)."""

    max_weight: float = 0.0
    """最大重量（千克）/ Maximum weight (kg)."""

    excess: float = 0.0
    """超出量（千克）/ Excess amount (kg)."""


@dataclass(frozen=True)
class MaxWeightConstraint:
    """最大重量约束 / Maximum weight constraint.

    验证每个货舱的装载重量不超过其最大承载限制。
    遍历所有货舱和重量限制，计算当前装载重量并与限制比较。
    Validates that each compartment's loaded weight does not exceed
    its maximum capacity. Iterates over all compartments and weight
    limits, comparing current load against limits.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "max_weight"
    """约束名称前缀 / Constraint name prefix."""

    def build_limits(
        self,
        compartments: tuple[StowageCompartment, ...],
    ) -> tuple[WeightLimit, ...]:
        """从货舱信息构建重量限制列表。

        Build weight limit list from compartment information.

        Args:
            compartments: 货舱列表。/ Compartment list.

        Returns:
            重量限制元组。/ Tuple of weight limits.
        """
        return tuple(
            WeightLimit(
                compartment=comp.comp_id,
                max_weight=comp.max_weight,
                flight_phase="GROUND",
            )
            for comp in compartments
            if comp.max_weight > 0.0
        )

    def check_compartments(
        self,
        *,
        compartments: tuple[StowageCompartment, ...],
        items: tuple[StowageItem, ...],
        assignments: dict[str, tuple[str, ...]],
    ) -> tuple[WeightViolation, ...]:
        """检查所有货舱的重量约束。

        Check weight constraints for all compartments.

        Args:
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            assignments: 货物到货舱的分配映射，键为货舱标识，
                值为货物标识列表。/
                Item-to-compartment assignment mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        item_map = {item.item_id: item for item in items}
        violations: list[WeightViolation] = []
        for comp in compartments:
            assigned_ids = assignments.get(comp.comp_id, ())
            current = sum(
                item_map[sid].weight for sid in assigned_ids if sid in item_map
            )
            if current > comp.max_weight:
                violations.append(
                    WeightViolation(
                        compartment_id=comp.comp_id,
                        current_weight=current,
                        max_weight=comp.max_weight,
                        excess=current - comp.max_weight,
                    )
                )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        compartments: tuple[StowageCompartment, ...],
        items: tuple[StowageItem, ...],
        assignments: dict[str, tuple[str, ...]],
    ) -> bool:
        """检查重量约束是否可行。

        Check whether weight constraints are feasible.

        Args:
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            assignments: 分配映射。/ Assignment mapping.

        Returns:
            所有货舱重量均在限制内时返回 True。
            True if all compartment weights are within limits.
        """
        return (
            len(
                self.check_compartments(
                    compartments=compartments,
                    items=items,
                    assignments=assignments,
                )
            )
            == 0
        )

    def constraint_name(
        self,
        compartment_id: str,
    ) -> str:
        """生成约束名称。

        Generate constraint name.

        Args:
            compartment_id: 舱室标识。/ Compartment identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{compartment_id}"
