"""Generation result model.

生成结果模型 / Generation result model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .generation_strategy import GenerationStrategy


@dataclass(frozen=True)
class GenerationResult:
    """Result of a bunch generation strategy execution.

    任务组生成策略执行的结果。
    """

    bunches: tuple[str, ...]
    score: float
    strategy: GenerationStrategy

    @property
    def bunch_count(self) -> int:
        """Number of bunches generated.

        生成的任务组数量。
        """
        return len(self.bunches)

    def is_better_than(self, other: GenerationResult) -> bool:
        """Compare this result against another by score.

        按分数与此结果与另一个进行比较。
        """
        return self.score > other.score

    @property
    def is_viable(self) -> bool:
        """Whether this result has a positive score and bunches.

        此结果是否有正分数和任务组。
        """
        return self.score > 0.0 and self.bunch_count > 0
