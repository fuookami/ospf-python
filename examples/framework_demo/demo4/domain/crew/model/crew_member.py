"""Crew member model.

机组成员模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class CrewRole(Enum):
    """Roles within a flight crew.

    飞行机组中的角色。
    """

    CAPTAIN = "CAPTAIN"
    """Pilot in command.

    机长。
    """

    FIRST_OFFICER = "FIRST_OFFICER"
    """Co-pilot.

    副驾驶。
    """

    FLIGHT_ENGINEER = "FLIGHT_ENGINEER"
    """Flight engineer.

    飞行工程师。
    """

    CABIN_CHIEF = "CABIN_CHIEF"
    """Chief cabin crew.

    乘务长。
    """

    CABIN_ATTENDANT = "CABIN_ATTENDANT"
    """Cabin crew member.

    乘务员。
    """


@dataclass(frozen=True)
class CrewMember:
    """An individual crew member with role and experience.

    具有角色和经验的单个机组成员。
    """

    member_id: str
    """Unique identifier for the member.

    成员的唯一标识符。
    """

    name: str
    """Member's full name.

    成员的全名。
    """

    role: CrewRole
    """Assigned role in the crew.

    在机组中的指定角色。
    """

    experience_hours: int = 0
    """Total flight experience in hours.

    总飞行经验（小时）。
    """

    @property
    def is_pilot(self) -> bool:
        """Whether this member is a pilot.

        此成员是否为飞行员。
        """
        return self.role in (
            CrewRole.CAPTAIN,
            CrewRole.FIRST_OFFICER,
        )

    @property
    def is_senior(self) -> bool:
        """Whether this member is senior (>5000 hours).

        此成员是否为资深（超过 5000 小时）。
        """
        return self.experience_hours > 5000

    @property
    def experience_years(self) -> float:
        """Experience expressed in years (approximate).

        以年表示的经验（近似值）。
        """
        return self.experience_hours / 1000.0
