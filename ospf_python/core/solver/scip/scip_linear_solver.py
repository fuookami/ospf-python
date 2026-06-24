"""SCIP 线性求解器 / SCIP linear solver.

基于 pyscipopt 的 LP/MILP 求解器实现。
LP/MILP solver implementation based on pyscipopt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.config.scip_solver_config import (
    SCIPSolverConfig,
)
from ospf_python.core.solver.linear_solver import (
    LinearSolver,
)
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.scip.scip_solver import (
    ScipSolver,
)

if TYPE_CHECKING:
    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class ScipLinearSolver(ScipSolver, LinearSolver):
    """SCIP 线性求解器 / SCIP linear solver.

    冻结数据类，实现 LinearSolver 接口，使用 pyscipopt
    求解 LP 和 MILP 问题。
    Frozen dataclass implementing the LinearSolver interface,
    using pyscipopt to solve LP and MILP problems.

    Attributes:
        config: SCIP 求解器配置 / SCIP solver config.
        _model: 底层 SCIP 模型 / Underlying model.
        _cleaned: 是否已清理 / Whether cleaned.
        _supports_int: 是否支持整数 / Whether integer
            variables are supported.
    """

    config: SCIPSolverConfig = field(
        default_factory=SCIPSolverConfig,
    )
    """SCIP 求解器配置 / SCIP solver config."""

    _supports_int: bool = field(
        default=True,
        repr=False,
    )
    """是否支持整数变量 / Whether integer variables are
    supported."""

    def supports_integer(self) -> bool:
        """是否支持整数变量 / Whether integer variables
        are supported.

        Returns:
            支持整数变量时返回 True / True when integer
            variables are supported.
        """
        return self._supports_int

    def solve(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """求解线性模型 / Solve a linear model.

        使用 pyscipopt 求解 LP/MILP 问题。
        Uses pyscipopt to solve LP/MILP problems.

        Args:
            model: 要求解的优化模型 / The optimization
                model.
            options: 求解选项 / Solve options.

        Returns:
            求解输出结果 / The solver output.
        """
        try:
            m = self._get_or_create_model()
            self._apply_config(m, options=options)

            if hasattr(model, "objective_sense"):
                if model.objective_sense == "min":
                    m.setMinimize()
                else:
                    m.setMaximize()

            m.optimize()
            return self._build_output(m)

        except Exception:
            return SolverOutput(
                status=SolverStatus.ERROR,
            )
