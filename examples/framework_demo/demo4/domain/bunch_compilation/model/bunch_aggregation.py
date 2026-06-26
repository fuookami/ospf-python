"""Bunch aggregation for grouping bunches by status.

按状态分组的任务组聚合 / Bunch aggregation by status.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .bunch_status import BunchStatus

if TYPE_CHECKING:
    from .bunch import Bunch


@dataclass(frozen=True)
class BunchAggregation:
    """Aggregation of bunches grouped by their status.

    按状态分组的任务组聚合。
    """

    bunches: tuple[Bunch, ...]
    by_status: dict[BunchStatus, tuple[Bunch, ...]]

    @classmethod
    def from_bunches(cls, bunches: tuple[Bunch, ...]) -> BunchAggregation:
        """Create aggregation by grouping bunches by status.

        通过按状态分组任务组来创建聚合。
        """
        groups: dict[BunchStatus, list[Bunch]] = defaultdict(list)
        for bunch in bunches:
            status = BunchStatus.PROPOSED
            groups[status].append(bunch)
        by_status = {status: tuple(items) for status, items in groups.items()}
        return cls(bunches=bunches, by_status=by_status)

    @classmethod
    def from_bunches_with_statuses(
        cls,
        bunch_statuses: tuple[tuple[Bunch, BunchStatus], ...],
    ) -> BunchAggregation:
        """Create aggregation from bunches paired with their statuses.

        从配对了状态的任务组创建聚合。
        """
        groups: dict[BunchStatus, list[Bunch]] = defaultdict(list)
        all_bunches: list[Bunch] = []
        for bunch, status in bunch_statuses:
            all_bunches.append(bunch)
            groups[status].append(bunch)
        by_status = {status: tuple(items) for status, items in groups.items()}
        return cls(
            bunches=tuple(all_bunches),
            by_status=by_status,
        )

    @property
    def count(self) -> int:
        """Total number of bunches.

        任务组总数。
        """
        return len(self.bunches)

    @property
    def status_counts(self) -> dict[BunchStatus, int]:
        """Count of bunches per status.

        每种状态的任务组数量。
        """
        return {status: len(items) for status, items in self.by_status.items()}
