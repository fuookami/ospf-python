"""MindOPT 线性求解器 / MindOPT linear solver.

基于 mindoptpy 的 LP/MILP 求解器实现。
LP/MILP solver implementation based on mindoptpy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.config.mindopt_solver_config import (
    MindOPTSolverConfig,
)
from ospf_python.core.solver.linear_solver import (
    LinearSolver,
)
from ospf_python.core.solver.mindopt.mindopt_solver import (
    MindOPTSolver,
)
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)

if TYPE_CHECKING:
    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class MindOPTLinearSolver(
    MindOPTSolver,
    LinearSolver,
):
    """MindOPT 线性求解器 / MindOPT linear solver.

    冻结数据类，实现 LinearSolver 接口，使用 mindoptpy
    求解 LP 和 MILP 问题。
    Frozen dataclass implementing the LinearSolver interface,
    using mindoptpy to solve LP and MILP problems.

    Attributes:
        config: MindOPT 求解器配置 / MindOPT solver config.
        _model: 底层 mindoptpy 模型 / Underlying model.
        _cleaned: 是否已清理 / Whether cleaned.
        _supports_int: 是否支持整数 / Whether integer
            variables are supported.
    """

    config: MindOPTSolverConfig = field(
        default_factory=MindOPTSolverConfig,
    )
    """MindOPT 求解器配置 / MindOPT solver config."""

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

        使用 mindoptpy 求解 LP/MILP 问题。
        Uses mindoptpy to solve LP/MILP problems.

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

            if hasattr(model, "objective_sense") and model.objective_sense == "min":
                m.setObjective(
                    m.getObjective(),
                    sense=-1,
                )

            m.optimize()
            return self._build_output(m)

        except Exception:
            return SolverOutput(
                status=SolverStatus.ERROR,
            )
