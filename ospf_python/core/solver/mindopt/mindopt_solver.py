"""MindOPT 求解器基类 / MindOPT solver base class.

封装 mindoptpy.Model，提供求解器基础设施。
Wraps mindoptpy.Model and provides solver infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.config.mindopt_solver_config import (
    MindOPTSolverConfig,
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
    import mindoptpy

    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class MindOPTSolver(
    Solver,
    SolverStatusSupport,
    SolverMemoryCleanupSupport,
):
    """MindOPT 求解器基类 / MindOPT solver base class.

    冻结数据类，封装 mindoptpy.Model 的创建和配置，
    提供状态查询和资源清理功能。
    Frozen dataclass wrapping mindoptpy.Model creation and
    configuration, providing status query and resource
    cleanup.

    Attributes:
        config: MindOPT 求解器配置 / MindOPT solver config.
        _model: 底层 mindoptpy 模型 / The underlying
            mindoptpy model.
        _cleaned: 是否已清理 / Whether already cleaned.
    """

    config: MindOPTSolverConfig = field(
        default_factory=MindOPTSolverConfig,
    )
    """MindOPT 求解器配置 / MindOPT solver config."""

    _model: mindoptpy.Model | None = field(
        default=None,
        repr=False,
    )
    """底层 mindoptpy 模型 / The underlying mindoptpy
    model."""

    _cleaned: bool = field(
        default=False,
        repr=False,
    )
    """是否已清理 / Whether already cleaned."""

    @property
    def name(self) -> str:
        """求解器名称 / Solver name.

        Returns:
            'mindopt' / 'mindopt'.
        """
        return "mindopt"

    def _get_or_create_model(self) -> mindoptpy.Model:
        """获取或创建 mindoptpy 模型 / Get or create the
        mindoptpy model.

        Returns:
            mindoptpy 模型实例 / The mindoptpy model
            instance.
        """
        import mindoptpy

        if self._model is None:
            object.__setattr__(
                self,
                "_model",
                mindoptpy.Model(
                    "ospf_mindopt",
                ),
            )
        return self._model  # type: ignore[return-value]

    def _apply_config(
        self,
        model: mindoptpy.Model,
        *,
        options: SolveOptions | None = None,
    ) -> None:
        """应用配置到模型 / Apply configuration to model.

        Args:
            model: mindoptpy 模型 / The mindoptpy model.
            options: 可选的求解选项 / Optional solve
                options.
        """
        cfg = self.config
        model.setParam(
            "MindOpt.Logging",
            (1 if cfg.log_to_console else 0),
        )
        model.setParam(
            "MindOpt.Threads",
            cfg.threads,
        )

        if options is not None:
            if options.time_limit < float("inf"):
                model.setParam(
                    "MindOpt.TimeLimit",
                    options.time_limit,
                )
            if options.verbose:
                model.setParam("MindOpt.Logging", 1)
            model.setParam(
                "MindOpt.Seed",
                options.seed,
            )
            model.setParam(
                "MindOpt.Threads",
                options.threads,
            )

        if cfg.time_limit < float("inf"):
            model.setParam(
                "MindOpt.TimeLimit",
                cfg.time_limit,
            )

    def _map_mindopt_status(
        self,
        model: mindoptpy.Model,
    ) -> SolverStatus:
        """映射 MindOPT 状态到 SolverStatus / Map
        MindOPT status to SolverStatus.

        Args:
            model: 已求解的 mindoptpy 模型 / The solved
                mindoptpy model.

        Returns:
            求解器状态 / The solver status.
        """
        from mindoptpy import MindOptStatus

        status = model.status
        if status == MindOptStatus.kOptimal:
            return SolverStatus.OPTIMAL
        if status == MindOptStatus.kInfeasible:
            return SolverStatus.INFEASIBLE
        if status == MindOptStatus.kUnbounded:
            return SolverStatus.UNBOUNDED
        if status in (
            MindOptStatus.kTimeout,
            MindOptStatus.kSubOptimal,
        ):
            return SolverStatus.TIMEOUT
        return SolverStatus.ERROR

    def _build_output(
        self,
        model: mindoptpy.Model,
    ) -> SolverOutput:
        """从求解结果构建输出 / Build output from solve
        results.

        Args:
            model: 已求解的 mindoptpy 模型 / The solved
                mindoptpy model.

        Returns:
            求解器输出 / The solver output.
        """
        from ospf_python.core.solver.value.solve_value import (
            SolveValue,
        )

        status = self._map_mindopt_status(model)
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
        return self._map_mindopt_status(self._model)

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

        释放底层 mindoptpy 模型。
        Releases the underlying mindoptpy model.
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
            model: 要求解的优化模型 / The optimization
                model.
            options: 求解选项 / Solve options.

        Returns:
            求解输出结果 / The solver output.
        """
        return SolverOutput(
            status=SolverStatus.ERROR,
        )
