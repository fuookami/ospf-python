"""多层启发式搜索算法 / Multi-layer heuristic search algorithm.

使用多层启发式策略搜索块装载方案。
Searches for block loading solutions using multi-layer
heuristic strategy.
"""

from __future__ import annotations

import abc


class MultiLayerHeuristicSearchAlgorithm(abc.ABC):
    """多层启发式搜索算法 / Multi-layer heuristic search algorithm.

    在多个层面上应用启发式规则搜索装载方案。
    Applies heuristic rules at multiple levels to search for
    loading solutions.
    """

    @abc.abstractmethod
    def search(
        self,
        blocks: tuple[object, ...],
        container: object,
    ) -> object:
        """执行搜索 / Execute search.

        Args:
            blocks: 待装载块 / Blocks to load.
            container: 目标容器 / The target container.

        Returns:
            装载方案 / The loading solution.
        """
        ...

    @abc.abstractmethod
    def evaluate(self, solution: object) -> float:
        """评估方案 / Evaluate solution.

        Args:
            solution: 装载方案 / The loading solution.

        Returns:
            方案评分 / The solution score.
        """
        ...
