"""种群 / Population.

管理启发式算法中的个体集合。
Manages the collection of individuals in a heuristic
algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.solver.value.solve_value import (
        SolveValue,
    )


@dataclass
class Population:
    """种群 / Population.

    存储启发式算法中的个体集合及其适应度。
    Stores individuals and their fitness values in a
    heuristic algorithm.

    Attributes:
        individuals: 个体列表 / List of individuals.
        fitness: 适应度列表 / List of fitness values.
        best_index: 最优个体索引 / Best individual index.
    """

    individuals: list[SolveValue] = field(
        default_factory=list,
    )
    """个体列表 / List of individuals."""

    fitness: list[float] = field(
        default_factory=list,
    )
    """适应度列表 / List of fitness values."""

    best_index: int = -1
    """最优个体索引 / Best individual index."""

    @property
    def size(self) -> int:
        """种群大小 / Population size.

        Returns:
            个体数量 / Number of individuals.
        """
        return len(self.individuals)

    @property
    def best_fitness(self) -> float:
        """最优适应度 / Best fitness value.

        Returns:
            最优适应度值 / Best fitness value.
        """
        if not self.fitness:
            return float("inf")
        return self.fitness[self.best_index]

    @property
    def best_individual(self) -> SolveValue | None:
        """最优个体 / Best individual.

        Returns:
            最优个体或 None / Best individual or None.
        """
        if self.best_index < 0:
            return None
        return self.individuals[self.best_index]

    def update_best(self) -> None:
        """更新最优个体索引 / Update best individual index."""
        if not self.fitness:
            self.best_index = -1
            return
        self.best_index = min(
            range(len(self.fitness)),
            key=lambda i: self.fitness[i],
        )
