"""并行组合线性求解器 / Parallel combinatorial linear solver.

定义并行线性求解的抽象接口。
Defines the abstract interface for parallel linear solving.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.solver.parallel_combinatorial_mode import (
        ParallelCombinatorialMode,
    )


class ParallelCombinatorialLinearSolver(abc.ABC):
    """并行组合线性求解器 / Parallel combinatorial linear solver.

    支持并行求解多个线性规划子问题。
    Supports parallel solving of multiple LP sub problems.
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
