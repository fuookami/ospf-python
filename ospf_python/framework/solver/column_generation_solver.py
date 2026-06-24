"""列生成求解器 / Column generation solver.

定义列生成求解器的抽象接口。
Defines the abstract interface for column generation solvers.
"""

from __future__ import annotations

import abc


class ColumnGenerationSolver(abc.ABC):
    """列生成求解器 / Column generation solver.

    实现列生成算法的求解器必须实现此接口。
    Solvers implementing column generation algorithms
    must implement this interface.
    """

    @abc.abstractmethod
    def initialize(self) -> None:
        """初始化求解器 / Initialize solver.

        准备求解器的初始状态。
        Prepares the initial state of the solver.
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
