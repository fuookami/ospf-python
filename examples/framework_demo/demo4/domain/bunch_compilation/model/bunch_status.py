"""Bunch status enumeration.

任务组状态枚举 / Bunch status enumeration.
"""

from __future__ import annotations

from enum import StrEnum


class BunchStatus(StrEnum):
    """Lifecycle status of a scheduling bunch.

    调度任务组的生命周期状态。
    """

    PROPOSED = "PROPOSED"
    CONFIRMED = "CONFIRMED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        """Whether this status represents a terminal state.

        此状态是否为终态。
        """
        return self in (BunchStatus.EXECUTED, BunchStatus.CANCELLED)

    def can_transition_to(self, target: BunchStatus) -> bool:
        """Check whether a transition to the target status is valid.

        检查是否可以转换到目标状态。
        """
        valid_transitions: dict[BunchStatus, frozenset[BunchStatus]] = {
            BunchStatus.PROPOSED: frozenset(
                {
                    BunchStatus.CONFIRMED,
                    BunchStatus.CANCELLED,
                }
            ),
            BunchStatus.CONFIRMED: frozenset(
                {
                    BunchStatus.EXECUTED,
                    BunchStatus.CANCELLED,
                }
            ),
            BunchStatus.EXECUTED: frozenset(),
            BunchStatus.CANCELLED: frozenset(),
        }
        return target in valid_transitions.get(self, frozenset())

    @property
    def description(self) -> str:
        """Bilingual description of the status.

        状态的中英文描述。
        """
        descriptions: dict[BunchStatus, str] = {
            BunchStatus.PROPOSED: "已提议 / Proposed",
            BunchStatus.CONFIRMED: "已确认 / Confirmed",
            BunchStatus.EXECUTED: "已执行 / Executed",
            BunchStatus.CANCELLED: "已取消 / Cancelled",
        }
        return descriptions[self]
