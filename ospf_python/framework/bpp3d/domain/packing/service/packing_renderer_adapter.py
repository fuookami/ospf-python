"""装箱渲染适配器 / Packing renderer adapter.

适配装箱方案的可视化渲染。
Adapts visualization rendering of packing solutions.
"""

from __future__ import annotations

import abc


class PackingRendererAdapter(abc.ABC):
    """装箱渲染适配器 / Packing renderer adapter.

    将装箱方案适配为可视化渲染格式。
    Adapts packing solutions into visualization rendering format.
    """

    @abc.abstractmethod
    def render(self, solution: object) -> object:
        """渲染方案 / Render solution.

        Args:
            solution: 装箱方案 / The packing solution.

        Returns:
            渲染结果 / The rendering result.
        """
        ...

    @abc.abstractmethod
    def export(
        self,
        solution: object,
        format_: str,
    ) -> bytes:
        """导出方案 / Export solution.

        Args:
            solution: 装箱方案 / The packing solution.
            format_: 导出格式 / The export format.

        Returns:
            导出数据 / The exported data.
        """
        ...
