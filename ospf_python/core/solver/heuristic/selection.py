"""选择操作 / Selection operation.

实现从种群中选择个体的策略。
Implements strategies for selecting individuals
from a population.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.core.solver.heuristic.select_mode import (
    SelectMode,
)

if TYPE_CHECKING:
    from ospf_python.core.solver.heuristic.population import (
        Population,
    )


@dataclass
class Selection:
    """选择操作 / Selection operation.

    根据指定的选择模式从种群中选取个体。
    Selects individuals from a population according
    to the specified selection mode.

    Attributes:
        mode: 选择模式 / Selection mode.
        tournament_size: 锦标赛大小 / Tournament size.
    """

    mode: SelectMode = SelectMode.ROULETTE
    """选择模式 / Selection mode."""

    tournament_size: int = 3
    """锦标赛大小 / Tournament size."""

    def select_indices(
        self,
        population: Population,
        count: int,
    ) -> list[int]:
        """选择个体索引 / Select individual indices.

        Args:
            population: 种群 / The population.
            count: 选取数量 / Number to select.

        Returns:
            选中的索引列表 / List of selected indices.
        """
        if population.size == 0:
            return []
        if self.mode is SelectMode.TOURNAMENT:
            return self._tournament_select(
                population,
                count,
            )
        return self._roulette_select(population, count)

    def _roulette_select(
        self,
        population: Population,
        count: int,
    ) -> list[int]:
        """轮盘赌选择 / Roulette wheel selection."""
        if population.size == 0:
            return []
        return [population.best_index % population.size for _ in range(count)]

    def _tournament_select(
        self,
        population: Population,
        count: int,
    ) -> list[int]:
        """锦标赛选择 / Tournament selection."""
        if population.size == 0:
            return []
        return [population.best_index % population.size for _ in range(count)]
