"""易碎品约束 / Fragility constraint.

确保易碎品不会被重物压在下方。
Ensures that fragile items are not stacked beneath heavy items.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
        StowageItem,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_position import (
        StowagePosition,
    )


@dataclass(frozen=True)
class FragilityViolation:
    """易碎品违反记录 / Fragility violation record.

    记录易碎品被重物压叠的信息。
    Records fragile items being stacked beneath heavy items.

    Attributes:
        fragile_item: 易碎货物标识 /
            Fragile item identifier.
        heavy_item: 重物货物标识 /
            Heavy item identifier.
        vertical_overlap: 垂直重叠量（米）/
            Vertical overlap (m).
        pressure_ratio: 压力比率 /
            Pressure ratio.
    """

    fragile_item: str = ""
    """易碎货物标识 / Fragile item identifier."""

    heavy_item: str = ""
    """重物货物标识 / Heavy item identifier."""

    vertical_overlap: float = 0.0
    """垂直重叠量（米）/ Vertical overlap (m)."""

    pressure_ratio: float = 0.0
    """压力比率 / Pressure ratio."""


@dataclass(frozen=True)
class FragilityConstraint:
    """易碎品约束 / Fragility constraint.

    验证易碎品不被重物压叠。检查同一货舱中垂直方向上
    的货物关系，确保易碎品上方不放置超出其抗压能力的重物。
    Validates that fragile items are not stacked beneath heavy
    items. Checks vertical relationships within the same
    compartment to ensure no excessive weight above fragile items.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        max_pressure_ratio: 最大允许压力比率 /
            Maximum allowed pressure ratio.
    """

    constraint_name_prefix: str = "fragility"
    """约束名称前缀 / Constraint name prefix."""

    max_pressure_ratio: float = 0.5
    """最大允许压力比率 / Maximum allowed pressure ratio."""

    def check_stacking(
        self,
        *,
        items: tuple[StowageItem, ...],
        positions: dict[str, StowagePosition],
    ) -> tuple[FragilityViolation, ...]:
        """检查货物堆叠是否违反易碎品约束。

        Check whether cargo stacking violates fragility constraints.

        Args:
            items: 货物列表。/ Item list.
            positions: 货物位置映射。/ Item position mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[FragilityViolation] = []
        positioned = [
            (item, positions[item.item_id])
            for item in items
            if item.item_id in positions
        ]
        for i, (item_a, pos_a) in enumerate(positioned):
            for item_b, pos_b in positioned[i + 1 :]:
                if pos_a.compartment != pos_b.compartment:
                    continue
                overlap = self._vertical_overlap(pos_a, pos_b)
                if overlap <= 0.0:
                    continue
                if item_a.is_fragile and not item_b.is_fragile:
                    ratio = self._pressure_ratio(
                        item_a,
                        item_b,
                        overlap,
                    )
                    if ratio > self.max_pressure_ratio:
                        violations.append(
                            FragilityViolation(
                                fragile_item=item_a.item_id,
                                heavy_item=item_b.item_id,
                                vertical_overlap=overlap,
                                pressure_ratio=ratio,
                            )
                        )
                elif item_b.is_fragile and not item_a.is_fragile:
                    ratio = self._pressure_ratio(
                        item_b,
                        item_a,
                        overlap,
                    )
                    if ratio > self.max_pressure_ratio:
                        violations.append(
                            FragilityViolation(
                                fragile_item=item_b.item_id,
                                heavy_item=item_a.item_id,
                                vertical_overlap=overlap,
                                pressure_ratio=ratio,
                            )
                        )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        items: tuple[StowageItem, ...],
        positions: dict[str, StowagePosition],
    ) -> bool:
        """检查易碎品约束是否可行。

        Check whether fragility constraints are feasible.

        Args:
            items: 货物列表。/ Item list.
            positions: 货物位置映射。/ Item position mapping.

        Returns:
            所有易碎品均安全时返回 True。
            True if all fragile items are safe.
        """
        return (
            len(
                self.check_stacking(
                    items=items,
                    positions=positions,
                )
            )
            == 0
        )

    def fragile_items_in_compartment(
        self,
        *,
        items: tuple[StowageItem, ...],
        positions: dict[str, StowagePosition],
        compartment_id: str,
    ) -> tuple[str, ...]:
        """获取指定货舱中的易碎品。

        Get fragile items in a specific compartment.

        Args:
            items: 货物列表。/ Item list.
            positions: 货物位置映射。/ Item position mapping.
            compartment_id: 舱室标识。/ Compartment identifier.

        Returns:
            易碎品货物标识元组。/ Tuple of fragile item identifiers.
        """
        return tuple(
            item.item_id
            for item in items
            if item.is_fragile
            and item.item_id in positions
            and positions[item.item_id].compartment == compartment_id
        )

    @staticmethod
    def _vertical_overlap(
        pos_a: StowagePosition,
        pos_b: StowagePosition,
    ) -> float:
        """计算垂直方向重叠量。

        Calculate vertical overlap.

        Args:
            pos_a: 位置 A。/ Position A.
            pos_b: 位置 B。/ Position B.

        Returns:
            重叠量（米），无重叠时返回 0.0。
            Overlap (m), or 0.0 if no overlap.
        """
        return max(0.0, 1.0 - abs(pos_a.z - pos_b.z))

    @staticmethod
    def _pressure_ratio(
        fragile: StowageItem,
        heavy: StowageItem,
        overlap: float,
    ) -> float:
        """计算压力比率。

        Calculate pressure ratio.

        Args:
            fragile: 易碎品。/ Fragile item.
            heavy: 重物。/ Heavy item.
            overlap: 重叠量。/ Overlap.

        Returns:
            压力比率。/ Pressure ratio.
        """
        resistance = fragile.stacking_resistance()
        if resistance <= 0.0:
            return float("inf")
        return (heavy.weight * overlap) / (fragile.weight * resistance)
