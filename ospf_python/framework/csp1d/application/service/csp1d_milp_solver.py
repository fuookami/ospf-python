"""CSP1D MILP 求解器 / CSP1D MILP solver."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.csp1d.application.service.csp1d_final_milp_status import (
    Csp1dFinalMilpStatus,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.application.service.csp1d_milp import (
        Csp1dMilp,
    )


@dataclass(frozen=True)
class SolverResult:
    """求解器结果 / Solver result.

    Attributes:
        status: 求解状态 / Solving status.
        objective_value: 目标函数值 / Objective value.
        variable_values: 变量取值 / Variable values.
    """

    status: Csp1dFinalMilpStatus
    objective_value: float
    variable_values: tuple[tuple[str, float], ...]


class Csp1dMilpSolver:
    """MILP 求解器 / MILP solver.

    封装外部求解器调用，将 Csp1dMilp 模型提交给求解器
    并返回结构化的求解结果。
    Wraps external solver calls, submitting the Csp1dMilp
    model to a solver and returning structured results.

    Attributes:
        _solver_fn: 底层求解函数 / Underlying solver function.
    """

    def __init__(
        self,
        solver_fn: Callable[[Csp1dMilp], SolverResult],
    ) -> None:
        """初始化求解器 / Initialize solver.

        Args:
            solver_fn: 底层求解函数 / Underlying solver function.
        """
        self._solver_fn = solver_fn

    def solve(
        self,
        model: Csp1dMilp,
    ) -> Result[SolverResult, str, object]:
        """求解 MILP 模型 / Solve the MILP model.

        Args:
            model: 待求解的 MILP 模型 / MILP model to solve.

        Returns:
            求解结果 / Solver result.
        """
        result = self._solver_fn(model)
        if result.status == Csp1dFinalMilpStatus.INFEASIBLE:
            return Failed(
                ErrorCode.APPLICATION_ERROR,
                "MILP 模型不可行 / MILP model is infeasible",
            )
        return Ok(result)
