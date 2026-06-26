"""危险品隔离约束 / Hazmat segregation constraint.

确保危险品货物之间保持规定的隔离距离。
Ensures that hazardous cargo items maintain required
segregation distances.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.hazmat_limit import (
        HazmatLimit,
    )
    from examples.framework_demo.demo2.domain.stowage.model.stowage_position import (
        StowagePosition,
    )


@dataclass(frozen=True)
class SegregationViolation:
    """隔离违反记录 / Segregation violation record.

    记录危险品隔离距离不足的信息。
    Records insufficient segregation distance between hazmat items.

    Attributes:
        item_a: 货物 A 标识 / Item A identifier.
        item_b: 货物 B 标识 / Item B identifier.
        required_distance: 所需隔离距离（米）/
            Required distance (m).
        actual_distance: 实际距离（米）/
            Actual distance (m).
        deficit: 不足量（米）/ Deficit amount (m).
    """

    item_a: str = ""
    """货物 A 标识 / Item A identifier."""

    item_b: str = ""
    """货物 B 标识 / Item B identifier."""

    required_distance: float = 0.0
    """所需隔离距离（米）/ Required distance (m)."""

    actual_distance: float = 0.0
    """实际距离（米）/ Actual distance (m)."""

    deficit: float = 0.0
    """不足量（米）/ Deficit amount (m)."""


@dataclass(frozen=True)
class HazmatSegregationConstraint:
    """危险品隔离约束 / Hazmat segregation constraint.

    验证危险品货物之间的距离满足隔离要求。对每对危险品
    货物计算实际距离，并与所需隔离距离比较。
    Validates that distances between hazardous cargo items meet
    segregation requirements. Computes actual distance for each
    hazmat item pair and compares against required distance.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "hazmat_segregation"
    """约束名称前缀 / Constraint name prefix."""

    def check_segregation(
        self,
        *,
        limits: tuple[HazmatLimit, ...],
        positions: dict[str, StowagePosition],
    ) -> tuple[SegregationViolation, ...]:
        """检查所有危险品的隔离距离。

        Check segregation distances for all hazmat items.

        Args:
            limits: 危险品限制列表。/ Hazmat limit list.
            positions: 货物位置映射。/ Item position mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[SegregationViolation] = []
        for i, limit_a in enumerate(limits):
            pos_a = positions.get(limit_a.item_id)
            if pos_a is None:
                continue
            for limit_b in limits[i + 1 :]:
                pos_b = positions.get(limit_b.item_id)
                if pos_b is None:
                    continue
                distance = self._euclidean_distance(pos_a, pos_b)
                required = limit_a.required_segregation_distance(
                    limit_b.hazard_class,
                )
                if distance < required:
                    violations.append(
                        SegregationViolation(
                            item_a=limit_a.item_id,
                            item_b=limit_b.item_id,
                            required_distance=required,
                            actual_distance=distance,
                            deficit=required - distance,
                        )
                    )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        limits: tuple[HazmatLimit, ...],
        positions: dict[str, StowagePosition],
    ) -> bool:
        """检查隔离约束是否可行。

        Check whether segregation constraints are feasible.

        Args:
            limits: 危险品限制列表。/ Hazmat limit list.
            positions: 货物位置映射。/ Item position mapping.

        Returns:
            所有隔离距离均满足时返回 True。
            True if all segregation distances are satisfied.
        """
        return (
            len(
                self.check_segregation(
                    limits=limits,
                    positions=positions,
                )
            )
            == 0
        )

    def hazmat_items_in_compartment(
        self,
        *,
        limits: tuple[HazmatLimit, ...],
        positions: dict[str, StowagePosition],
        compartment_id: str,
    ) -> tuple[str, ...]:
        """获取指定货舱中的危险品货物。

        Get hazmat items in a specific compartment.

        Args:
            limits: 危险品限制列表。/ Hazmat limit list.
            positions: 货物位置映射。/ Item position mapping.
            compartment_id: 舱室标识。/ Compartment identifier.

        Returns:
            货物标识元组。/ Tuple of item identifiers.
        """
        return tuple(
            lim.item_id
            for lim in limits
            if lim.item_id in positions
            and positions[lim.item_id].compartment == compartment_id
        )

    @staticmethod
    def _euclidean_distance(
        pos_a: StowagePosition,
        pos_b: StowagePosition,
    ) -> float:
        """计算两点间的欧氏距离。

        Compute Euclidean distance between two positions.

        Args:
            pos_a: 位置 A。/ Position A.
            pos_b: 位置 B。/ Position B.

        Returns:
            欧氏距离。/ Euclidean distance.
        """
        dx = pos_a.x - pos_b.x
        dy = pos_a.y - pos_b.y
        dz = pos_a.z - pos_b.z
        return float((dx * dx + dy * dy + dz * dz) ** 0.5)
