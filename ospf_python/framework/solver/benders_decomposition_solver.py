"""Benders 分解求解器 / Benders decomposition solver.

定义 Benders 分解求解器的抽象接口。
Defines the abstract interface for Benders decomposition solvers.
"""

from __future__ import annotations

import abc


class BendersDecompositionSolver(abc.ABC):
    """Benders 分解求解器 / Benders decomposition solver.

    实现 Benders 分解算法的求解器必须实现此接口。
    Solvers implementing Benders decomposition algorithms
    must implement this interface.
    """

    @abc.abstractmethod
    def initialize(self) -> None:
        """初始化求解器 / Initialize solver.

        准备主问题和子问题的初始状态。
        Prepares the initial state of master and sub problems.
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
    def solve_sub_problem(self) -> bool:
        """求解子问题 / Solve sub problem.

        Returns:
            求解成功返回 True / True if solving succeeded.
        """
        ...

    @abc.abstractmethod
    def add_cut(self) -> bool:
        """添加割平面 / Add cut.

        根据子问题结果向主问题添加割平面。
        Adds a cut to the master problem based on sub problem results.

        Returns:
            添加成功返回 True / True if cut was added.
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

        释放求解器占用的资源。
        Releases resources held by the solver.
        """
        ...
