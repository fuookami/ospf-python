"""装箱方案类适配器 / Package solution-like adapter.

适配不同格式的装箱方案。
Adapts packing solutions of different formats.
"""

from __future__ import annotations

import abc


class PackageSolutionLikeAdapter(abc.ABC):
    """装箱方案类适配器 / Package solution-like adapter.

    将外部装箱方案适配为统一接口。
    Adapts external packing solutions into a unified interface.
    """

    @abc.abstractmethod
    def adapt(self, raw_solution: object) -> object:
        """适配方案 / Adapt solution.

        Args:
            raw_solution: 原始方案 / The raw solution.

        Returns:
            适配后的方案 / The adapted solution.
        """
        ...

    @abc.abstractmethod
    def supports(self, raw_solution: object) -> bool:
        """检查支持 / Check support.

        Args:
            raw_solution: 待检查方案 / The solution to check.

        Returns:
            支持该格式返回 True / True if format supported.
        """
        ...
