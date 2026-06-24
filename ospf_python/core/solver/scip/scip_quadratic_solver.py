"""SCIP 二次求解器 / SCIP quadratic solver.

基于 pyscipopt 的 QP/MIQP 求解器实现。
QP/MIQP solver implementation based on pyscipopt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.config.scip_solver_config import (
    SCIPSolverConfig,
)
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.quadratic_solver import (
    QuadraticSolver,
)
from ospf_python.core.solver.scip.scip_solver import (
    ScipSolver,
)

if TYPE_CHECKING:
    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class ScipQuadraticSolver(ScipSolver, QuadraticSolver):
    """SCIP 二次求解器 / SCIP quadratic solver.

    冻结数据类，实现 QuadraticSolver 接口，使用 pyscipopt
    求解 QP 和 MIQP 问题。
    Frozen dataclass implementing the QuadraticSolver
    interface, using pyscipopt to solve QP and MIQP
    problems.

    Attributes:
        config: SCIP 求解器配置 / SCIP solver config.
        _model: 底层 SCIP 模型 / Underlying model.
        _cleaned: 是否已清理 / Whether cleaned.
    """

    config: SCIPSolverConfig = field(
        default_factory=SCIPSolverConfig,
    )
    """SCIP 求解器配置 / SCIP solver config."""

    def supports_quadratic_objective(self) -> bool:
        """是否支持二次目标函数 / Whether quadratic
        objectives are supported.

        Returns:
            SCIP 支持二次目标，返回 True / SCIP supports
            quadratic objectives, returns True.
        """
        return True

    def supports_quadratic_constraint(self) -> bool:
        """是否支持二次约束 / Whether quadratic constraints
        are supported.

        Returns:
            SCIP 支持二次约束，返回 True / SCIP supports
            quadratic constraints, returns True.
        """
        return True

    def solve(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """求解二次模型 / Solve a quadratic model.

        使用 pyscipopt 求解 QP/MIQP 问题。
        Uses pyscipopt to solve QP/MIQP problems.

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
            m.optimize()
            return self._build_output(m)

        except Exception:
            return SolverOutput(
                status=SolverStatus.ERROR,
            )
