"""深度优先搜索算法 / Depth-first search algorithm.

使用深度优先搜索策略求解块装载问题。
Solves block loading problems using depth-first search strategy.
"""

from __future__ import annotations

import abc


class DepthFirstSearchAlgorithm(abc.ABC):
    """深度优先搜索算法 / Depth-first search algorithm.

    通过深度优先遍历搜索最优块装载方案。
    Searches for optimal block loading solutions via
    depth-first traversal.
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
            最优装载方案 / The optimal loading solution.
        """
        ...

    @abc.abstractmethod
    def prune(self, state: object) -> bool:
        """剪枝判断 / Pruning decision.

        Args:
            state: 当前搜索状态 / Current search state.

        Returns:
            应剪枝返回 True / True if should prune.
        """
        ...
