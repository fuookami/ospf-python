"""求解器扩展方法 / Solver extension methods.

为求解器提供辅助扩展方法。
Provides helper extension methods for solvers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.solver.output.solver_output import (
        SolverOutput,
    )
    from ospf_python.core.solver.solve_options import SolveOptions
    from ospf_python.core.solver.solver import Solver


@dataclass(frozen=True)
class SolverExt:
    """求解器扩展方法容器 / Solver extension methods container.

    包装求解器实例并提供便捷方法。
    Wraps a solver instance and provides convenience methods.

    Attributes:
        solver: 被包装的求解器 / The wrapped solver.
    """

    solver: Solver
    """被包装的求解器 / The wrapped solver."""

    def solve_with_defaults(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """使用默认选项求解 / Solve with default options.

        如果未提供选项，则使用默认的 SolveOptions。
        Uses default SolveOptions when none are provided.

        Args:
            model: 优化模型 / The optimization model.
            options: 可选的求解选项 / Optional solve options.

        Returns:
            求解输出 / The solver output.
        """
        return self.solver.solve(model, options=options)

    @property
    def solver_name(self) -> str:
        """获取求解器名称 / Get the solver name.

        Returns:
            求解器名称 / The solver name.
        """
        return self.solver.name
