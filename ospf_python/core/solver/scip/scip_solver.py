"""SCIP 求解器基类 / SCIP solver base class.

封装 pyscipopt.Model，提供求解器基础设施。
Wraps pyscipopt.Model and provides solver infrastructure.
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
from ospf_python.core.solver.solver import Solver
from ospf_python.core.solver.solver_memory_cleanup_support import (
    SolverMemoryCleanupSupport,
)
from ospf_python.core.solver.solver_status_support import (
    SolverStatusSupport,
)

if TYPE_CHECKING:
    from pyscipopt import Model as ScipModel

    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class ScipSolver(
    Solver,
    SolverStatusSupport,
    SolverMemoryCleanupSupport,
):
    """SCIP 求解器基类 / SCIP solver base class.

    冻结数据类，封装 pyscipopt.Model 的创建和配置，
    提供状态查询和资源清理功能。
    Frozen dataclass wrapping pyscipopt.Model creation and
    configuration, providing status query and resource
    cleanup.

    Attributes:
        config: SCIP 求解器配置 / SCIP solver config.
        _model: 底层 SCIP 模型 / The underlying SCIP
            model.
        _cleaned: 是否已清理 / Whether already cleaned.
    """

    config: SCIPSolverConfig = field(
        default_factory=SCIPSolverConfig,
    )
    """SCIP 求解器配置 / SCIP solver config."""

    _model: ScipModel | None = field(
        default=None,
        repr=False,
    )
    """底层 SCIP 模型 / The underlying SCIP model."""

    _cleaned: bool = field(
        default=False,
        repr=False,
    )
    """是否已清理 / Whether already cleaned."""

    @property
    def name(self) -> str:
        """求解器名称 / Solver name.

        Returns:
            'scip' / 'scip'.
        """
        return "scip"

    def _get_or_create_model(self) -> ScipModel:
        """获取或创建 SCIP 模型 / Get or create the SCIP
        model.

        Returns:
            SCIP 模型实例 / The SCIP model instance.
        """
        from pyscipopt import Model

        if self._model is None:
            object.__setattr__(
                self,
                "_model",
                Model("ospf_scip"),
            )
        return self._model  # type: ignore[return-value]

    def _apply_config(
        self,
        model: ScipModel,
        *,
        options: SolveOptions | None = None,
    ) -> None:
        """应用配置到模型 / Apply configuration to model.

        Args:
            model: SCIP 模型 / The SCIP model.
            options: 可选的求解选项 / Optional solve
                options.
        """
        cfg = self.config

        if not cfg.verbose:
            model.hideOutput()

        model.setIntParam(
            "display/verblevel",
            5 if cfg.verbose else 0,
        )

        if cfg.time_limit < float("inf"):
            model.setRealParam(
                "limits/time",
                cfg.time_limit,
            )

        if options is not None:
            if options.time_limit < float("inf"):
                model.setRealParam(
                    "limits/time",
                    options.time_limit,
                )
            if options.verbose:
                model.showOutput()  # type: ignore[attr-defined]
                model.setIntParam(
                    "display/verblevel",
                    5,
                )
            model.setIntParam(
                "randomization/randomseedshift",
                options.seed,
            )

        model.setRealParam(
            "limits/gap",
            cfg.gap_tolerance,
        )

    def _map_scip_status(
        self,
        model: ScipModel,
    ) -> SolverStatus:
        """映射 SCIP 状态到 SolverStatus / Map SCIP
        status to SolverStatus.

        Args:
            model: 已求解的 SCIP 模型 / The solved SCIP
                model.

        Returns:
            求解器状态 / The solver status.
        """
        status = model.getStatus()
        if status == "optimal":
            return SolverStatus.OPTIMAL
        if status in ("infeasible", "infeasible or unbounded"):
            return SolverStatus.INFEASIBLE
        if status == "unbounded":
            return SolverStatus.UNBOUNDED
        if status in ("timelimit", "userinterrupt"):
            return SolverStatus.TIMEOUT
        return SolverStatus.ERROR

    def _build_output(
        self,
        model: ScipModel,
    ) -> SolverOutput:
        """从求解结果构建输出 / Build output from solve
        results.

        Args:
            model: 已求解的 SCIP 模型 / The solved SCIP
                model.

        Returns:
            求解器输出 / The solver output.
        """
        from ospf_python.core.solver.value.solve_value import (
            SolveValue,
        )

        status = self._map_scip_status(model)
        if status is not SolverStatus.OPTIMAL:
            return SolverOutput(status=status)

        values: dict[str, float] = {}
        for var in model.getVars():
            values[var.name] = model.getVal(var)

        obj_val = model.getObjVal()

        return SolverOutput(
            status=status,
            objective=obj_val,
            values=SolveValue(values=values),
        )

    def get_status(self) -> SolverStatus:
        """获取当前求解状态 / Get current solve status.

        Returns:
            求解器状态 / The solver status.
        """
        if self._model is None:
            return SolverStatus.UNKNOWN
        return self._map_scip_status(self._model)

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

        释放底层 SCIP 模型。
        Releases the underlying SCIP model.
        """
        if self._model is not None:
            self._model.freeProb()
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
            model: 要求解的优化模型 / The optimization
                model.
            options: 求解选项 / Solve options.

        Returns:
            求解输出结果 / The solver output.
        """
        return SolverOutput(
            status=SolverStatus.ERROR,
        )
