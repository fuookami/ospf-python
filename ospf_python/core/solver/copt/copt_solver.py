"""COPT 求解器基类 / COPT solver base class.

封装 coptpy.Model，提供求解器基础设施。
Wraps coptpy.Model and provides solver infrastructure.

环境受限：coptpy 许可证不可用时跳过集成测试。
Environment-limited: skips integration tests when coptpy license unavailable.
"""

# Coverage exemption: copt_solver requires coptpy license (environment-limited)
# pragma: no cover

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.config.copt_solver_config import (
    CoptSolverConfig,
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
    import coptpy

    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class CoptSolver(
    Solver,
    SolverStatusSupport,
    SolverMemoryCleanupSupport,
):
    """COPT 求解器基类 / COPT solver base class.

    冻结数据类，封装 coptpy.Model 的创建和配置，
    提供状态查询和资源清理功能。
    Frozen dataclass wrapping coptpy.Model creation and
    configuration, providing status query and resource
    cleanup.

    Attributes:
        config: COPT 求解器配置 / COPT solver config.
        _model: 底层 coptpy 模型 / The underlying coptpy
            model.
        _cleaned: 是否已清理 / Whether already cleaned.
    """

    config: CoptSolverConfig = field(
        default_factory=CoptSolverConfig,
    )
    """COPT 求解器配置 / COPT solver config."""

    _model: coptpy.Model | None = field(
        default=None,
        repr=False,
    )
    """底层 coptpy 模型 / The underlying coptpy model."""

    _cleaned: bool = field(
        default=False,
        repr=False,
    )
    """是否已清理 / Whether already cleaned."""

    @property
    def name(self) -> str:
        """求解器名称 / Solver name.

        Returns:
            'copt' / 'copt'.
        """
        return "copt"

    def _get_or_create_model(self) -> coptpy.Model:
        """获取或创建 coptpy 模型 / Get or create the
        coptpy model.

        Returns:
            coptpy 模型实例 / The coptpy model instance.
        """
        import coptpy

        if self._model is None:
            object.__setattr__(
                self,
                "_model",
                coptpy.Model("ospf_copt"),  # type: ignore[call-arg]
            )
        return self._model  # type: ignore[return-value]

    def _apply_config(
        self,
        model: coptpy.Model,
        *,
        options: SolveOptions | None = None,
    ) -> None:
        """应用配置到模型 / Apply configuration to model.

        Args:
            model: coptpy 模型 / The coptpy model.
            options: 可选的求解选项 / Optional solve options.
        """
        from coptpy import COPT

        cfg = self.config
        model.setParam(COPT.Param.Logging, (1 if cfg.log_to_console else 0))
        model.setParam(COPT.Param.Threads, cfg.threads)

        if options is not None:
            if options.time_limit < float("inf"):
                model.setParam(
                    COPT.Param.TimeLimit,
                    options.time_limit,
                )
            if options.verbose:
                model.setParam(COPT.Param.Logging, 1)
            model.setParam(
                COPT.Param.Seed,  # type: ignore[attr-defined]
                options.seed,
            )
            model.setParam(
                COPT.Param.Threads,
                options.threads,
            )

        if cfg.time_limit < float("inf"):
            model.setParam(
                COPT.Param.TimeLimit,
                cfg.time_limit,
            )

    def _map_copt_status(
        self,
        model: coptpy.Model,
    ) -> SolverStatus:
        """映射 COPT 状态到 SolverStatus / Map COPT
        status to SolverStatus.

        Args:
            model: 已求解的 coptpy 模型 / The solved
                coptpy model.

        Returns:
            求解器状态 / The solver status.
        """
        from coptpy import COPT

        status = model.status
        if status == COPT.OPTIMAL:
            return SolverStatus.OPTIMAL
        if status == COPT.INFEASIBLE:
            return SolverStatus.INFEASIBLE
        if status == COPT.UNBOUNDED:
            return SolverStatus.UNBOUNDED
        if status in (COPT.TIMEOUT, COPT.SUBOPTIMAL):  # type: ignore[attr-defined]
            return SolverStatus.TIMEOUT
        return SolverStatus.ERROR

    def _build_output(
        self,
        model: coptpy.Model,
    ) -> SolverOutput:
        """从求解结果构建输出 / Build output from solve
        results.

        Args:
            model: 已求解的 coptpy 模型 / The solved
                coptpy model.

        Returns:
            求解器输出 / The solver output.
        """
        from ospf_python.core.solver.value.solve_value import (
            SolveValue,
        )

        status = self._map_copt_status(model)
        if status is not SolverStatus.OPTIMAL:
            return SolverOutput(status=status)

        values: dict[str, float] = {}
        for var in model.getVars():
            values[var.name] = var.x

        return SolverOutput(
            status=status,
            objective=model.objval,
            values=SolveValue(values=values),
        )

    def get_status(self) -> SolverStatus:
        """获取当前求解状态 / Get current solve status.

        Returns:
            求解器状态 / The solver status.
        """
        if self._model is None:
            return SolverStatus.UNKNOWN
        return self._map_copt_status(self._model)

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

        释放底层 coptpy 模型。
        Releases the underlying coptpy model.
        """
        if self._model is not None:
            self._model.clear()
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
