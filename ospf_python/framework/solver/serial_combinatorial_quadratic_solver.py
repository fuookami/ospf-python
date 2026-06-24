"""串行组合二次求解器 / Serial combinatorial quadratic solver.

定义串行二次规划求解的抽象接口。
Defines the abstract interface for serial quadratic solving.
"""

from __future__ import annotations

import abc


class SerialCombinatorialQuadraticSolver(abc.ABC):
    """串行组合二次求解器 / Serial combinatorial quadratic solver.

    以串行方式求解二次规划问题。
    Solves quadratic programming problems in serial fashion.
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
