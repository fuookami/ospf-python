"""Selection result model for optimal bunch selection.

选择结果模型：最优任务组选择。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SelectionResult:
    """Result of selecting optimal bunches from candidates.

    从候选中选择最优任务组的结果。
    """

    selected_bunches: tuple[str, ...]
    score: float

    @property
    def count(self) -> int:
        """Number of selected bunches.

        已选任务组数量。
        """
        return len(self.selected_bunches)

    @property
    def is_empty(self) -> bool:
        """Whether no bunches were selected.

        是否没有选择任何任务组。
        """
        return self.count == 0

    @property
    def avg_score_per_bunch(self) -> float:
        """Average score per selected bunch.

        每个已选任务组的平均分数。
        """
        if self.count == 0:
            return 0.0
        return self.score / self.count

    def contains(self, bunch_id: str) -> bool:
        """Check whether a specific bunch was selected.

        检查特定任务组是否被选中。
        """
        return bunch_id in self.selected_bunches

    def merge(self, other: SelectionResult) -> SelectionResult:
        """Merge two selection results into one.

        将两个选择结果合并为一个。
        """
        combined_ids = list(self.selected_bunches)
        for bid in other.selected_bunches:
            if bid not in combined_ids:
                combined_ids.append(bid)
        return SelectionResult(
            selected_bunches=tuple(combined_ids),
            score=max(self.score, other.score),
        )
