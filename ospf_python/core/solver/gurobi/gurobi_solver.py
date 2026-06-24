"""Gurobi 求解器基类 / Gurobi solver base class.

封装 gurobipy.Model，提供求解器基础设施。
Wraps gurobipy.Model and provides solver infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.config.gurobi_solver_config import (
    GurobiSolverConfig,
)
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.solver import Solver
from ospf_python.core.solver.solver_memory_cleanup_support import (
    SolverMemoryCleanupSupport,
)
from ospf_python.core.solver.solver_status_support import (
    SolverStatusSupport,
)

if TYPE_CHECKING:
    import gurobipy as gp

    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class GurobiSolver(
    Solver,
    SolverStatusSupport,
    SolverMemoryCleanupSupport,
):
    """Gurobi 求解器基类 / Gurobi solver base class.

    冻结数据类，封装 gurobipy.Model 的创建和配置，
    提供状态查询和资源清理功能。
    Frozen dataclass wrapping gurobipy.Model creation and
    configuration, providing status query and resource
    cleanup.

    Attributes:
        config: Gurobi 求解器配置 / Gurobi solver config.
        _model: 底层 gurobipy 模型 / The underlying
            gurobipy model.
        _cleaned: 是否已清理 / Whether already cleaned.
    """

    config: GurobiSolverConfig = field(
        default_factory=GurobiSolverConfig,
    )
    """Gurobi 求解器配置 / Gurobi solver config."""

    _model: gp.Model | None = field(
        default=None,
        repr=False,
    )
    """底层 gurobipy 模型 / The underlying gurobipy model."""

    _cleaned: bool = field(
        default=False,
        repr=False,
    )
    """是否已清理 / Whether already cleaned."""

    @property
    def name(self) -> str:
        """求解器名称 / Solver name.

        Returns:
            'gurobi' / 'gurobi'.
        """
        return "gurobi"

    def _get_or_create_model(self) -> gp.Model:
        """获取或创建 gurobipy 模型 / Get or create the
        gurobipy model.

        Returns:
            gurobipy 模型实例 / The gurobipy model instance.
        """
        import gurobipy as gp

        if self._model is None:
            object.__setattr__(
                self,
                "_model",
                gp.Model("ospf_gurobi"),
            )
        return self._model  # type: ignore[return-value]

    def _apply_config(
        self,
        model: gp.Model,
        *,
        options: SolveOptions | None = None,
    ) -> None:
        """应用配置到模型 / Apply configuration to model.

        Args:
            model: gurobipy 模型 / The gurobipy model.
            options: 可选的求解选项 / Optional solve options.
        """
        cfg = self.config
        model.Params.OutputFlag = 1 if cfg.log_to_console else 0
        model.Params.Threads = cfg.threads
        model.Params.MIPGap = cfg.mip_gap

        if options is not None:
            if options.time_limit < float("inf"):
                model.Params.TimeLimit = options.time_limit
            if options.verbose:
                model.Params.OutputFlag = 1
            model.Params.Seed = options.seed
            model.Params.Threads = options.threads

        if cfg.time_limit < float("inf"):
            model.Params.TimeLimit = cfg.time_limit

    def _map_gurobi_status(
        self,
        model: gp.Model,
    ) -> SolverStatus:
        """映射 Gurobi 状态到 SolverStatus / Map Gurobi
        status to SolverStatus.

        Args:
            model: 已求解的 gurobipy 模型 / The solved
                gurobipy model.

        Returns:
            求解器状态 / The solver status.
        """
        from gurobipy import GRB

        status = model.Status
        if status == GRB.OPTIMAL:
            return SolverStatus.OPTIMAL
        if status == GRB.INFEASIBLE:
            return SolverStatus.INFEASIBLE
        if status == GRB.UNBOUNDED:
            return SolverStatus.UNBOUNDED
        if status in (
            GRB.TIME_LIMIT,
            GRB.SUBOPTIMAL,
        ):
            return SolverStatus.TIMEOUT
        return SolverStatus.ERROR

    def _build_output(
        self,
        model: gp.Model,
    ) -> SolverOutput:
        """从求解结果构建输出 / Build output from solve
        results.

        Args:
            model: 已求解的 gurobipy 模型 / The solved
                gurobipy model.

        Returns:
            求解器输出 / The solver output.
        """
        from ospf_python.core.solver.value.solve_value import (
            SolveValue,
        )

        status = self._map_gurobi_status(model)
        if status is not SolverStatus.OPTIMAL:
            return SolverOutput(status=status)

        values: dict[str, float] = {}
        for var in model.getVars():
            values[var.VarName] = var.X

        return SolverOutput(
            status=status,
            objective=model.ObjVal,
            values=SolveValue(values=values),
        )

    def get_status(self) -> SolverStatus:
        """获取当前求解状态 / Get current solve status.

        Returns:
            求解器状态 / The solver status.
        """
        if self._model is None:
            return SolverStatus.UNKNOWN
        return self._map_gurobi_status(self._model)

    def is_terminated(self) -> bool:
        """检查是否已终止 / Check whether terminated.

        Returns:
            已终止返回 True / True when terminated.
        """
        return self._cleaned

    def is_feasible(self) -> bool:
        """检查当前解是否可行 / Check whether current
        solution is feasible.

        Returns:
            可行返回 True / True when feasible.
        """
        status = self.get_status()
        return status is SolverStatus.OPTIMAL

    def cleanup(self) -> None:
        """清理求解器资源 / Clean up solver resources.

        释放底层 gurobipy 模型。
        Releases the underlying gurobipy model.
        """
        if self._model is not None:
            self._model.dispose()
            object.__setattr__(self, "_model", None)
        object.__setattr__(self, "_cleaned", True)

    def is_cleaned_up(self) -> bool:
        """检查是否已清理 / Check whether already cleaned
        up.

        Returns:
            已清理返回 True / True when already cleaned up.
        """
        return self._cleaned

    def solve(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """求解模型 / Solve the model.

        子类应重写此方法以处理具体模型类型。
        Subclasses should override this method to handle
        specific model types.

        Args:
            model: 要求解的优化模型 / The optimization model.
            options: 求解选项 / Solve options.

        Returns:
            求解输出结果 / The solver output.
        """
        return SolverOutput(
            status=SolverStatus.ERROR,
        )
