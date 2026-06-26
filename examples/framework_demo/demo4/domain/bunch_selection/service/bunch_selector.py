"""Bunch selector for choosing optimal bunches from candidates.

任务组选择器：从候选中选择最优任务组。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateBunch:
    """A candidate bunch for selection.

    用于选择的候选任务组。
    """

    bunch_id: str
    score: float
    utilization: float


class BunchSelector:
    """Selects optimal bunches based on score and utilization.

    基于分数和利用率选择最优任务组。
    """

    def __init__(
        self,
        *,
        max_count: int,
        min_score: float = 0.0,
    ) -> None:
        self._max_count = max_count
        self._min_score = min_score

    def select(
        self,
        candidates: tuple[CandidateBunch, ...],
    ) -> tuple[str, ...]:
        """Select top-K candidates by score above the minimum.

        选择分数高于最低值的前 K 个候选。
        """
        eligible = [c for c in candidates if c.score >= self._min_score]
        sorted_candidates = sorted(
            eligible,
            key=lambda c: c.score,
            reverse=True,
        )
        selected = sorted_candidates[: self._max_count]
        return tuple(c.bunch_id for c in selected)

    def select_by_utilization(
        self,
        candidates: tuple[CandidateBunch, ...],
        min_utilization: float,
    ) -> tuple[str, ...]:
        """Select candidates that meet a utilization threshold.

        选择满足利用率阈值的候选。
        """
        eligible = [
            c
            for c in candidates
            if (c.utilization >= min_utilization and c.score >= self._min_score)
        ]
        sorted_candidates = sorted(
            eligible,
            key=lambda c: c.score,
            reverse=True,
        )
        selected = sorted_candidates[: self._max_count]
        return tuple(c.bunch_id for c in selected)

    def rank(
        self,
        candidates: tuple[CandidateBunch, ...],
    ) -> tuple[str, ...]:
        """Rank all candidates by score (descending).

        按分数降序排列所有候选。
        """
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.score,
            reverse=True,
        )
        return tuple(c.bunch_id for c in sorted_candidates)

    @property
    def max_count(self) -> int:
        """Maximum number of bunches to select.

        最多选择的任务组数量。
        """
        return self._max_count

    @property
    def min_score(self) -> float:
        """Minimum score threshold for eligibility.

        合格的最低分数阈值。
        """
        return self._min_score
