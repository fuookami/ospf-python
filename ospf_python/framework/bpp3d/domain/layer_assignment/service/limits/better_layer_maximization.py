"""更好层最大化 / Better layer maximization.

最大化使用更优层的数量。
Maximizes the quantity of better layers used.
"""

from __future__ import annotations

import abc


class BetterLayerMaximization(abc.ABC):
    """更好层最大化 / Better layer maximization.

    优先选择更优的层以提高装载效率。
    Prioritizes better layers to improve loading efficiency.
    """

    @abc.abstractmethod
    def evaluate(self, layers: tuple[object, ...]) -> float:
        """评估层质量 / Evaluate layer quality.

        Args:
            layers: 待评估的层 / Layers to evaluate.

        Returns:
            层质量评分 / The layer quality score.
        """
        ...

    @abc.abstractmethod
    def select_better(
        self,
        candidates: tuple[object, ...],
    ) -> object | None:
        """选择更优层 / Select better layer.

        Args:
            candidates: 候选层 / Candidate layers.

        Returns:
            更优层或 None / Better layer or None.
        """
        ...
