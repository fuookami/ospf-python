"""Greedy bunch generation strategy.

贪心任务组生成策略 / Greedy bunch generation strategy.
"""

from __future__ import annotations

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


class GreedyGenerator:
    """Generates bunches by greedily filling capacity first.

    通过优先填满容量来贪心生成任务组。
    """

    def __init__(self, config: GenerationConfig) -> None:
        self._config = config

    def generate(
        self,
        tasks: tuple[TaskSlot, ...],
    ) -> GenerationResult:
        """Assign tasks to bunches using a greedy fill strategy.

        使用贪心填充策略将任务分配到任务组。
        """
        if not tasks:
            return GenerationResult(
                bunches=(),
                score=0.0,
                strategy=GenerationStrategy.GREEDY,
            )
        sorted_tasks = sorted(
            tasks,
            key=lambda t: t.weight,
            reverse=True,
        )
        bunches: list[list[str]] = []
        current: list[str] = []
        current_load = 0.0
        max_size = self._config.max_bunch_size
        for task in sorted_tasks:
            if len(current) >= max_size or (
                current_load + task.weight > 1.0 and current
            ):
                bunches.append(current)
                current = []
                current_load = 0.0
            current.append(task.task_id)
            current_load += task.weight
        if current:
            bunches.append(current)
        score = self._score_bunches(bunches, tuple(sorted_tasks))
        bunch_ids = tuple(f"greedy_{i}" for i in range(len(bunches)))
        return GenerationResult(
            bunches=bunch_ids,
            score=score,
            strategy=GenerationStrategy.GREEDY,
        )

    def _score_bunches(
        self,
        bunches: list[list[str]],
        tasks: tuple[TaskSlot, ...],
    ) -> float:
        """Calculate a quality score for the generated bunches.

        计算生成任务组的质量分数。
        """
        if not bunches:
            return 0.0
        task_map = {t.task_id: t for t in tasks}
        total_weight = sum(t.weight for t in tasks)
        if total_weight == 0.0:
            return 0.0
        bunch_scores: list[float] = []
        for bunch in bunches:
            load = sum(task_map[tid].weight for tid in bunch if tid in task_map)
            bunch_scores.append(
                min(load, 1.0) / max(len(bunch), 1),
            )
        avg = sum(bunch_scores) / len(bunch_scores)
        balance = 1.0 - (
            max(bunch_scores) - min(bunch_scores) if len(bunch_scores) > 1 else 0.0
        )
        return avg * 0.6 + balance * 0.4
