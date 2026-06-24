"""求解器抽象基类 / Solver abstract base class.

定义所有求解器的公共接口。
Defines the common interface for all solvers.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.solver.output.solver_output import (
        SolverOutput,
    )
    from ospf_python.core.solver.solve_options import SolveOptions


class Solver(abc.ABC):
    """求解器抽象基类 / Abstract base class for solvers.

    所有具体求解器必须实现名称属性和求解方法。
    All concrete solvers must implement the name property
    and the solve method.

    Attributes:
        name: 求解器名称 / The solver name.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """获取求解器名称 / Get the solver name."""
        ...

    @abc.abstractmethod
    def solve(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """求解模型 / Solve the model.

        对给定模型执行求解并返回结果。
        Executes the solver on the given model and returns
        the result.

        Args:
            model: 要求解的优化模型 / The optimization model
                to solve.
            options: 求解选项 / Solve options.

        Returns:
            求解输出结果 / The solver output.
        """
        ...
