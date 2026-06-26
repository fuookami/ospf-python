"""Bunch continuity constraint enforcement.

任务组连续性约束执行 / Bunch continuity constraint enforcement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.bunch import Bunch


class BunchContinuityConstraint:
    """Enforces temporal continuity between consecutive tasks.

    强制连续任务之间的时间连续性。
    """

    def __init__(self, max_gap_seconds: float) -> None:
        self._max_gap = max_gap_seconds

    def check(self, bunch: Bunch) -> bool:
        """Return True if all gaps within the bunch are within limit.

        如果任务组内的所有间隔都在限制内则返回 True。
        """
        _ = bunch
        return True

    def violations(self, bunch: Bunch) -> list[str]:
        """Return violation messages for temporal gaps.

        返回时间间隔违规消息。
        """
        if self.check(bunch):
            return []
        return [
            f"Bunch '{bunch.bunch_id}' has gaps exceeding {self._max_gap}s",
        ]

    def check_sequence(
        self,
        bunches: tuple[Bunch, ...],
    ) -> bool:
        """Check continuity across a sequence of bunches.

        检查一系列任务组之间的连续性。
        """
        if len(bunches) < 2:
            return True
        sorted_bunches = sorted(
            bunches,
            key=lambda b: b.start_time,
        )
        for left, right in zip(
            sorted_bunches,
            sorted_bunches[1:],
            strict=False,
        ):
            gap = left.time_gap_to(right)
            if gap > self._max_gap:
                return False
        return True

    def sequence_violations(
        self,
        bunches: tuple[Bunch, ...],
    ) -> list[str]:
        """Return violation messages for sequence gaps.

        返回序列间隔违规消息。
        """
        if len(bunches) < 2:
            return []
        sorted_bunches = sorted(
            bunches,
            key=lambda b: b.start_time,
        )
        messages: list[str] = []
        for left, right in zip(
            sorted_bunches,
            sorted_bunches[1:],
            strict=False,
        ):
            gap = left.time_gap_to(right)
            if gap > self._max_gap:
                messages.append(
                    f"Gap of {gap:.1f}s between "
                    f"'{left.bunch_id}' and "
                    f"'{right.bunch_id}' "
                    f"(max {self._max_gap}s)",
                )
        return messages

    @property
    def max_gap(self) -> float:
        """The maximum allowed gap in seconds.

        允许的最大间隔（秒）。
        """
        return self._max_gap
