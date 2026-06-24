"""自底向上左对齐算法 / Bottom-up left-justified algorithm.

实现二维装箱的自底向上左对齐启发式。
Implements the bottom-up left-justified heuristic for
two-dimensional bin packing.
"""

from __future__ import annotations

import abc


class BottomUpLeftJustifiedAlgorithm(abc.ABC):
    """自底向上左对齐算法 / Bottom-up left-justified algorithm.

    按自底向上、左对齐的策略放置物品。
    Places items using a bottom-up, left-justified strategy.
    """

    @abc.abstractmethod
    def pack(self, items: tuple[object, ...]) -> object:
        """执行装箱 / Execute packing.

        Args:
            items: 待装箱物品 / Items to pack.

        Returns:
            装箱方案 / The packing solution.
        """
        ...

    @abc.abstractmethod
    def reset(self) -> None:
        """重置状态 / Reset state.

        将算法恢复到初始状态。
        Resets the algorithm to its initial state.
        """
        ...
