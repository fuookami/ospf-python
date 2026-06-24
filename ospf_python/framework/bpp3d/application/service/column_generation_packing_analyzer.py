"""列生成装箱分析器 / Column generation packing analyzer.

分析列生成过程中的装箱结果。
Analyzes packing results during column generation.
"""

from __future__ import annotations

import abc


class ColumnGenerationPackingAnalyzer(abc.ABC):
    """列生成装箱分析器 / Column generation packing analyzer.

    对列生成求解结果进行装箱质量分析。
    Performs packing quality analysis on column generation
    solution results.
    """

    @abc.abstractmethod
    def analyze(self, solution: object) -> object:
        """分析装箱方案 / Analyze packing solution.

        Args:
            solution: 待分析的装箱方案 / The packing solution
                to analyze.

        Returns:
            分析结果 / The analysis result.
        """
        ...

    @abc.abstractmethod
    def calculate_loading_rate(self, solution: object) -> float:
        """计算装载率 / Calculate loading rate.

        Args:
            solution: 装箱方案 / The packing solution.

        Returns:
            装载率（0.0-1.0） / Loading rate (0.0-1.0).
        """
        ...
