"""Priority-based bunch generation strategy.

基于优先级的任务组生成策略 / Priority-based bunch generation.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..model.generation_result import GenerationResult
from ..model.generation_strategy import GenerationStrategy

if TYPE_CHECKING:
    from ..model.generation_config import GenerationConfig


@dataclass(frozen=True)
class TaskSlot:
    """A task available for bunch assignment.

    可用于任务组分配的任务槽。
    """

    task_id: str
    resource_type: str
    weight: float
    priority: int


class PriorityGenerator:
    """Generates bunches by grouping tasks by priority level.

    通过按优先级分组任务来生成任务组。
    """

    def __init__(self, config: GenerationConfig) -> None:
        self._config = config

    def generate(
        self,
        tasks: tuple[TaskSlot, ...],
    ) -> GenerationResult:
        """Group tasks by priority into separate bunches.

        按优先级将任务分组到不同的任务组。
        """
        if not tasks:
            return GenerationResult(
                bunches=(),
                score=0.0,
                strategy=GenerationStrategy.PRIORITY,
            )
        by_priority: dict[int, list[TaskSlot]] = defaultdict(list)
        for task in tasks:
            by_priority[task.priority].append(task)
        bunches: list[list[str]] = []
        max_size = self._config.max_bunch_size
        for priority in sorted(by_priority.keys()):
            group = by_priority[priority]
            chunk: list[str] = []
            for task in group:
                chunk.append(task.task_id)
                if len(chunk) >= max_size:
                    bunches.append(chunk)
                    chunk = []
            if chunk:
                bunches.append(chunk)
        score = self._score_priority(
            bunches,
            by_priority,
        )
        bunch_ids = tuple(f"priority_{i}" for i in range(len(bunches)))
        return GenerationResult(
            bunches=bunch_ids,
            score=score,
            strategy=GenerationStrategy.PRIORITY,
        )

    def _score_priority(
        self,
        bunches: list[list[str]],
        by_priority: dict[int, list[TaskSlot]],
    ) -> float:
        """Score based on priority coherence within bunches.

        基于任务组内优先级一致性进行评分。
        """
        if not bunches:
            return 0.0
        task_priority: dict[str, int] = {}
        for priority, group in by_priority.items():
            for task in group:
                task_priority[task.task_id] = priority
        coherent = 0
        for bunch in bunches:
            priorities = {task_priority.get(tid, 0) for tid in bunch}
            if len(priorities) <= 1:
                coherent += 1
        return coherent / len(bunches)
