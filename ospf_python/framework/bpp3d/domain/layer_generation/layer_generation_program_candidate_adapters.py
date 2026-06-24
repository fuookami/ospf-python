"""层生成候选适配器 / Layer generation candidate adapters.

适配层生成程序的候选层数据。
Adapts candidate layer data for layer generation programs.
"""

from __future__ import annotations

import abc


class LayerGenerationProgramCandidateAdapter(abc.ABC):
    """层生成候选适配器 / Layer generation candidate adapter.

    将候选层数据适配为程序可用格式。
    Adapts candidate layer data into program-usable format.
    """

    @abc.abstractmethod
    def adapt_candidate(self, candidate: object) -> object:
        """适配候选层 / Adapt candidate layer.

        Args:
            candidate: 原始候选层 / The raw candidate layer.

        Returns:
            适配后的候选层 / The adapted candidate layer.
        """
        ...

    @abc.abstractmethod
    def filter_candidates(
        self,
        candidates: tuple[object, ...],
    ) -> tuple[object, ...]:
        """过滤候选层 / Filter candidate layers.

        Args:
            candidates: 候选层列表 / The candidate layers.

        Returns:
            过滤后的候选层 / Filtered candidate layers.
        """
        ...

    @abc.abstractmethod
    def rank_candidates(
        self,
        candidates: tuple[object, ...],
    ) -> tuple[object, ...]:
        """排序候选层 / Rank candidate layers.

        Args:
            candidates: 候选层列表 / The candidate layers.

        Returns:
            排序后的候选层 / Ranked candidate layers.
        """
        ...
