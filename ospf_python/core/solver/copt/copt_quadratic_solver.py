"""COPT 二次求解器 / COPT quadratic solver.

基于 coptpy 的 QP/MIQP 求解器实现。
QP/MIQP solver implementation based on coptpy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.config.copt_solver_config import (
    CoptSolverConfig,
)
from ospf_python.core.solver.copt.copt_solver import (
    CoptSolver,
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

if TYPE_CHECKING:
    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class CoptQuadraticSolver(CoptSolver, QuadraticSolver):
    """COPT 二次求解器 / COPT quadratic solver.

    冻结数据类，实现 QuadraticSolver 接口，使用 coptpy
    求解 QP 和 MIQP 问题。
    Frozen dataclass implementing the QuadraticSolver
    interface, using coptpy to solve QP and MIQP problems.

    Attributes:
        config: COPT 求解器配置 / COPT solver config.
        _model: 底层 coptpy 模型 / Underlying model.
        _cleaned: 是否已清理 / Whether cleaned.
    """

    config: CoptSolverConfig = field(
        default_factory=CoptSolverConfig,
    )
    """COPT 求解器配置 / COPT solver config."""

    def supports_quadratic_objective(self) -> bool:
        """是否支持二次目标函数 / Whether quadratic
        objectives are supported.

        Returns:
            COPT 支持二次目标，返回 True / COPT
            supports quadratic objectives, returns True.
        """
        return True

    def supports_quadratic_constraint(self) -> bool:
        """是否支持二次约束 / Whether quadratic constraints
        are supported.

        Returns:
            COPT 支持二次约束，返回 True / COPT
            supports quadratic constraints, returns True.
        """
        return True

    def solve(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """求解二次模型 / Solve a quadratic model.

        使用 coptpy 求解 QP/MIQP 问题。
        Uses coptpy to solve QP/MIQP problems.

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
            m.solve()
            return self._build_output(m)

        except Exception:
            return SolverOutput(
                status=SolverStatus.ERROR,
            )
