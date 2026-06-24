"""并行组合二次求解器 / Parallel combinatorial quadratic solver.

定义并行二次规划求解的抽象接口。
Defines the abstract interface for parallel quadratic solving.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.solver.parallel_combinatorial_mode import (
        ParallelCombinatorialMode,
    )


class ParallelCombinatorialQuadraticSolver(abc.ABC):
    """并行组合二次求解器 / Parallel combinatorial quadratic solver.

    支持并行求解多个二次规划子问题。
    Supports parallel solving of multiple QP sub problems.
    """

    @property
    @abc.abstractmethod
    def mode(self) -> ParallelCombinatorialMode:
        """获取并行模式 / Get parallel mode.

        Returns:
            当前并行模式 / The current parallel mode.
        """
        ...

    @abc.abstractmethod
    def solve_parallel(self, problems: list[object]) -> list[object]:
        """并行求解 / Solve in parallel.

        Args:
            problems: 待求解问题列表 / List of problems to solve.

        Returns:
            求解结果列表 / List of solve results.
        """
        ...
