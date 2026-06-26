"""舱门定义 / Hatch door definition.

航空器货舱舱门（隔板门）定义。
Aircraft cargo hatch door (partition door) definition.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HatchDoor:
    """舱门 / Hatch door.

    描述航空器货舱内的隔板门或检修口。
    Describes a partition door or access hatch within
    an aircraft cargo hold.

    Attributes:
        door_id: 舱门标识 / Door identifier.
        position: 舱门位置描述 / Door position description.
        width: 舱门宽度 (m) / Door width (m).
        height: 舱门高度 (m) / Door height (m).
        max_load: 舱门可承受最大载荷 (kg) / Max load the door can bear (kg).
    """

    door_id: str
    """舱门标识 / Door identifier."""

    position: str
    """舱门位置描述 / Door position description."""

    width: float
    """舱门宽度 (m) / Door width (m)."""

    height: float
    """舱门高度 (m) / Door height (m)."""

    max_load: float
    """舱门可承受最大载荷 (kg) / Max load the door can bear (kg)."""

    @staticmethod
    def create(
        *,
        door_id: str,
        position: str,
        width: float,
        height: float,
        max_load: float = 0.0,
    ) -> HatchDoor:
        """创建舱门实例 / Create hatch door instance.

        Args:
            door_id: 舱门标识 / Door identifier.
            position: 舱门位置描述 / Door position description.
            width: 舱门宽度 / Door width.
            height: 舱门高度 / Door height.
            max_load: 最大载荷，默认 0 / Max load, default 0.

        Returns:
            舱门实例 / Hatch door instance.
        """
        return HatchDoor(
            door_id=door_id,
            position=position,
            width=width,
            height=height,
            max_load=max_load,
        )

    @property
    def opening_area(self) -> float:
        """舱门开口面积 / Door opening area.

        Returns:
            宽 x 高 (m^2) / Width x Height (m^2).
        """
        return self.width * self.height

    def can_accept_load(self, load: float) -> bool:
        """检查是否可承受指定载荷 / Check if load is acceptable.

        Args:
            load: 待检查的载荷 (kg) / Load to check (kg).

        Returns:
            载荷不超过最大值时为 True / True if load does not exceed max.
        """
        return load <= self.max_load

    def with_max_load(self, max_load: float) -> HatchDoor:
        """创建不同载荷限制的舱门 / Create door with different max load.

        Args:
            max_load: 新最大载荷 / New max load.

        Returns:
            新舱门实例 / New hatch door instance.
        """
        return HatchDoor(
            door_id=self.door_id,
            position=self.position,
            width=self.width,
            height=self.height,
            max_load=max_load,
        )
