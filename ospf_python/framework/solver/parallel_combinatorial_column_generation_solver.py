"""并行组合列生成求解器 / Parallel combinatorial column generation solver.

定义并行列生成求解的抽象接口。
Defines the abstract interface for parallel column generation solving.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from ospf_python.framework.solver.column_generation_solver import (
    ColumnGenerationSolver,
)

if TYPE_CHECKING:
    from ospf_python.framework.solver.parallel_combinatorial_mode import (
        ParallelCombinatorialMode,
    )


class ParallelCombinatorialColumnGenerationSolver(ColumnGenerationSolver, abc.ABC):
    """并行组合列生成求解器 / Parallel combinatorial CG solver.

    在列生成求解器基础上增加并行执行能力。
    Extends column generation solver with parallel execution.

    Attributes:
        mode: 并行模式 / The parallel mode.
    """

    @property
    @abc.abstractmethod
    def mode(self) -> ParallelCombinatorialMode:
        """获取并行模式 / Get parallel mode.

        Returns:
            当前并行模式 / The current parallel mode.
        """
        ...
