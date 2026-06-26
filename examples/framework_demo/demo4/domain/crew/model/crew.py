"""Crew model.

机组模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Crew:
    """A flight crew with qualifications and base airport.

    具有资质和基地机场的飞行机组。
    """

    crew_id: str
    """Unique identifier for the crew.

    机组的唯一标识符。
    """

    name: str
    """Crew name or designation.

    机组名称或代号。
    """

    base_airport: str
    """Home base airport IATA code.

    基地机场 IATA 代码。
    """

    qualifications: tuple[str, ...] = field(default_factory=tuple)
    """Aircraft type qualifications held by this crew.

    此机组持有的飞机类型资质。
    """

    @property
    def qualification_count(self) -> int:
        """Number of type qualifications.

        类型资质数量。
        """
        return len(self.qualifications)

    def is_qualified_for(
        self,
        aircraft_type: str,
    ) -> bool:
        """Check if crew is qualified for an aircraft type.

        检查机组是否有资格操作某飞机类型。

        Args:
            aircraft_type: Aircraft type code.

        Returns:
            True if crew holds the qualification.
        """
        return aircraft_type in self.qualifications

    @property
    def is_multi_qualification(self) -> bool:
        """Whether crew has multiple type qualifications.

        机组是否具有多种类型资质。
        """
        return len(self.qualifications) > 1
