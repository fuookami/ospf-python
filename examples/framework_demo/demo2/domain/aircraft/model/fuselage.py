"""机身定义 / Fuselage definition.

航空器货舱机身几何定义。
Aircraft cargo fuselage geometry definition.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CargoDoor:
    """货舱门 / Cargo door.

    描述机身上的一个货舱门开口。
    Describes a cargo door opening on the fuselage.

    Attributes:
        door_id: 货舱门标识 / Door identifier.
        position_along: 沿机身纵向位置 (m) / Longitudinal position (m).
        width: 门开口宽度 (m) / Door opening width (m).
        height: 门开口高度 (m) / Door opening height (m).
    """

    door_id: str
    """货舱门标识 / Door identifier."""

    position_along: float
    """沿机身纵向位置 (m) / Longitudinal position along fuselage (m)."""

    width: float
    """门开口宽度 (m) / Door opening width (m)."""

    height: float
    """门开口高度 (m) / Door opening height (m)."""

    @property
    def area(self) -> float:
        """门开口面积 / Door opening area.

        Returns:
            宽 x 高 (m^2) / Width x Height (m^2).
        """
        return self.width * self.height


@dataclass(frozen=True)
class Fuselage:
    """机身 / Fuselage.

    描述航空器机身的货舱相关几何参数。
    Describes cargo-related geometric parameters of
    an aircraft fuselage.

    Attributes:
        length: 机身长度 (m) / Fuselage length (m).
        max_width: 机身最大宽度 (m) / Max fuselage width (m).
        max_height: 机身最大高度 (m) / Max fuselage height (m).
        cargo_doors: 货舱门列表 / List of cargo doors.
    """

    length: float
    """机身长度 (m) / Fuselage length (m)."""

    max_width: float
    """机身最大宽度 (m) / Max fuselage width (m)."""

    max_height: float
    """机身最大高度 (m) / Max fuselage height (m)."""

    cargo_doors: tuple[CargoDoor, ...]
    """货舱门列表 / List of cargo doors."""

    @staticmethod
    def create(
        *,
        length: float,
        max_width: float,
        max_height: float,
        cargo_doors: tuple[CargoDoor, ...] = (),
    ) -> Fuselage:
        """创建机身实例 / Create fuselage instance.

        Args:
            length: 机身长度 / Fuselage length.
            max_width: 机身最大宽度 / Max fuselage width.
            max_height: 机身最大高度 / Max fuselage height.
            cargo_doors: 货舱门列表，默认空 / Cargo doors, default empty.

        Returns:
            机身实例 / Fuselage instance.
        """
        return Fuselage(
            length=length,
            max_width=max_width,
            max_height=max_height,
            cargo_doors=cargo_doors,
        )

    @property
    def cross_section_area(self) -> float:
        """机身截面积估算 / Fuselage cross-section area estimate.

        假设椭圆截面的面积近似。
        Approximate area assuming elliptical cross-section.

        Returns:
            截面积 (m^2) / Cross-section area (m^2).
        """
        import math

        return math.pi * (self.max_width / 2) * (self.max_height / 2)

    @property
    def cargo_door_count(self) -> int:
        """货舱门数量 / Number of cargo doors.

        Returns:
            货舱门数量 / Cargo door count.
        """
        return len(self.cargo_doors)

    def largest_door(self) -> CargoDoor | None:
        """获取最大货舱门 / Get the largest cargo door.

        Returns:
            最大货舱门，无门时返回 None /
            Largest cargo door, None if no doors.
        """
        if not self.cargo_doors:
            return None
        return max(self.cargo_doors, key=lambda d: d.area)
