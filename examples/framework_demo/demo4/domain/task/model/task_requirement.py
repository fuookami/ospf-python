"""Task requirement model.

任务需求模型。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskRequirement:
    """Resource requirements for a flight task.

    航班任务的资源需求。
    """

    task_id: str
    """ID of the task this requirement belongs to.

    此需求所属任务的 ID。
    """

    crew_count: int
    """Required number of crew members.

    所需的机组成员数量。
    """

    aircraft_type: str
    """Required aircraft type code.

    所需的飞机类型代码。
    """

    min_experience: int = 0
    """Minimum flight hours required for crew.

    机组人员的最低飞行小时要求。
    """

    @property
    def is_high_experience(self) -> bool:
        """Whether the task requires high experience (>5000 hours).

        任务是否要求高经验（超过 5000 小时）。
        """
        return self.min_experience > 5000

    @property
    def is_large_crew(self) -> bool:
        """Whether the task requires a large crew (>6 members).

        任务是否需要大型机组（超过 6 人）。
        """
        return self.crew_count > 6
