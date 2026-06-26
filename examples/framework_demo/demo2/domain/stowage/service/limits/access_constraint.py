"""可达性约束 / Access constraint.

确保货物不会阻塞货舱门和舱口。
Ensures that cargo does not block compartment doors and hatches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.stowage.model.stowage_position import (
        StowagePosition,
    )


@dataclass(frozen=True)
class AccessPoint:
    """可达点 / Access point.

    描述货舱门或舱口的位置和所需通道空间。
    Describes the position and required clearance of a
    compartment door or hatch.

    Attributes:
        point_id: 可达点标识 / Access point identifier.
        compartment_id: 所属舱室 / Associated compartment.
        x: 纵向坐标 / Longitudinal coordinate.
        y: 横向坐标 / Lateral coordinate.
        z: 垂直坐标 / Vertical coordinate.
        clearance_radius: 所需通道半径（米）/
            Required clearance radius (m).
    """

    point_id: str = ""
    """可达点标识 / Access point identifier."""

    compartment_id: str = ""
    """所属舱室 / Associated compartment."""

    x: float = 0.0
    """纵向坐标 / Longitudinal coordinate."""

    y: float = 0.0
    """横向坐标 / Lateral coordinate."""

    z: float = 0.0
    """垂直坐标 / Vertical coordinate."""

    clearance_radius: float = 1.0
    """所需通道半径（米）/ Required clearance radius (m)."""


@dataclass(frozen=True)
class AccessViolation:
    """可达性违反记录 / Access violation record.

    记录货物阻塞可达点的信息。
    Records cargo blocking an access point.

    Attributes:
        item_id: 货物标识 / Item identifier.
        access_point: 被阻塞的可达点 /
            Blocked access point.
        distance: 货物到可达点的距离 /
            Distance from item to access point.
        blocking_amount: 阻塞量 /
            Blocking amount.
    """

    item_id: str = ""
    """货物标识 / Item identifier."""

    access_point: AccessPoint = None  # type: ignore[assignment]
    """被阻塞的可达点 / Blocked access point."""

    distance: float = 0.0
    """货物到可达点的距离 / Distance to access point."""

    blocking_amount: float = 0.0
    """阻塞量 / Blocking amount."""


@dataclass(frozen=True)
class AccessConstraint:
    """可达性约束 / Access constraint.

    验证货物不阻塞货舱门和舱口的通道空间。检查每个可达点
    周围是否有货物侵入所需通道半径。
    Validates that cargo does not block door and hatch clearance.
    Checks each access point for cargo intrusion into required
    clearance radius.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "access"
    """约束名称前缀 / Constraint name prefix."""

    def check_access(
        self,
        *,
        access_points: tuple[AccessPoint, ...],
        positions: dict[str, StowagePosition],
    ) -> tuple[AccessViolation, ...]:
        """检查可达性约束。

        Check access constraints.

        Args:
            access_points: 可达点列表。/ Access point list.
            positions: 货物位置映射。/ Item position mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[AccessViolation] = []
        for item_id, pos in positions.items():
            for ap in access_points:
                if pos.compartment != ap.compartment_id:
                    continue
                distance = self._distance_to_point(pos, ap)
                if distance < ap.clearance_radius:
                    violations.append(
                        AccessViolation(
                            item_id=item_id,
                            access_point=ap,
                            distance=distance,
                            blocking_amount=(ap.clearance_radius - distance),
                        )
                    )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        access_points: tuple[AccessPoint, ...],
        positions: dict[str, StowagePosition],
    ) -> bool:
        """检查可达性约束是否可行。

        Check whether access constraints are feasible.

        Args:
            access_points: 可达点列表。/ Access point list.
            positions: 货物位置映射。/ Item position mapping.

        Returns:
            所有可达点均未被阻塞时返回 True。
            True if all access points are unblocked.
        """
        return (
            len(
                self.check_access(
                    access_points=access_points,
                    positions=positions,
                )
            )
            == 0
        )

    def blocked_items_for_point(
        self,
        *,
        access_point: AccessPoint,
        positions: dict[str, StowagePosition],
    ) -> tuple[str, ...]:
        """获取阻塞指定可达点的货物。

        Get items blocking a specific access point.

        Args:
            access_point: 可达点。/ Access point.
            positions: 货物位置映射。/ Item position mapping.

        Returns:
            阻塞货物标识元组。/ Tuple of blocking item IDs.
        """
        blocked: list[str] = []
        for item_id, pos in positions.items():
            if pos.compartment != access_point.compartment_id:
                continue
            distance = self._distance_to_point(pos, access_point)
            if distance < access_point.clearance_radius:
                blocked.append(item_id)
        return tuple(blocked)

    @staticmethod
    def _distance_to_point(
        pos: StowagePosition,
        point: AccessPoint,
    ) -> float:
        """计算位置到可达点的距离。

        Calculate distance from position to access point.

        Args:
            pos: 货物位置。/ Item position.
            point: 可达点。/ Access point.

        Returns:
            欧氏距离。/ Euclidean distance.
        """
        dx = pos.x - point.x
        dy = pos.y - point.y
        dz = pos.z - point.z
        return float((dx * dx + dy * dy + dz * dz) ** 0.5)
