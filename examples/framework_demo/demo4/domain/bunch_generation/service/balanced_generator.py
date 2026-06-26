"""Balanced bunch generation strategy.

均衡任务组生成策略 / Balanced bunch generation strategy.
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


class BalancedGenerator:
    """Generates bunches that distribute load evenly.

    生成均匀分配负载的任务组。
    """

    def __init__(self, config: GenerationConfig) -> None:
        self._config = config

    def generate(
        self,
        tasks: tuple[TaskSlot, ...],
    ) -> GenerationResult:
        """Distribute tasks evenly across bunches.

        将任务均匀分配到各任务组。
        """
        if not tasks:
            return GenerationResult(
                bunches=(),
                score=0.0,
                strategy=GenerationStrategy.BALANCED,
            )
        total_weight = sum(t.weight for t in tasks)
        max_size = self._config.max_bunch_size
        target_bunches = max(
            1,
            min(
                len(tasks),
                int(total_weight / 0.8) + 1,
            ),
        )
        target_bunches = min(
            target_bunches,
            len(tasks) // max(max_size // 10, 1) + 1,
        )
        buckets: list[list[str]] = [[] for _ in range(target_bunches)]
        loads = [0.0] * target_bunches
        sorted_tasks = sorted(
            tasks,
            key=lambda t: t.weight,
            reverse=True,
        )
        for task in sorted_tasks:
            min_idx = loads.index(min(loads))
            if len(buckets[min_idx]) < max_size:
                buckets[min_idx].append(task.task_id)
                loads[min_idx] += task.weight
        non_empty = [b for b in buckets if b]
        score = self._score_balance(loads, non_empty)
        bunch_ids = tuple(f"balanced_{i}" for i in range(len(non_empty)))
        return GenerationResult(
            bunches=bunch_ids,
            score=score,
            strategy=GenerationStrategy.BALANCED,
        )

    def _score_balance(
        self,
        loads: list[float],
        bunches: list[list[str]],
    ) -> float:
        """Score the balance quality of the distribution.

        评估分配的均衡质量分数。
        """
        if not bunches:
            return 0.0
        active_loads = [l for l, b in zip(loads, bunches, strict=False) if b]
        if not active_loads:
            return 0.0
        avg_load = sum(active_loads) / len(active_loads)
        if avg_load == 0.0:
            return 0.5
        deviations = [abs(l - avg_load) / avg_load for l in active_loads]
        avg_deviation = sum(deviations) / len(deviations)
        return max(0.0, 1.0 - avg_deviation)
