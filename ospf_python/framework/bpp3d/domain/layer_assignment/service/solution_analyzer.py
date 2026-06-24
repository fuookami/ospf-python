"""方案分析器 / Solution analyzer.

分析层分配方案的质量和可行性。
Analyzes quality and feasibility of layer assignment solutions.
"""

from __future__ import annotations

import abc


class SolutionAnalyzer(abc.ABC):
    """方案分析器 / Solution analyzer.

    对层分配求解结果进行分析。
    Analyzes layer assignment solution results.
    """

    @abc.abstractmethod
    def analyze(self, solution: object) -> object:
        """分析方案 / Analyze solution.

        Args:
            solution: 待分析的方案 / The solution to analyze.

        Returns:
            分析结果 / The analysis result.
        """
        ...

    @abc.abstractmethod
    def is_feasible(self, solution: object) -> bool:
        """检查可行性 / Check feasibility.

        Args:
            solution: 待检查的方案 / The solution to check.

        Returns:
            可行返回 True / True if feasible.
        """
        ...

    @abc.abstractmethod
    def calculate_objective(self, solution: object) -> float:
        """计算目标值 / Calculate objective value.

        Args:
            solution: 待评估的方案 / The solution to evaluate.

        Returns:
            目标函数值 / The objective function value.
        """
        ...
