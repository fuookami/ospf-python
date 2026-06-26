"""装载位置 / Stowage position.

定义货物在飞机货舱中的三维位置。
Defines the 3D position of cargo in an aircraft compartment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StowagePosition:
    """装载位置 / Stowage position.

    描述货物在货舱中的具体位置，包括舱室、槽位和三维坐标。
    Describes the specific position of cargo in a compartment,
    including compartment, slot, and 3D coordinates.

    Attributes:
        compartment: 舱室标识 / Compartment identifier.
        slot_id: 槽位标识 / Slot identifier.
        x: 纵向坐标（机头方向为正）/
            Longitudinal coordinate (positive toward nose).
        y: 横向坐标（右翼方向为正）/
            Lateral coordinate (positive toward right wing).
        z: 垂直坐标（向上为正）/
            Vertical coordinate (positive upward).
    """

    compartment: str = ""
    """舱室标识 / Compartment identifier."""

    slot_id: str = ""
    """槽位标识 / Slot identifier."""

    x: float = 0.0
    """纵向坐标（米）/ Longitudinal coordinate (m)."""

    y: float = 0.0
    """横向坐标（米）/ Lateral coordinate (m)."""

    z: float = 0.0
    """垂直坐标（米）/ Vertical coordinate (m)."""

    @staticmethod
    def create(
        *,
        compartment: str,
        slot_id: str,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ) -> StowagePosition:
        """创建装载位置。

        Create stowage position.

        Args:
            compartment: 舱室标识。/ Compartment identifier.
            slot_id: 槽位标识。/ Slot identifier.
            x: 纵向坐标。/ Longitudinal coordinate.
            y: 横向坐标。/ Lateral coordinate.
            z: 垂直坐标。/ Vertical coordinate.

        Returns:
            位置实例。/ Position instance.
        """
        return StowagePosition(
            compartment=compartment,
            slot_id=slot_id,
            x=x,
            y=y,
            z=z,
        )

    @property
    def height_from_floor(self) -> float:
        """距货舱底部的高度。

        Height from compartment floor.

        Returns:
            z 坐标值。/ z coordinate value.
        """
        return self.z

    def lateral_distance_to_center(self) -> float:
        """到飞机中心线的横向距离。

        Lateral distance to aircraft centerline.

        Returns:
            y 坐标的绝对值。/ Absolute value of y coordinate.
        """
        return abs(self.y)

    def longitudinal_moment(self, weight: float) -> float:
        """计算纵向力矩。

        Calculate longitudinal moment.

        Args:
            weight: 货物重量（千克）。/ Cargo weight (kg).

        Returns:
            重量乘以纵向坐标。/ Weight times longitudinal coordinate.
        """
        return weight * self.x

    def lateral_moment(self, weight: float) -> float:
        """计算横向力矩。

        Calculate lateral moment.

        Args:
            weight: 货物重量（千克）。/ Cargo weight (kg).

        Returns:
            重量乘以横向坐标。/ Weight times lateral coordinate.
        """
        return weight * self.y
