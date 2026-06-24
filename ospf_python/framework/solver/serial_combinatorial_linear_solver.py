"""串行组合线性求解器 / Serial combinatorial linear solver.

定义串行线性求解的抽象接口。
Defines the abstract interface for serial linear solving.
"""

from __future__ import annotations

import abc


class SerialCombinatorialLinearSolver(abc.ABC):
    """串行组合线性求解器 / Serial combinatorial linear solver.

    以串行方式求解线性规划问题。
    Solves linear programming problems in serial fashion.
    """

    @abc.abstractmethod
    def solve(self, problem: object) -> object:
        """求解问题 / Solve problem.

        Args:
            problem: 待求解问题 / The problem to solve.

        Returns:
            求解结果 / The solve result.
        """
        ...

    @abc.abstractmethod
    def is_feasible(self) -> bool:
        """是否可行 / Whether feasible.

        Returns:
            问题可行时返回 True / True when the problem is feasible.
        """
        ...
