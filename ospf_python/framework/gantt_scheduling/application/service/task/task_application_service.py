"""甘特调度任务应用服务 / Gantt scheduling task application service.

实现 BranchAndPrice 列生成编排，管理完整的列生成生命周期：
注册 -> 增列 -> 删列 -> 刷新影子价格 -> 终止 -> 提取解。
Implements BranchAndPrice column generation orchestration,
managing the full column generation lifecycle: register ->
add_columns -> remove_columns -> refresh_shadow_price ->
finalize -> extract_solution.
"""

from __future__ import annotations

import math
import time
from fractions import Fraction
from typing import TYPE_CHECKING, TypeVar

from ospf_python._binding.control import CancellationScope
from ospf_python._binding.gantt_task import (
    improving_columns as _native_improving_columns,
)
from ospf_python._binding.gantt_task import solve_task_columns as _solve_task_columns
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import (
    BindingResult,
    FailureContext,
    invalid,
)
from ospf_python.core.solver.output.solver_status import SolverStatus
from ospf_python.core.solver.value.solve_value import SolveValue
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    GanttSolution,
    TaskScheduleEntry,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column_generation_algorithm import (
    TaskColumnGenerationAlgorithm,
    TaskPricingColumn,
    TaskPricingPolicy,
    TaskPricingResult,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_model_builder import (
    _build_native_task_model,
    _build_triad_from_export,
    _extract_triad_shadow_prices,
    _task_column_coefficients,
    build_schedule,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_utilization import (
    ResourceUtilization,
)
from ospf_python.framework.gantt_scheduling.domain.task.error.gantt_errors import (
    GanttErrors,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err, ExErr
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python._binding.control import ProgressCallback
    from ospf_python._binding.model import MetaModelFloat64
    from ospf_python.core.model.intermediate.linear_triad_model import (
        LinearTriadModel,
    )
    from ospf_python.core.solver.solver import Solver
    from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
        GanttProblem,
    )
    from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
        TaskColumn,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
        ResourceContext,
    )
    from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
        TaskContext,
    )

T = TypeVar("T")
_TASK_COLUMN_MAX_WORK = 100_000_000


class TaskApplicationService:
    """任务应用服务 / Task application service.

    实现 BranchAndPrice 列生成编排。
    管理列生成算法的完整生命周期，包括问题注册、
    列增删、影子价格刷新、模型终止和解提取。
    Implements BranchAndPrice column generation orchestration.
    Manages the full lifecycle of the column generation algorithm,
    including problem registration, column add/remove, shadow
    price refresh, model finalization, and solution extraction.

    Attributes:
        _solver: 求解器实例 / Solver instance.
        _task_context: 任务上下文 / Task context.
        _resource_context: 资源上下文 / Resource context.
        _native_model: Rust 持有的原生模型 / Rust-owned native model.
        _native_solver: 可选的显式原生 LP 后端 / Optional explicit native LP backend.
        _iteration: 当前迭代次数 / Current iteration count.
        _max_iterations: 最大迭代次数 / Maximum iterations.
        _converged: 是否已收敛 / Whether converged.
        _shadow_prices: 影子价格字典 / Shadow price dict.
        _dual_values: 最近一次完整源行对偶 / Latest complete source-row duals.
        _active_columns: 活跃列列表 / Active column list.
        _window_columns: 固定容量窗口事件集 / Fixed capacity-window event set.
        _problem: 已注册的问题 / Registered problem.
    """

    def __init__(
        self,
        *,
        solver: Solver,
        task_context: TaskContext,
        resource_context: ResourceContext,
        max_iterations: int = 100,
        native_solver: str | None = None,
    ) -> None:
        """初始化任务应用服务 / Initialize task application service.

        Args:
            solver: 求解器实例 / Solver instance.
            task_context: 任务上下文 / Task context.
            resource_context: 资源上下文 / Resource context.
            max_iterations: 最大迭代次数 / Maximum iterations.
            native_solver: 显式原生 LP 后端；省略时保持现有 solver 路径 / Explicit native LP backend; omitted keeps the existing solver path.
        """
        self._solver = solver
        self._task_context = task_context
        self._resource_context = resource_context
        self._max_iterations = max_iterations
        self._native_solver = native_solver
        self._native_model: MetaModelFloat64 | None = None
        self._iteration: int = 0
        self._converged: bool = False
        self._finite_pool_exhausted: bool = False
        self._shadow_prices: dict[str, float] = {}
        self._dual_values: dict[str, float] = {}
        self._active_columns: list[TaskColumn] = []
        self._window_columns: tuple[TaskColumn, ...] = ()
        self._problem: GanttProblem | None = None

    # ==================== 生命周期 / Lifecycle =====================

    def register(
        self,
        problem: GanttProblem,
        *,
        cancellation: CancellationScope | None = None,
    ) -> Result[None, str, Err[str]]:
        """注册问题变量和约束 / Register problem variables and constraints.

        在 Rust 所有者中注册任务变量、资源容量约束和优先关系约束，
        设置最小化完工时间目标。
        Registers task variables, capacity and precedence rows on the Rust
        owner and minimizes the makespan plus selected-column cost.

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.
            cancellation: 发布候选模型前观察的取消作用域 / Cancellation scope observed before publishing the candidate model.

        Returns:
            注册结果 / Registration result.
        """
        if cancellation is not None and not isinstance(cancellation, CancellationScope):
            return invalid("需要 CancellationScope / Expected a CancellationScope")
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        validation = problem.validate()
        if validation.is_failed():
            return validation
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        model = _build_native_task_model(
            problem=problem,
            active_columns=(),
            window_columns=(),
        )
        if model.is_failed():
            return _service_failure(model.error)
        candidate = model.unwrap()
        if cancellation is not None and cancellation.is_cancelled:
            candidate.close()
            return _cancelled_failure()

        self._replace_native_model(candidate)
        self._problem = problem
        self._active_columns.clear()
        self._window_columns = ()
        self._shadow_prices.clear()
        self._dual_values.clear()
        self._iteration = 0
        self._converged = False
        self._finite_pool_exhausted = False

        return Ok(None)

    def add_columns(
        self,
        new_columns: tuple[TaskColumn, ...],
        *,
        cancellation: CancellationScope | None = None,
    ) -> Result[None, str, Err[str]]:
        """新增调度列 / Add new scheduling columns.

        校验整批列后在新的 Rust 模型中重建结构，成功后才原子替换当前模型。
        Validates the batch, rebuilds the structure on a fresh Rust model, and
        replaces the current model only after the whole build succeeds.

        Args:
            new_columns: 待添加的列 / Columns to add.
            cancellation: 发布候选模型前观察的取消作用域 / Cancellation scope observed before publishing the candidate model.

        Returns:
            操作结果 / Operation result.
        """
        if cancellation is not None and not isinstance(cancellation, CancellationScope):
            return invalid("需要 CancellationScope / Expected a CancellationScope")
        if not new_columns:
            return Ok(None)

        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]

        validation = self._validate_column_batch(
            new_columns=new_columns,
            cancellation=cancellation,
        )
        if validation.is_failed():
            return validation
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        problem = self._require_problem()
        if problem.is_failed():
            return problem

        candidate_columns = (*self._active_columns, *new_columns)
        window_columns = _merge_columns(
            self._window_columns,
            candidate_columns,
        )
        native_model = _build_native_task_model(
            problem=problem.unwrap(),
            active_columns=candidate_columns,
            window_columns=window_columns,
        )
        if native_model.is_failed():
            return _service_failure(native_model.error)
        candidate = native_model.unwrap()
        if cancellation is not None and cancellation.is_cancelled:
            candidate.close()
            return _cancelled_failure()

        self._replace_native_model(candidate)
        self._active_columns.extend(new_columns)
        self._window_columns = window_columns
        self._shadow_prices.clear()
        self._dual_values.clear()
        self._converged = False
        self._finite_pool_exhausted = False
        return Ok(None)

    def remove_columns(
        self,
        column_keys: tuple[str, ...],
        *,
        cancellation: CancellationScope | None = None,
    ) -> Result[None, str, Err[str]]:
        """移除调度列 / Remove scheduling columns.

        从候选活跃列重建 Rust 模型，成功后才发布删除结果。
        Rebuilds the Rust model from the candidate active set and publishes the
        removal only after the rebuild succeeds.

        Args:
            column_keys: 待移除的列键 / Column keys to remove.
            cancellation: 发布候选模型前观察的取消作用域 / Cancellation scope observed before publishing the candidate model.

        Returns:
            操作结果 / Operation result.
        """
        if cancellation is not None and not isinstance(cancellation, CancellationScope):
            return invalid("需要 CancellationScope / Expected a CancellationScope")
        if not column_keys:
            return Ok(None)

        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]
        problem = self._require_problem()
        if problem.is_failed():
            return problem
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        key_set = set(column_keys)
        kept_columns: list[TaskColumn] = []
        for column in self._active_columns:
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            if column.column_key not in key_set:
                kept_columns.append(column)
        candidate_columns = tuple(kept_columns)
        if len(candidate_columns) == len(self._active_columns):
            return Ok(None)

        native_model = _build_native_task_model(
            problem=problem.unwrap(),
            active_columns=candidate_columns,
            window_columns=(
                self._window_columns if self._window_columns else candidate_columns
            ),
        )
        if native_model.is_failed():
            return _service_failure(native_model.error)
        candidate = native_model.unwrap()
        if cancellation is not None and cancellation.is_cancelled:
            candidate.close()
            return _cancelled_failure()

        self._replace_native_model(candidate)
        self._active_columns = list(candidate_columns)
        if not self._window_columns:
            self._window_columns = candidate_columns
        self._shadow_prices.clear()
        self._dual_values.clear()
        self._converged = False
        self._finite_pool_exhausted = False
        return Ok(None)

    def refresh_shadow_price(
        self,
        *,
        time_limit: int | float | None = None,
        cancellation: CancellationScope | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Result[dict[str, float], str, Err[str]]:
        """刷新影子价格 / Refresh shadow prices.

        求解当前 LP 松弛，提取约束的对偶值（影子价格），
        更新影子价格映射并检查收敛性。

        Args:
            time_limit: 本次原生 LP 的可选秒数 / Optional native-LP time limit.
            cancellation: 显式原生求解的取消作用域 / Cancellation scope for an explicit native solve.
            on_progress: 显式原生求解的只读进度回调 / Read-only callback for an explicit native solve.

        Returns:
            影子价格字典或错误 / Shadow price dict or error.
        """
        validated_limit = _validated_time_limit(time_limit)
        if validated_limit.is_failed():
            return Failed(validated_limit.error)
        if cancellation is not None and not isinstance(cancellation, CancellationScope):
            return invalid("需要 CancellationScope / Expected a CancellationScope")
        if on_progress is not None and not callable(on_progress):
            return invalid("进度回调必须可调用 / Progress callback must be callable")

        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]
        if self._native_solver is None and any(
            control is not None for control in (time_limit, cancellation, on_progress)
        ):
            return Failed(
                Err(
                    _code=ErrorCode.NOT_SUPPORTED,
                    _message=(
                        "影子价格停止控制需要显式原生后端 / "
                        "Shadow-price stop controls require an explicit native backend"
                    ),
                )
            )
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        if self._native_solver is not None:
            return self._refresh_native_shadow_price(
                time_limit=validated_limit.unwrap(),
                cancellation=cancellation,
                on_progress=on_progress,
            )

        triad = self._native_triad(relaxation=True)
        if triad.is_failed():
            return _service_failure(triad.error)
        output = self._solver.solve(triad.unwrap())

        if output.status is SolverStatus.ERROR:
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=("LP 松弛求解失败 / LP relaxation solve failed"),
                )
            )

        if output.status is SolverStatus.INFEASIBLE:
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=("LP 松弛不可行 / LP relaxation is infeasible"),
                )
            )

        prices = _extract_triad_shadow_prices(
            triad=triad.unwrap(),
            values=output.values,
            dual_values=output.dual_values,
            task_count=(
                len(self._problem.tasks) if self._problem is not None else None
            ),
        )
        if prices.is_failed():
            return _service_failure(prices.error)
        self._shadow_prices = prices.unwrap()
        self._dual_values = dict(output.dual_values or {})
        self._iteration += 1

        if self._iteration >= self._max_iterations:
            self._converged = True

        return Ok(dict(self._shadow_prices))

    def run_task_pricing(
        self,
        *,
        columns: tuple[TaskPricingColumn, ...],
        policy: TaskPricingPolicy,
        solver: str | None = None,
        time_limit: int | float | None = None,
        cancellation: CancellationScope | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Result[TaskPricingResult, str, Err[str]]:
        """执行一次显式无时隙任务定价 / Run one explicit unslotted task-pricing pass.

        该入口把已注册问题的任务和资源顺序映射为上游任务与执行器索引，创建
        公共 `TaskColumnGenerationAlgorithm`，完成初始列注册、LP 求解和策略批次。
        它不会替换或修改当前 Gantt 原生模型、活跃列、影子价格或迭代状态。
        This entry maps the registered problem's task and resource order to
        upstream task and executor indices, creates the public
        `TaskColumnGenerationAlgorithm`, and performs initial-column registration,
        LP solve and policy generation. It never replaces or mutates the current
        Gantt native model, active columns, shadow prices or iteration state.

        Args:
            columns: 初始无时隙任务-执行器列 / Initial unslotted task-executor columns.
            policy: 认证定价策略 / Certified pricing policy.
            solver: 显式后端；省略时使用服务配置 / Explicit backend; defaults to the service setting.
            time_limit: 本次 LP 的可选秒数 / Optional seconds for this LP.
            cancellation: 单次 LP attempt 的取消作用域 / Cancellation scope for the single LP attempt.
            on_progress: 只读进度回调 / Read-only progress callback.

        Returns:
            任务、资源键与 LP 报告、批次和认证下界快照 / Task and resource keys
            with the LP report, batch and certified-bound snapshot.
        """
        problem = self._require_problem()
        if problem.is_failed():
            return problem
        registered = problem.unwrap()
        if not registered.resources:
            return Failed(
                Err(
                    _code=ErrorCode.FAILED_PRECONDITION,
                    _message=(
                        "任务定价需要至少一个执行器资源 / "
                        "Task pricing requires at least one executor resource"
                    ),
                )
            )
        if self._max_iterations <= 0:
            return Failed(
                Err(
                    _code=ErrorCode.FAILED_PRECONDITION,
                    _message=(
                        "最大迭代次数必须为正 / Maximum iterations must be positive"
                    ),
                )
            )
        validated_limit = _validated_time_limit(time_limit)
        if validated_limit.is_failed():
            return Failed(validated_limit.error)
        if cancellation is not None and not isinstance(cancellation, CancellationScope):
            return invalid("需要 CancellationScope / Expected a CancellationScope")
        if on_progress is not None and not callable(on_progress):
            return invalid("进度回调必须可调用 / Progress callback must be callable")
        if not callable(policy):
            return invalid("定价策略必须可调用 / Pricing policy must be callable")

        native_solver = self._native_solver if solver is None else solver
        if native_solver is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_SUPPORTED,
                    _message=(
                        "任务定价需要显式原生后端 / "
                        "Task pricing requires an explicit native backend"
                    ),
                )
            )
        if not isinstance(native_solver, str) or not native_solver.strip():
            return invalid(
                "原生后端名称不能为空 / Native solver name must not be empty"
            )
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        created = TaskColumnGenerationAlgorithm.create(
            task_count=len(registered.tasks),
            executor_count=len(registered.resources),
            max_iterations=self._max_iterations,
        )
        if created.is_failed():
            return _service_failure(created.error)
        algorithm = created.unwrap()

        added = algorithm.add_columns(list(columns))
        if added.is_failed():
            return _service_failure(added.error)
        compatible = _validate_pricing_columns(
            problem=registered,
            columns=added.unwrap(),
            cancellation=cancellation,
        )
        if compatible.is_failed():
            return compatible
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        attempt_handle = None if cancellation is None else cancellation.new_handle()
        if attempt_handle is not None and attempt_handle.is_failed():
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            return _service_failure(attempt_handle.error)

        solved = algorithm.solve_lp(
            solver=native_solver,
            time_limit=validated_limit.unwrap(),
            cancellation=None if attempt_handle is None else attempt_handle.unwrap(),
            on_progress=on_progress,
        )
        if solved.is_failed():
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            return _service_failure(solved.error)
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        report = solved.unwrap()
        if report.termination_reason == "CANCELLED":
            return _cancelled_failure()
        if report.problem_status == "INFEASIBLE":
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=("任务定价 LP 不可行 / Task-pricing LP is infeasible"),
                )
            )
        if report.termination_reason == "TIME_LIMIT":
            return _timeout_failure()
        if not report.is_optimal:
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=(
                        "任务定价 LP 未达到最优 / Task-pricing LP did not reach optimality"
                    ),
                )
            )

        generated = algorithm.generate(policy)
        if generated.is_failed():
            return _service_failure(generated.error)
        batch = generated.unwrap()
        compatible = _validate_pricing_columns(
            problem=registered,
            columns=batch.columns,
            cancellation=cancellation,
        )
        if compatible.is_failed():
            return compatible
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()
        bound = algorithm.certified_lower_bound()
        if bound.is_failed():
            return _service_failure(bound.error)

        return Ok(
            TaskPricingResult(
                task_keys=tuple(task.task_key for task in registered.tasks),
                resource_keys=tuple(
                    resource.resource_key for resource in registered.resources
                ),
                lp_report=report,
                batch=batch,
                certified_lower_bound=bound.unwrap(),
            )
        )

    def _refresh_native_shadow_price(
        self,
        *,
        model: MetaModelFloat64 | None = None,
        time_limit: float | None = None,
        cancellation: CancellationScope | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Result[dict[str, float], str, Err[str]]:
        """从同一原生快照的 LP 松弛提取证书价格 / Extract certified prices from one relaxed native snapshot.

        Args:
            model: 可选的待求解模型；省略时使用当前发布模型 / Optional model to solve instead of the published model.
            time_limit: 本次尝试的剩余秒数 / Remaining seconds for this attempt.
            cancellation: 多 attempt 取消作用域 / Multi-attempt cancellation scope.
            on_progress: 只读进度回调 / Read-only progress callback.

        Returns:
            影子价格字典或错误 / Shadow price dict or error.
        """
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()
        if model is None:
            required = self._require_model()
            if required.is_failed():
                return required  # type: ignore[return-value]
            native_model = required.unwrap()
        else:
            native_model = model
        native_solver = self._native_solver
        if native_solver is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_INITIALIZED,
                    _message=(
                        "未配置原生 LP 后端 / Native LP backend is not configured"
                    ),
                )
            )

        exported = native_model.to_linear_triad()
        if exported.is_failed():
            return _service_failure(exported.error)

        attempt_handle = None if cancellation is None else cancellation.new_handle()
        if attempt_handle is not None and attempt_handle.is_failed():
            return _service_failure(attempt_handle.error)
        attempt = native_model.solve_relaxed_compiled(
            solver=native_solver,
            time_limit=time_limit,
            cancellation=None if attempt_handle is None else attempt_handle.unwrap(),
            on_progress=on_progress,
        )
        if attempt.is_failed():
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            return _service_failure(attempt.error)
        compiled = attempt.unwrap()
        if compiled.report.problem_status == "INFEASIBLE":
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=("LP 松弛不可行 / LP relaxation is infeasible"),
                )
            )
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()
        if compiled.report.termination_reason != "COMPLETED":
            return _termination_failure(compiled.report.termination_reason)
        if compiled.certificate.is_failed():
            return _service_failure(compiled.certificate.error)

        handles = native_model.constraint_handles()
        if handles.is_failed():
            return _service_failure(handles.error)
        certificate = compiled.certificate.unwrap()
        dual_values: dict[str, float] = {}
        for constraint_handle in handles.unwrap():
            price = native_model.source_price(
                certificate=certificate,
                handle=constraint_handle,
            )
            if price.is_failed():
                return _service_failure(price.error)
            dual_values[constraint_handle.name] = price.unwrap()

        triad = _build_triad_from_export(
            exported=exported.unwrap(),
            relaxation=True,
        )
        if triad.is_failed():
            return _service_failure(triad.error)
        triad_model = triad.unwrap()
        if len(compiled.report.values) != len(triad_model.variables):
            return invalid(
                "LP 解向量与变量顺序不一致 / LP values do not match variable order"
            )
        prices = _extract_triad_shadow_prices(
            triad=triad_model,
            values=SolveValue(
                values=dict(
                    zip(
                        triad_model.variables,
                        compiled.report.values,
                        strict=True,
                    )
                )
            ),
            dual_values=dual_values,
            task_count=(
                len(self._problem.tasks) if self._problem is not None else None
            ),
        )
        if prices.is_failed():
            return _service_failure(prices.error)

        self._shadow_prices = prices.unwrap()
        self._dual_values = dual_values
        self._iteration += 1
        if self._iteration >= self._max_iterations:
            self._converged = True
        return Ok(dict(self._shadow_prices))

    def run_column_generation(
        self,
        *,
        candidates: tuple[TaskColumn, ...],
        tolerance: float = 1e-9,
        time_limit: int | float | None = None,
        cancellation: CancellationScope | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Result[tuple[TaskColumn, ...], str, Err[str]]:
        """在有限候选池上自动执行列生成 / Run column generation over a finite candidate pool.

        每轮使用当前原生 LP 证书的完整源行对偶计算候选列缩减成本，严格低于
        `-tolerance` 的列整批加入。容量窗口固定为整个候选池的事件集，避免加列
        改变行结构后复用错误对偶。该入口只证明有限候选池已扫描完，不证明上游
        完整定价域或整数最优。
        Each round prices candidates with complete source-row duals from the
        current certified native LP and atomically adds every column below
        `-tolerance`. Capacity windows are fixed over the whole candidate pool so
        adding columns cannot silently change the row structure. This proves
        only that the finite pool has no further improving column, not global
        pricing or integer optimality.

        Args:
            candidates: 待定价的有限候选池 / Finite candidate pool to price.
            tolerance: 严格改善阈值 / Strict improvement threshold.
            time_limit: 整轮总时限秒数，跨所有 LP attempt / Total run limit across all LP attempts.
            cancellation: 跨多个单次 attempt 的取消作用域 / Cancellation scope spanning single-use attempts.
            on_progress: 每次 LP attempt 的只读进度回调 / Read-only callback for each LP attempt.

        Returns:
            本轮实际加入的列或错误 / Columns added by this run, or an error.
        """
        if self._native_solver is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_SUPPORTED,
                    _message=(
                        "有限候选池列生成需要显式原生后端 / "
                        "Finite-pool column generation requires an explicit native backend"
                    ),
                )
            )
        if (
            isinstance(tolerance, bool)
            or not isinstance(tolerance, (int, float))
            or not math.isfinite(tolerance)
            or tolerance < 0.0
        ):
            return Failed(
                Err(
                    _code=ErrorCode.ILLEGAL_ARGUMENT,
                    _message=(
                        "缩减成本容差必须有限且非负 / "
                        "Reduced-cost tolerance must be finite and nonnegative"
                    ),
                )
            )
        validated_limit = _validated_time_limit(time_limit)
        if validated_limit.is_failed():
            return Failed(validated_limit.error)
        if cancellation is not None and not isinstance(cancellation, CancellationScope):
            return invalid("需要 CancellationScope / Expected a CancellationScope")
        if on_progress is not None and not callable(on_progress):
            return invalid("进度回调必须可调用 / Progress callback must be callable")
        if self._max_iterations <= 0:
            return Failed(
                Err(
                    _code=ErrorCode.FAILED_PRECONDITION,
                    _message=(
                        "最大迭代次数必须为正 / Maximum iterations must be positive"
                    ),
                )
            )

        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]
        problem = self._require_problem()
        if problem.is_failed():
            return problem
        if not self._active_columns:
            return Failed(
                Err(
                    _code=ErrorCode.FAILED_PRECONDITION,
                    _message=(
                        "自动列生成需要至少一个初始活跃列 / "
                        "Automatic column generation requires at least one active seed column"
                    ),
                )
            )

        active_by_key = {column.column_key: column for column in self._active_columns}
        remaining: list[TaskColumn] = []
        candidate_keys: set[str] = set()
        for candidate in candidates:
            if candidate.column_key in candidate_keys:
                return Failed(
                    Err(
                        _code=ErrorCode.ALREADY_EXIST,
                        _message=(
                            f"候选列键重复: {candidate.column_key} / "
                            f"Duplicate candidate column key: {candidate.column_key}"
                        ),
                    )
                )
            candidate_keys.add(candidate.column_key)
            active = active_by_key.get(candidate.column_key)
            if active is not None:
                if active != candidate:
                    return Failed(
                        Err(
                            _code=ErrorCode.ALREADY_EXIST,
                            _message=(
                                f"候选列与活跃列内容不一致: {candidate.column_key} / "
                                f"Candidate differs from active column: {candidate.column_key}"
                            ),
                        )
                    )
                continue
            remaining.append(candidate)

        validation = self._validate_column_batch(
            new_columns=tuple(remaining),
            cancellation=cancellation,
        )
        if validation.is_failed():
            return validation

        seconds = validated_limit.unwrap()
        deadline = None if seconds is None else time.monotonic() + seconds
        self._iteration = 0
        self._converged = False
        self._finite_pool_exhausted = False
        self._shadow_prices.clear()
        self._dual_values.clear()

        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()
        if _remaining_time(deadline) == 0.0:
            return _timeout_failure()

        window_columns = _merge_columns(
            self._window_columns,
            self._active_columns,
            candidates,
        )
        native_model = _build_native_task_model(
            problem=problem.unwrap(),
            active_columns=tuple(self._active_columns),
            window_columns=window_columns,
        )
        if native_model.is_failed():
            return _service_failure(native_model.error)

        current_model = native_model.unwrap()
        if cancellation is not None and cancellation.is_cancelled:
            current_model.close()
            return _cancelled_failure()
        if _remaining_time(deadline) == 0.0:
            current_model.close()
            return _timeout_failure()

        added: list[TaskColumn] = []
        while self._iteration < self._max_iterations:
            if cancellation is not None and cancellation.is_cancelled:
                if self._native_model is not current_model:
                    current_model.close()
                return _cancelled_failure()
            remaining_time = _remaining_time(deadline)
            if remaining_time == 0.0:
                if self._native_model is not current_model:
                    current_model.close()
                return _timeout_failure()

            prices = self._refresh_native_shadow_price(
                model=current_model,
                time_limit=remaining_time,
                cancellation=cancellation,
                on_progress=on_progress,
            )
            if prices.is_failed():
                if self._native_model is not current_model:
                    current_model.close()
                return _service_failure(prices.error)
            if self._native_model is not current_model:
                self._replace_native_model(current_model)
            self._window_columns = window_columns

            coefficients = {
                column.column_key: (
                    column.cost,
                    _task_column_coefficients(
                        problem=problem.unwrap(),
                        column=column,
                        window_columns=window_columns,
                    ),
                )
                for column in remaining
            }
            improving = _native_improving_columns(
                columns=coefficients,
                dual_values=self._dual_values,
                tolerance=float(tolerance),
            )
            if improving.is_failed():
                return _service_failure(improving.error)
            improving_by_key = improving.unwrap()
            batch = tuple(
                column
                for column in remaining
                if improving_by_key.get(column.column_key, False)
            )
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            if _remaining_time(deadline) == 0.0:
                return _timeout_failure()
            if not batch:
                self._converged = True
                self._finite_pool_exhausted = True
                return Ok(tuple(added))

            candidate_active = (*self._active_columns, *batch)
            candidate_model = _build_native_task_model(
                problem=problem.unwrap(),
                active_columns=candidate_active,
                window_columns=window_columns,
            )
            if candidate_model.is_failed():
                return _service_failure(candidate_model.error)

            candidate = candidate_model.unwrap()
            if cancellation is not None and cancellation.is_cancelled:
                candidate.close()
                return _cancelled_failure()
            if _remaining_time(deadline) == 0.0:
                candidate.close()
                return _timeout_failure()

            self._replace_native_model(candidate)
            current_model = candidate
            self._active_columns.extend(batch)
            added.extend(batch)
            batch_keys = {column.column_key for column in batch}
            remaining = [
                column for column in remaining if column.column_key not in batch_keys
            ]
            self._shadow_prices.clear()
            self._dual_values.clear()

        self._converged = True
        return Ok(tuple(added))

    def finalize(self) -> Result[None, str, Err[str]]:
        """终止列生成 / Finalize column generation.

        记录最终状态；实际最终 MIP 求解由 `extract_solution` 执行。
        Records the final state; `extract_solution` performs the final MIP solve.

        Returns:
            操作结果 / Operation result.
        """
        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]

        self._converged = True
        return Ok(None)

    def extract_solution(
        self,
        *,
        time_limit: int | float | None = None,
        cancellation: CancellationScope | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Result[GanttSolution, str, Err[str]]:
        """提取调度方案 / Extract scheduling solution.

        从原生模型的只读三元组快照求解，构建任务调度表，
        计算 KPI（完工时间、利用率），返回 GanttSolution。
        Solves a read-only triad snapshot of the native model, builds the task
        schedule and computes completion and utilization KPIs.

        Args:
            time_limit: 最终 MIP 的可选秒数 / Optional final-MIP time limit.
            cancellation: 显式原生求解的取消作用域 / Cancellation scope for an explicit native solve.
            on_progress: 显式原生求解的只读进度回调 / Read-only callback for an explicit native solve.

        Returns:
            调度方案或错误 / Scheduling solution or error.
        """
        validated_limit = _validated_time_limit(time_limit)
        if validated_limit.is_failed():
            return Failed(validated_limit.error)
        if cancellation is not None and not isinstance(cancellation, CancellationScope):
            return invalid("需要 CancellationScope / Expected a CancellationScope")
        if on_progress is not None and not callable(on_progress):
            return invalid("进度回调必须可调用 / Progress callback must be callable")

        if self._native_model is None or self._problem is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_INITIALIZED,
                    _message=(
                        "模型未注册，请先调用 register / "
                        "Model not registered, call register first"
                    ),
                )
            )

        native_solver = self._native_solver
        if native_solver is None and any(
            control is not None for control in (time_limit, cancellation, on_progress)
        ):
            return Failed(
                Err(
                    _code=ErrorCode.NOT_SUPPORTED,
                    _message=(
                        "最终 MIP 停止控制需要显式原生后端 / "
                        "Final-MIP stop controls require an explicit native backend"
                    ),
                )
            )
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        if native_solver is not None and self._active_columns:
            return self._extract_finite_task_solution(
                solver=native_solver,
                time_limit=validated_limit.unwrap(),
                cancellation=cancellation,
                on_progress=on_progress,
            )
        if native_solver is not None:
            triad = self._native_triad(relaxation=False)
            if triad.is_failed():
                return _service_failure(triad.error)
            return self._extract_native_solution(
                solver=native_solver,
                triad=triad.unwrap(),
                time_limit=validated_limit.unwrap(),
                cancellation=cancellation,
                on_progress=on_progress,
            )

        triad = self._native_triad(relaxation=False)
        if triad.is_failed():
            return _service_failure(triad.error)
        output = self._solver.solve(triad.unwrap())

        if output.status is SolverStatus.ERROR:
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=("最终 MIP 求解失败 / Final MIP solve failed"),
                )
            )

        if output.status is SolverStatus.INFEASIBLE:
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=("最终 MIP 不可行 / Final MIP is infeasible"),
                )
            )

        schedule = build_schedule(
            problem=self._problem,
            values=output.values,
        )
        makespan = _compute_makespan(schedule)
        utilizations = self._compute_utilizations(
            schedule=schedule,
            makespan=makespan,
        )

        return Ok(
            GanttSolution(
                name=f"solution_{self._problem.name}",
                schedule=schedule,
                makespan=makespan,
                objective_value=output.objective,
                resource_utilizations=utilizations,
                is_optimal=(output.status is SolverStatus.OPTIMAL),
            )
        )

    # ==================== 属性 / Properties ========================

    @property
    def iteration(self) -> int:
        """当前迭代次数 / Current iteration count."""
        return self._iteration

    @property
    def converged(self) -> bool:
        """是否已收敛 / Whether converged."""
        return self._converged

    @property
    def finite_pool_exhausted(self) -> bool:
        """有限候选池是否已无严格改进列 / Whether the finite pool has no strictly improving column."""
        return self._finite_pool_exhausted

    @property
    def shadow_prices(self) -> dict[str, float]:
        """影子价格字典 / Shadow price dict."""
        return dict(self._shadow_prices)

    @property
    def active_columns(self) -> tuple[TaskColumn, ...]:
        """当前活跃列 / Currently active columns."""
        return tuple(self._active_columns)

    # ==================== 内部方法 / Internal methods ===============

    def _require_model(
        self,
    ) -> Result[MetaModelFloat64, str, Err[str]]:
        """获取已注册的原生模型 / Get the registered native model.

        Returns:
            原生模型或错误 / Native model or error.
        """
        if self._native_model is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_INITIALIZED,
                    _message=(
                        "模型未注册，请先调用 register / "
                        "Model not registered, call register "
                        "first"
                    ),
                )
            )
        return Ok(self._native_model)

    def _require_problem(self) -> Result[GanttProblem, str, Err[str]]:
        """获取已注册的问题 / Get the registered problem.

        Returns:
            甘特问题或错误 / Gantt problem or error.
        """
        if self._problem is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_INITIALIZED,
                    _message=(
                        "模型未注册，请先调用 register / "
                        "Model not registered, call register first"
                    ),
                )
            )
        return Ok(self._problem)

    def _native_triad(
        self,
        *,
        relaxation: bool,
    ) -> BindingResult[LinearTriadModel]:
        """从原生模型生成只读求解快照 / Build a read-only solver snapshot.

        Args:
            relaxation: 是否取消整数性但保留边界 / Whether to relax
                integrality while preserving bounds.

        Returns:
            线性三元组或绑定失败 / Linear triad or binding failure.
        """
        model = self._require_model()
        if model.is_failed():
            return Failed(
                ExErr(
                    _code=model.error.code,
                    _message=model.error.message,
                    value=FailureContext(
                        source="ospf-python",
                        category=model.error.code.name,
                        rust_code=None,
                        error_class="APPLICATION",
                    ),
                )
            )
        exported = model.unwrap().to_linear_triad()
        if exported.is_failed():
            return exported
        return _build_triad_from_export(
            exported=exported.unwrap(),
            relaxation=relaxation,
        )

    def _replace_native_model(self, model: MetaModelFloat64) -> None:
        """原子替换当前原生模型 / Atomically replace the current native model.

        Args:
            model: 已完整构建的新模型 / Fully built replacement model.
        """
        previous = self._native_model
        self._native_model = model
        if previous is not None:
            previous.close()

    def _validate_column_batch(
        self,
        *,
        new_columns: tuple[TaskColumn, ...],
        cancellation: CancellationScope | None = None,
    ) -> Result[None, str, Err[str]]:
        """原子校验待添加列 / Validate a column batch atomically.

        Args:
            new_columns: 待添加列 / Columns to add.
            cancellation: 校验循环的取消作用域 / Cancellation scope for validation loops.

        Returns:
            校验结果 / Validation result.
        """
        problem = self._problem
        if problem is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_INITIALIZED,
                    _message=(
                        "模型未注册，请先调用 register / "
                        "Model not registered, call register first"
                    ),
                )
            )
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        existing_keys = {column.column_key for column in self._active_columns}
        batch_keys: set[str] = set()

        for column in new_columns:
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            if (
                not isinstance(column.column_key, str)
                or not column.column_key
                or column.column_key in existing_keys
                or column.column_key in batch_keys
            ):
                return Failed(
                    Err(
                        _code=ErrorCode.ALREADY_EXIST,
                        _message=(
                            f"列已存在或列键为空: {column.column_key!r} / "
                            f"Column already exists or has an empty key: "
                            f"{column.column_key!r}"
                        ),
                    )
                )
            batch_keys.add(column.column_key)

            if not math.isfinite(column.cost):
                return Failed(
                    Err(
                        _code=ErrorCode.ILLEGAL_ARGUMENT,
                        _message=(
                            f"列成本必须有限: {column.column_key} / "
                            f"Column cost must be finite: {column.column_key}"
                        ),
                    )
                )
            if not column.task_assignments:
                return Failed(
                    Err(
                        _code=ErrorCode.ILLEGAL_ARGUMENT,
                        _message=(
                            f"列必须包含至少一个任务: {column.column_key} / "
                            f"Column must contain at least one task: "
                            f"{column.column_key}"
                        ),
                    )
                )

            seen_assignments: set[tuple[str, str]] = set()
            task_start_times: dict[str, float] = {}
            for task_key, resource_key, start_time in column.task_assignments:
                if cancellation is not None and cancellation.is_cancelled:
                    return _cancelled_failure()
                task = problem.task_by_key(task_key)
                if task is None:
                    return Failed(
                        Err(
                            _code=GanttErrors.TASK_NOT_FOUND.value,  # type: ignore[arg-type]
                            _message=(
                                f"列引用了未知任务: {task_key} / "
                                f"Column references unknown task: {task_key}"
                            ),
                        )
                    )
                if not problem.has_resource(resource_key):
                    return Failed(
                        Err(
                            _code=ErrorCode.NOT_FOUND,
                            _message=(
                                f"列引用了未知资源: {resource_key} / "
                                f"Column references an unknown resource: {resource_key}"
                            ),
                        )
                    )
                if task.resource_requirements and not task.requires_resource(
                    resource_key
                ):
                    return Failed(
                        Err(
                            _code=ErrorCode.NOT_FOUND,
                            _message=(
                                f"列引用了任务不使用的资源: {task_key}, {resource_key} / "
                                f"Column references a resource not required by the task: "
                                f"{task_key}, {resource_key}"
                            ),
                        )
                    )
                assignment_key = (task_key, resource_key)
                if assignment_key in seen_assignments:
                    return Failed(
                        Err(
                            _code=ErrorCode.ALREADY_EXIST,
                            _message=(
                                f"列内任务资源重复: {task_key}, {resource_key} / "
                                f"Duplicate task-resource assignment in column: "
                                f"{task_key}, {resource_key}"
                            ),
                        )
                    )
                seen_assignments.add(assignment_key)

                if not math.isfinite(start_time):
                    return Failed(
                        Err(
                            _code=ErrorCode.ILLEGAL_ARGUMENT,
                            _message=(
                                f"列开始时间必须有限: {column.column_key} / "
                                f"Column start time must be finite: "
                                f"{column.column_key}"
                            ),
                        )
                    )
                previous_start = task_start_times.setdefault(task_key, start_time)
                if not math.isclose(previous_start, start_time, abs_tol=1e-9):
                    return Failed(
                        Err(
                            _code=ErrorCode.ILLEGAL_ARGUMENT,
                            _message=(
                                f"同一列内任务开始时间不一致: {task_key} / "
                                f"Task start times differ within column: {task_key}"
                            ),
                        )
                    )
                if start_time < task.earliest_start - 1e-9:
                    return Failed(
                        Err(
                            _code=ErrorCode.ILLEGAL_ARGUMENT,
                            _message=(
                                f"列开始时间早于最早开始时间: {task_key} / "
                                f"Column starts before earliest start: {task_key}"
                            ),
                        )
                    )
                if (
                    task.deadline < float("inf")
                    and start_time + task.duration > task.deadline + 1e-9
                ):
                    return Failed(
                        Err(
                            _code=ErrorCode.ILLEGAL_ARGUMENT,
                            _message=(
                                f"列结束时间晚于截止时间: {task_key} / "
                                f"Column ends after deadline: {task_key}"
                            ),
                        )
                    )

        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()
        return Ok(None)

    def _extract_native_solution(
        self,
        *,
        solver: str,
        triad: LinearTriadModel,
        time_limit: float | None = None,
        cancellation: CancellationScope | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Result[GanttSolution, str, Err[str]]:
        """从原生编译快照提取最终 MIP 解 / Extract the final MIP from one compiled native snapshot.

        Args:
            solver: 已编译后端 / Compiled backend.
            triad: 同模型导出的变量顺序 / Variable order exported from the same model.
            time_limit: 最终 MIP 秒数 / Final-MIP seconds.
            cancellation: 取消作用域 / Cancellation scope.
            on_progress: 只读进度回调 / Read-only progress callback.

        Returns:
            调度方案或错误 / Schedule solution or error.
        """
        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]
        problem = self._require_problem()
        if problem.is_failed():
            return problem
        problem = problem.unwrap()

        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()
        attempt_handle = None if cancellation is None else cancellation.new_handle()
        if attempt_handle is not None and attempt_handle.is_failed():
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            return _service_failure(attempt_handle.error)
        attempt = model.unwrap().solve_compiled(
            solver=solver,
            time_limit=time_limit,
            cancellation=None if attempt_handle is None else attempt_handle.unwrap(),
            on_progress=on_progress,
        )
        if attempt.is_failed():
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            return _service_failure(attempt.error)
        report = attempt.unwrap().report
        if report.termination_reason == "CANCELLED":
            return _cancelled_failure()
        if report.termination_reason not in {"COMPLETED", "TIME_LIMIT"}:
            return _termination_failure(report.termination_reason)
        if report.problem_status == "INFEASIBLE":
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=("最终 MIP 不可行 / Final MIP is infeasible"),
                )
            )
        if report.solution_presence == "NONE":
            if report.termination_reason == "TIME_LIMIT":
                return _timeout_failure()
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=("最终 MIP 未提供解 / Final MIP has no solution"),
                )
            )
        if report.objective is None:
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=("最终 MIP 缺少目标值 / Final MIP has no objective value"),
                )
            )
        if len(report.values) != len(triad.variables):
            return invalid(
                "MIP 解向量与变量顺序不一致 / MIP values do not match variable order"
            )

        schedule = build_schedule(
            problem=problem,
            values=SolveValue(
                values=dict(zip(triad.variables, report.values, strict=True))
            ),
        )
        makespan = _compute_makespan(schedule)
        return Ok(
            GanttSolution(
                name=f"solution_{problem.name}",
                schedule=schedule,
                makespan=makespan,
                objective_value=report.objective,
                resource_utilizations=self._compute_utilizations(
                    schedule=schedule,
                    makespan=makespan,
                ),
                is_optimal=(report.solution_presence == "OPTIMAL"),
            )
        )

    def _extract_finite_task_solution(
        self,
        *,
        solver: str,
        time_limit: float | None = None,
        cancellation: CancellationScope | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Result[GanttSolution, str, Err[str]]:
        """在 Rust 有限活动模型上求解当前任务列 / Solve current task columns on the Rust finite activity model."""
        problem = self._require_problem()
        if problem.is_failed():
            return problem
        registered = problem.unwrap()
        if not self._active_columns:
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=(
                        "没有可求解的任务列 / There are no task columns to solve"
                    ),
                )
            )
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        units = _task_resource_units(registered)
        if units.is_failed():
            return _service_failure(units.error)
        attempt_handle = None if cancellation is None else cancellation.new_handle()
        if attempt_handle is not None and attempt_handle.is_failed():
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            return _service_failure(attempt_handle.error)

        solved = _solve_task_columns(
            problem=registered,
            columns=tuple(self._active_columns),
            resource_units=units.unwrap(),
            max_work=_TASK_COLUMN_MAX_WORK,
            solver=solver,
            time_limit=time_limit,
            cancellation=None if attempt_handle is None else attempt_handle.unwrap(),
            on_progress=on_progress,
            objective="makespan_cost",
        )
        if solved.is_failed():
            if cancellation is not None and cancellation.is_cancelled:
                return _cancelled_failure()
            return _service_failure(solved.error)
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()

        output = solved.unwrap()
        report = output.report
        if report.termination_reason == "CANCELLED":
            return _cancelled_failure()
        if report.problem_status == "INFEASIBLE":
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=("任务列模型不可行 / Task-column model is infeasible"),
                )
            )
        if report.solution_presence == "NONE":
            if report.termination_reason == "TIME_LIMIT":
                return _timeout_failure()
            return _termination_failure(report.termination_reason)
        if report.termination_reason not in {"COMPLETED", "TIME_LIMIT"}:
            return _termination_failure(report.termination_reason)
        if output.solution.is_failed():
            return _service_failure(output.solution.error)

        selection = output.solution.unwrap()
        schedule = _schedule_from_task_columns(
            problem=registered,
            columns=selection.columns,
        )
        if schedule.is_failed():
            return _service_failure(schedule.error)
        entries = schedule.unwrap()
        makespan = _compute_makespan(entries)
        objective = Fraction(makespan) + sum(
            (Fraction(column.cost) for column in selection.columns),
            Fraction(),
        )
        return Ok(
            GanttSolution(
                name=f"solution_{registered.name}",
                schedule=entries,
                makespan=makespan,
                objective_value=float(objective),
                resource_utilizations=self._compute_utilizations(
                    schedule=entries,
                    makespan=makespan,
                ),
                is_optimal=(report.solution_presence == "OPTIMAL"),
            )
        )

    def _compute_utilizations(
        self,
        *,
        schedule: tuple[TaskScheduleEntry, ...],
        makespan: float,
    ) -> tuple[ResourceUtilization, ...]:
        """计算资源利用率 / Compute resource utilizations.

        Args:
            schedule: 调度条目元组 / Schedule entry tuple.
            makespan: 完工时间 / Makespan.

        Returns:
            资源利用率元组 / Resource utilization tuple.
        """
        if self._problem is None or makespan <= 0.0:
            return ()

        # used_capacity 的单位是资源量，与 BunchCapacity/Capacity 的 used_capacity=total_demand
        # 口径一致。按任务条数计数会让需求量 3.0 和 0.1 的任务占用同样多的容量。
        # used_capacity is a resource amount, matching the used_capacity=total_demand convention
        # of BunchCapacity/Capacity. Counting tasks made demands of 3.0 and 0.1 consume alike.
        demand = {
            (task.task_key, resource_key): amount
            for task in self._problem.tasks
            for resource_key, amount in task.resource_requirements
        }
        utilizations: list[ResourceUtilization] = []
        for resource in self._problem.resources:
            used = sum(
                demand.get((entry.task_key, resource.resource_key), 0.0)
                for entry in schedule
                if entry.assigned_resource == resource.resource_key
            )
            utilizations.append(
                ResourceUtilization(
                    resource_key=resource.resource_key,
                    time_range_start=0.0,
                    time_range_end=makespan,
                    total_capacity=resource.capacity,
                    used_capacity=used,
                    peak_usage=used,
                )
            )

        return tuple(utilizations)


# ==================== 模块级辅助函数 / Module helpers ================


def _task_resource_units(problem: GanttProblem) -> BindingResult[dict[str, Unit]]:
    """为任务资源创建共享的无量纲原生单位 / Create one shared dimensionless native unit for task resources."""
    unit = Unit.create(
        name="scheduling resource",
        symbol="scheduling resource",
        powers=(0,) * 10,
    )
    return unit.map(
        lambda value: {resource.resource_key: value for resource in problem.resources}
    )


def _schedule_from_task_columns(
    *,
    problem: GanttProblem,
    columns: tuple[TaskColumn, ...],
) -> Result[tuple[TaskScheduleEntry, ...], str, Err[str]]:
    """把已选任务列映射为按问题顺序排列的调度 / Map selected task columns to a problem-ordered schedule."""
    tasks = {task.task_key: task for task in problem.tasks}
    resources = {resource.resource_key for resource in problem.resources}
    selected: dict[str, tuple[int | float, str]] = {}
    for column in columns:
        for task_key, resource_key, start_time in column.task_assignments:
            if task_key not in tasks or resource_key not in resources:
                return Failed(
                    Err(
                        _code=ErrorCode.APPLICATION_ERROR,
                        _message=(
                            "已选任务列引用未知任务或资源 / "
                            "Selected task column references an unknown task or resource"
                        ),
                    )
                )
            previous = selected.get(task_key)
            if previous is not None:
                if previous[0] != start_time:
                    return Failed(
                        Err(
                            _code=ErrorCode.APPLICATION_ERROR,
                            _message=(
                                "同一任务在已选列中的开始时间不一致 / "
                                "Selected columns disagree on a task start time"
                            ),
                        )
                    )
                continue
            selected[task_key] = (start_time, resource_key)

    entries: list[TaskScheduleEntry] = []
    for task in problem.tasks:
        placement = selected.get(task.task_key)
        if placement is None:
            return Failed(
                Err(
                    _code=ErrorCode.APPLICATION_ERROR,
                    _message=(
                        f"已选任务列未覆盖任务: {task.task_key} / "
                        f"Selected task columns do not cover task: {task.task_key}"
                    ),
                )
            )
        start_time, resource_key = placement
        entries.append(
            TaskScheduleEntry(
                task_key=task.task_key,
                start_time=start_time,
                end_time=start_time + task.duration,
                assigned_resource=resource_key,
            )
        )
    return Ok(tuple(entries))


def _merge_columns(
    *groups: tuple[TaskColumn, ...],
) -> tuple[TaskColumn, ...]:
    """按列键合并事件集，后出现的同键列覆盖旧快照 / Merge event sets by key with later snapshots winning.

    Args:
        groups: 按优先级排列的列组 / Column groups ordered by precedence.

    Returns:
        保持首次出现顺序的去重列元组 / Deduplicated columns preserving first-seen order.
    """
    merged: dict[str, TaskColumn] = {}
    for group in groups:
        for column in group:
            merged[column.column_key] = column
    return tuple(merged.values())


def _service_failure(
    error: ExErr[str, FailureContext],
) -> Result[T, str, Err[str]]:
    """将绑定失败映射为应用服务错误 / Map a binding failure to the service.

    Args:
        error: 保留原生来源的绑定错误 / Binding error with native provenance.

    Returns:
        应用服务错误 / Application-service failure.
    """
    return Failed(
        Err(
            _code=error.code,
            _message=error.message,
        )
    )


def _validate_pricing_columns(
    *,
    problem: GanttProblem,
    columns: list[TaskPricingColumn],
    cancellation: CancellationScope | None = None,
) -> Result[None, str, Err[str]]:
    """校验定价列与已注册任务资源域一致 / Validate pricing columns against the registered task-resource domain."""
    for task_index, executor_index, _cost in columns:
        if cancellation is not None and cancellation.is_cancelled:
            return _cancelled_failure()
        task = problem.tasks[task_index]
        resource = problem.resources[executor_index]
        if task.resource_requirements and not task.requires_resource(
            resource.resource_key
        ):
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(
                        "任务定价列引用了任务不使用的执行器资源: "
                        f"{task.task_key}, {resource.resource_key} / "
                        "Task-pricing column references an executor resource "
                        "not required by the task: "
                        f"{task.task_key}, {resource.resource_key}"
                    ),
                )
            )
    return Ok(None)


def _validated_time_limit(
    value: int | float | None,
) -> Result[float | None, str, Err[str]]:
    """校验整轮时限 / Validate the whole-run time limit.

    Args:
        value: 可选秒数 / Optional seconds.

    Returns:
        规范化秒数或输入错误 / Normalized seconds or an input failure.
    """
    if value is None:
        return Ok(None)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return invalid("时间限制需要 int 或 float / Time limit expects int or float")
    if isinstance(value, int) and abs(value) > 2**53 - 1:
        return invalid(
            "时间限制整数超出 Float64 精确边界 / "
            "Time-limit integer exceeds the exact Float64 boundary"
        )
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0.0:
        return invalid(
            "时间限制必须有限且为正 / Time limit must be finite and positive"
        )
    return Ok(seconds)


def _remaining_time(deadline: float | None) -> float | None:
    """计算剩余整轮时限 / Compute remaining whole-run time.

    Args:
        deadline: 单调时钟截止点 / Monotonic-clock deadline.

    Returns:
        剩余秒数或 None / Remaining seconds or None.
    """
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _timeout_failure() -> Result[T, str, Err[str]]:
    """构造整轮超时结果 / Build a whole-run timeout result."""
    return Failed(
        Err(
            _code=ErrorCode.TIMEOUT,
            _message=("列生成超过时限 / Column generation exceeded its time limit"),
        )
    )


def _cancelled_failure() -> Result[T, str, Err[str]]:
    """构造取消停止结果 / Build a cancellation stop result."""
    return Failed(
        Err(
            _code=ErrorCode.CANCELLED,
            _message=("列生成已取消 / Column generation was cancelled"),
        )
    )


def _termination_failure(reason: str) -> Result[T, str, Err[str]]:
    """把非完成终态映射为结构化停止 / Map non-completed termination to a structured stop.

    Args:
        reason: Rust 终止原因 / Rust termination reason.

    Returns:
        取消、时限或一般求解失败 / Cancellation, time limit, or generic solve failure.
    """
    if reason == "CANCELLED":
        return _cancelled_failure()
    if reason == "TIME_LIMIT":
        return _timeout_failure()
    return Failed(
        Err(
            _code=ErrorCode.SOLVE_FAILED,
            _message=("求解未完成 / Solve did not complete"),
        )
    )


def _compute_makespan(
    schedule: tuple[TaskScheduleEntry, ...],
) -> float:
    """计算完工时间 / Compute makespan.

    Args:
        schedule: 调度条目元组 / Schedule entry tuple.

    Returns:
        完工时间（秒）/ Makespan (seconds).
    """
    if not schedule:
        return 0.0
    return max(entry.end_time for entry in schedule)
