"""最大容积约束 / Maximum volume constraint.

确保每个货舱的装载容积不超过其最大承载限制。
Ensures that each compartment's loaded volume does not exceed
its maximum capacity limit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.stowage.model.volume_limit import (
    VolumeLimit,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_compartment import (
        StowageCompartment,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )


@dataclass(frozen=True)
class VolumeViolation:
    """容积违反记录 / Volume violation record.

    记录一个货舱的容积超限信息。
    Records volume excess information for a compartment.

    Attributes:
        compartment_id: 舱室标识 / Compartment identifier.
        current_volume: 当前容积（立方米）/
            Current volume (cubic meters).
        max_volume: 最大容积（立方米）/
            Maximum volume (cubic meters).
        excess: 超出量（立方米）/ Excess amount (cubic meters).
    """

    compartment_id: str = ""
    """舱室标识 / Compartment identifier."""

    current_volume: float = 0.0
    """当前容积（立方米）/ Current volume (cubic meters)."""

    max_volume: float = 0.0
    """最大容积（立方米）/ Maximum volume (cubic meters)."""

    excess: float = 0.0
    """超出量（立方米）/ Excess amount (cubic meters)."""


@dataclass(frozen=True)
class MaxVolumeConstraint:
    """最大容积约束 / Maximum volume constraint.

    验证每个货舱的装载容积不超过其最大承载限制。
    遍历所有货舱，汇总已分配货物的体积并与限制比较。
    Validates that each compartment's loaded volume does not exceed
    its maximum capacity. Iterates over all compartments, summing
    assigned item volumes and comparing against limits.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "max_volume"
    """约束名称前缀 / Constraint name prefix."""

    def build_limits(
        self,
        compartments: tuple[StowageCompartment, ...],
    ) -> tuple[VolumeLimit, ...]:
        """从货舱信息构建容积限制列表。

        Build volume limit list from compartment information.

        Args:
            compartments: 货舱列表。/ Compartment list.

        Returns:
            容积限制元组。/ Tuple of volume limits.
        """
        return tuple(
            VolumeLimit(
                compartment=comp.comp_id,
                max_volume=comp.max_volume,
            )
            for comp in compartments
            if comp.max_volume > 0.0
        )

    def check_compartments(
        self,
        *,
        compartments: tuple[StowageCompartment, ...],
        items: tuple[StowageItem, ...],
        assignments: dict[str, tuple[str, ...]],
    ) -> tuple[VolumeViolation, ...]:
        """检查所有货舱的容积约束。

        Check volume constraints for all compartments.

        Args:
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            assignments: 货物到货舱的分配映射。/
                Item-to-compartment assignment mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        item_map = {item.item_id: item for item in items}
        violations: list[VolumeViolation] = []
        for comp in compartments:
            assigned_ids = assignments.get(comp.comp_id, ())
            current = sum(
                item_map[sid].volume for sid in assigned_ids if sid in item_map
            )
            if current > comp.max_volume:
                violations.append(
                    VolumeViolation(
                        compartment_id=comp.comp_id,
                        current_volume=current,
                        max_volume=comp.max_volume,
                        excess=current - comp.max_volume,
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
        """检查容积约束是否可行。

        Check whether volume constraints are feasible.

        Args:
            compartments: 货舱列表。/ Compartment list.
            items: 货物列表。/ Item list.
            assignments: 分配映射。/ Assignment mapping.

        Returns:
            所有货舱容积均在限制内时返回 True。
            True if all compartment volumes are within limits.
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

    def compartment_volume_usage(
        self,
        *,
        compartment_id: str,
        items: tuple[StowageItem, ...],
        assigned_ids: tuple[str, ...],
    ) -> float:
        """计算货舱的当前容积使用量。

        Calculate current volume usage for a compartment.

        Args:
            compartment_id: 舱室标识。/ Compartment identifier.
            items: 货物列表。/ Item list.
            assigned_ids: 已分配的货物标识。/ Assigned item IDs.

        Returns:
            当前容积使用量（立方米）。
            Current volume usage (cubic meters).
        """
        item_map = {item.item_id: item for item in items}
        return sum(item_map[sid].volume for sid in assigned_ids if sid in item_map)

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
