"""Pilot model.

飞行员模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, unique


@unique
class LicenseType(Enum):
    """Pilot license types.

    飞行员执照类型。
    """

    ATPL = "ATPL"
    """Airline Transport Pilot License.

    航空运输飞行员执照。
    """

    CPL = "CPL"
    """Commercial Pilot License.

    商业飞行员执照。
    """

    PPL = "PPL"
    """Private Pilot License.

    私人飞行员执照。
    """


@dataclass(frozen=True)
class Pilot:
    """A pilot with license and aircraft ratings.

    具有执照和飞机等级的飞行员。
    """

    pilot_id: str
    """Unique identifier for the pilot.

    飞行员的唯一标识符。
    """

    name: str
    """Pilot's full name.

    飞行员的全名。
    """

    license_type: LicenseType
    """Type of pilot license held.

    持有的飞行员执照类型。
    """

    aircraft_ratings: tuple[str, ...] = field(default_factory=tuple)
    """Aircraft type ratings (e.g. 'A320', 'B737').

    飞机类型等级（如 'A320'、'B737'）。
    """

    flight_hours: int = 0
    """Total logged flight hours.

    总记录飞行小时。
    """

    @property
    def rating_count(self) -> int:
        """Number of aircraft type ratings.

        飞机类型等级数量。
        """
        return len(self.aircraft_ratings)

    def can_fly(self, aircraft_type: str) -> bool:
        """Check if pilot is rated for an aircraft type.

        检查飞行员是否有资格驾驶某飞机类型。

        Args:
            aircraft_type: Aircraft type to check.

        Returns:
            True if pilot holds the rating.
        """
        return aircraft_type in self.aircraft_ratings

    @property
    def is_atpl(self) -> bool:
        """Whether pilot holds ATPL license.

        飞行员是否持有 ATPL 执照。
        """
        return self.license_type == LicenseType.ATPL

    @property
    def is_experienced(self) -> bool:
        """Whether pilot has >3000 flight hours.

        飞行员是否有超过 3000 飞行小时。
        """
        return self.flight_hours > 3000

    @property
    def experience_level(self) -> str:
        """Categorical experience level.

        分类经验水平。
        """
        if self.flight_hours > 10000:
            return "veteran"
        if self.flight_hours > 5000:
            return "senior"
        if self.flight_hours > 1500:
            return "mid-level"
        return "junior"
