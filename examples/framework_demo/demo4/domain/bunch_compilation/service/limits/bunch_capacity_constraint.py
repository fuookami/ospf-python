"""Bunch capacity constraint enforcement.

任务组容量约束执行 / Bunch capacity constraint enforcement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.bunch import Bunch


class BunchCapacityConstraint:
    """Enforces a maximum task count per bunch.

    强制每个任务组的最大任务数量。
    """

    def __init__(self, max_tasks_per_bunch: int) -> None:
        self._max_tasks = max_tasks_per_bunch

    def check(self, bunch: Bunch) -> bool:
        """Return True if the bunch is within capacity.

        如果任务组在容量范围内则返回 True。
        """
        return bunch.task_count <= self._max_tasks

    def violations(self, bunch: Bunch) -> list[str]:
        """Return violation messages for the bunch.

        返回任务组的违规消息。
        """
        if self.check(bunch):
            return []
        excess = bunch.task_count - self._max_tasks
        return [
            f"Bunch '{bunch.bunch_id}' exceeds capacity "
            f"by {excess} tasks "
            f"({bunch.task_count}/{self._max_tasks})",
        ]

    def filter_compliant(
        self,
        bunches: tuple[Bunch, ...],
    ) -> tuple[Bunch, ...]:
        """Return only bunches that satisfy the capacity limit.

        仅返回满足容量限制的任务组。
        """
        return tuple(bunch for bunch in bunches if self.check(bunch))

    def apply(
        self,
        bunches: tuple[Bunch, ...],
    ) -> tuple[Bunch, ...]:
        """Alias for filter_compliant.

        filter_compliant 的别名。
        """
        return self.filter_compliant(bunches)

    @property
    def max_tasks(self) -> int:
        """The maximum tasks allowed per bunch.

        每个任务组允许的最大任务数。
        """
        return self._max_tasks
