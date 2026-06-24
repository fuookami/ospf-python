"""列生成算法 / Column generation algorithm.

定义列生成算法的生命周期接口。
Defines the lifecycle interface for column generation algorithms.
"""

from __future__ import annotations

import abc


class ColumnGenerationAlgorithm(abc.ABC):
    """列生成算法 / Column generation algorithm.

    实现列生成算法的求解器必须实现此生命周期接口。
    Solvers implementing column generation must implement this
    lifecycle interface.
    """

    @abc.abstractmethod
    def initialize(self) -> None:
        """初始化算法 / Initialize algorithm.

        准备主问题和定价问题的初始状态。
        Prepares the initial state of master and pricing problems.
        """
        ...

    @abc.abstractmethod
    def solve_master_problem(self) -> bool:
        """求解主问题 / Solve master problem.

        Returns:
            求解成功返回 True / True if solving succeeded.
        """
        ...

    @abc.abstractmethod
    def solve_pricing_problem(self) -> bool:
        """求解定价问题 / Solve pricing problem.

        Returns:
            求解成功返回 True / True if solving succeeded.
        """
        ...

    @abc.abstractmethod
    def add_columns(self) -> bool:
        """添加列 / Add columns.

        根据定价问题结果向主问题添加新列。
        Adds new columns to the master problem based on
        pricing problem results.

        Returns:
            添加成功返回 True / True if columns were added.
        """
        ...

    @abc.abstractmethod
    def is_optimal(self) -> bool:
        """是否已最优 / Whether optimal.

        Returns:
            已达到最优时返回 True / True when optimality reached.
        """
        ...

    @abc.abstractmethod
    def cleanup(self) -> None:
        """清理资源 / Cleanup resources.

        释放算法占用的资源。
        Releases resources held by the algorithm.
        """
        ...
