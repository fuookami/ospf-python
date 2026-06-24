"""串行组合列生成求解器 / Serial combinatorial column generation solver.

定义串行列生成求解的抽象接口。
Defines the abstract interface for serial column generation solving.
"""

from __future__ import annotations

import abc

from ospf_python.framework.solver.column_generation_solver import (
    ColumnGenerationSolver,
)


class SerialCombinatorialColumnGenerationSolver(ColumnGenerationSolver, abc.ABC):
    """串行组合列生成求解器 / Serial combinatorial CG solver.

    以串行方式执行列生成算法。
    Executes column generation algorithm in serial fashion.
    """

    @abc.abstractmethod
    def get_iteration_count(self) -> int:
        """获取迭代次数 / Get iteration count.

        Returns:
            当前已完成的迭代次数 / Current completed iteration count.
        """
        ...
