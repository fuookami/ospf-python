"""甘特调度束编组应用服务 / Gantt scheduling bunch application service.

实现 BranchAndPrice 列生成编排，管理束编组的完整列生成生命周期：
注册 -> 增列 -> 删列 -> 刷新影子价格 -> 终止 -> 提取解。
Implements BranchAndPrice column generation orchestration for
bunches, managing the full column generation lifecycle: register
-> add_columns -> remove_columns -> refresh_shadow_price ->
finalize -> extract_solution.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import TYPE_CHECKING, TypeVar

from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import (
    BindingResult,
    FailureContext,
)
from ospf_python.core.solver.output.solver_status import SolverStatus
from ospf_python.framework.gantt_scheduling.application.model.bunch.bunch_solution import (
    BunchAssignment,
    BunchSolution,
)
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    GanttSolution,
    TaskScheduleEntry,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_model_builder import (
    _build_bunch_triad,
    _build_native_bunch_model,
    _extract_bunch_shadow_prices,
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
    from ospf_python._binding.gantt_bunch import BunchSelection
    from ospf_python._binding.model import MetaModelFloat64, SolveReport
    from ospf_python.core.model.intermediate.linear_triad_model import (
        LinearTriadModel,
    )
    from ospf_python.core.model.mechanism.meta_model import MetaModel
    from ospf_python.core.solver.solver import Solver
    from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
        GanttProblem,
    )
    from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
        BunchColumn,
        BunchConstraintCoeff,
    )
    from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
        BunchGenerationContext,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
        ResourceContext,
    )
    from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
        TaskContext,
    )

T = TypeVar("T")

# 有限束列活动模型的工作量上限 / Work budget of the finite bunch-column activity model.
_BUNCH_COLUMN_MAX_WORK = 100_000_000


class BunchApplicationService:
    """束编组应用服务 / Bunch application service.

    实现 BranchAndPrice 列生成编排。
    管理束编组列生成算法的完整生命周期，包括问题注册、
    列增删、影子价格刷新、模型终止和解提取。
    Implements BranchAndPrice column generation orchestration.
    Manages the full lifecycle of the bunch column generation
    algorithm, including problem registration, column add/remove,
    shadow price refresh, model finalization, and solution
    extraction.

    Attributes:
        _solver: 求解器实例 / Solver instance.
        _task_context: 任务上下文 / Task context.
        _resource_context: 资源上下文 / Resource context.
        _bunch_context: 束编组上下文 / Bunch context.
        _native_model: Rust 持有的原生模型 / Rust-owned native model.
        _iteration: 当前迭代次数 / Current iteration count.
        _max_iterations: 最大迭代次数 / Maximum iterations.
        _converged: 是否已收敛 / Whether converged.
        _shadow_prices: 影子价格字典 / Shadow price dict.
        _active_columns: 活跃列列表 / Active column list.
        _problem: 已注册的问题 / Registered problem.
        _native_solver: 可选的显式原生 LP/MIP 后端 / Optional explicit native backend.
    """

    def __init__(
        self,
        *,
        solver: Solver,
        task_context: TaskContext,
        resource_context: ResourceContext,
        bunch_context: BunchGenerationContext,
        max_iterations: int = 100,
        native_solver: str | None = None,
    ) -> None:
        """初始化束编组应用服务 / Initialize bunch application service.

        Args:
            solver: 求解器实例 / Solver instance.
            task_context: 任务上下文 / Task context.
            resource_context: 资源上下文 / Resource context.
            bunch_context: 束编组上下文 / Bunch context.
            max_iterations: 最大迭代次数 / Maximum iterations.
            native_solver: 显式原生后端名；省略时保留现有 solver 路径 /
                Explicit native backend name; omitted keeps the existing solver path.
        """
        self._solver = solver
        self._task_context = task_context
        self._resource_context = resource_context
        self._bunch_context = bunch_context
        self._max_iterations = max_iterations
        self._native_solver = native_solver
        self._native_model: MetaModelFloat64 | None = None
        self._iteration: int = 0
        self._converged: bool = False
        self._shadow_prices: dict[str, float] = {}
        self._active_columns: list[BunchColumn] = []
        self._problem: GanttProblem | None = None

    # ==================== 生命周期 / Lifecycle =====================

    def register(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册问题变量和约束 / Register problem variables and constraints.

        在新的 Rust 模型中注册束编组变量、资源容量约束、优先关系、
        需求覆盖行和最小化列成本目标，完整成功后才发布。
        Registers bunch variables, capacity and precedence rows, demand
        coverage and the minimum-column-cost objective on a fresh Rust model,
        publishing it only after the whole build succeeds.

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.

        Returns:
            注册结果 / Registration result.
        """
        validation = problem.validate()
        if validation.is_failed():
            return validation

        native_model = _build_native_bunch_model(
            problem=problem,
            active_columns=(),
        )
        if native_model.is_failed():
            return _service_failure(native_model.error)

        self._replace_native_model(native_model.unwrap())
        self._problem = problem
        self._active_columns.clear()
        self._shadow_prices.clear()
        self._iteration = 0
        self._converged = False

        return Ok(None)

    def add_columns(
        self,
        new_bunches: tuple[BunchColumn, ...],
    ) -> Result[None, str, Err[str]]:
        """新增束编组列 / Add new bunch columns.

        整批校验后从候选活跃列重建 Rust 模型，成功后才原子替换。
        Validates the batch, rebuilds the Rust model from the candidate active
        set, and replaces the current model only after the build succeeds.

        Args:
            new_bunches: 待添加的束编组列 / Bunch columns to add.

        Returns:
            操作结果 / Operation result.
        """
        if not new_bunches:
            return Ok(None)

        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]

        validation = self._validate_column_batch(new_bunches=new_bunches)
        if validation.is_failed():
            return validation

        problem = self._require_problem()
        if problem.is_failed():
            return problem

        candidate_columns = (*self._active_columns, *new_bunches)
        native_model = _build_native_bunch_model(
            problem=problem.unwrap(),
            active_columns=candidate_columns,
        )
        if native_model.is_failed():
            return _service_failure(native_model.error)

        self._replace_native_model(native_model.unwrap())
        self._active_columns.extend(new_bunches)

        return Ok(None)

    def remove_columns(
        self,
        bunch_keys: tuple[str, ...],
    ) -> Result[None, str, Err[str]]:
        """移除束编组列 / Remove bunch columns.

        从候选活跃列重建 Rust 模型，成功后才发布删除结果。
        Rebuilds the Rust model from the candidate active set and publishes the
        removal only after the rebuild succeeds.

        Args:
            bunch_keys: 待移除的束编组键 / Bunch keys to remove.

        Returns:
            操作结果 / Operation result.
        """
        if not bunch_keys:
            return Ok(None)

        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]

        problem = self._require_problem()
        if problem.is_failed():
            return problem

        key_set = set(bunch_keys)
        candidate_columns = tuple(
            column for column in self._active_columns if column.bunch_key not in key_set
        )
        if len(candidate_columns) == len(self._active_columns):
            return Ok(None)

        native_model = _build_native_bunch_model(
            problem=problem.unwrap(),
            active_columns=candidate_columns,
        )
        if native_model.is_failed():
            return _service_failure(native_model.error)

        self._replace_native_model(native_model.unwrap())
        self._active_columns = list(candidate_columns)

        return Ok(None)

    def refresh_shadow_price(
        self,
    ) -> Result[dict[str, float], str, Err[str]]:
        """刷新影子价格 / Refresh shadow prices.

        求解当前 LP 松弛，提取约束的对偶值（影子价格），
        更新影子价格映射并检查收敛性。

        Returns:
            影子价格字典或错误 / Shadow price dict or error.
        """
        triad = self._native_triad(relaxation=True)
        if triad.is_failed():
            return _service_failure(triad.error)

        output = self._solver.solve(triad.unwrap())

        if output.status is SolverStatus.ERROR:
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=(
                        "束编组 LP 松弛求解失败 / Bunch LP relaxation solve failed"
                    ),
                )
            )

        if output.status is SolverStatus.INFEASIBLE:
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=(
                        "束编组 LP 松弛不可行 / Bunch LP relaxation is infeasible"
                    ),
                )
            )

        prices = _extract_bunch_shadow_prices(
            triad=triad.unwrap(),
            values=output.values.values,
            dual_values=output.dual_values,
        )
        if prices.is_failed():
            return _service_failure(prices.error)
        self._shadow_prices = prices.unwrap()
        self._iteration += 1

        if self._iteration >= self._max_iterations:
            self._converged = True

        return Ok(dict(self._shadow_prices))

    def finalize(self) -> Result[None, str, Err[str]]:
        """终止列生成 / Finalize column generation.

        将束编组分配变量设为整数约束，求解最终 MIP。

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
    ) -> Result[GanttSolution, str, Err[str]]:
        """提取调度方案 / Extract scheduling solution.

        从求解器结果中读取变量值，构建任务调度表，
        计算 KPI（完工时间、利用率），返回 GanttSolution。
        配置显式原生后端且存在活跃列时，最终解由固定 Rust 的有限束列
        activity 模型产生；其余情况保留现有 solver 路径。
        With an explicit native backend and active columns the final solution
        comes from the pinned Rust finite bunch-column activity model; other
        cases keep the existing solver path.

        Returns:
            调度方案或错误 / Scheduling solution or error.
        """
        if self._native_model is None or self._problem is None:
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

        native_solver = self._native_solver_name()
        if native_solver.is_failed():
            return native_solver  # type: ignore[return-value]
        solver_name = native_solver.unwrap()
        if solver_name is not None and self._active_columns:
            return self._extract_finite_bunch_solution(solver=solver_name)

        triad = self._native_triad(relaxation=False)
        if triad.is_failed():
            return _service_failure(triad.error)
        output = self._solver.solve(triad.unwrap())

        if output.status is SolverStatus.ERROR:
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=("束编组最终 MIP 求解失败 / Bunch final MIP solve failed"),
                )
            )

        if output.status is SolverStatus.INFEASIBLE:
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=("束编组最终 MIP 不可行 / Bunch final MIP is infeasible"),
                )
            )

        schedule = _build_schedule(
            problem=self._problem,
            active_columns=tuple(self._active_columns),
            values=output.values,
        )
        makespan = _compute_makespan(schedule)
        utilizations = self._compute_utilizations(
            schedule=schedule,
            makespan=makespan,
        )

        return Ok(
            GanttSolution(
                name=f"bunch_solution_{self._problem.name}",
                schedule=schedule,
                makespan=makespan,
                objective_value=output.objective,
                resource_utilizations=utilizations,
                is_optimal=(output.status is SolverStatus.OPTIMAL),
                iteration_count=self._iteration,
            )
        )

    def _extract_finite_bunch_solution(
        self,
        *,
        solver: str,
    ) -> Result[GanttSolution, str, Err[str]]:
        """在 Rust 有限活动模型上求解当前束列 / Solve current bunch columns on the Rust finite activity model.

        Args:
            solver: 显式原生后端名 / Explicit native backend name.

        Returns:
            调度方案或错误 / Scheduling solution or error.
        """
        problem = self._require_problem()
        if problem.is_failed():
            return problem  # type: ignore[return-value]
        registered = problem.unwrap()

        selected = self._finite_bunch_selection(solver=solver)
        if selected.is_failed():
            return _service_failure(selected.error)
        selection, report = selected.unwrap()

        if any(
            task.task_key
            not in {
                key
                for column in selection.columns
                for key, _ in column.task_assignments
            }
            for task in registered.tasks
        ):
            return _failure(
                ErrorCode.APPLICATION_ERROR,
                "选中束列未覆盖全部任务 / Selected bunch columns do not cover every task",
            )
        schedule = _schedule_from_bunch_columns(
            problem=registered,
            active_columns=selection.columns,
        )
        if schedule.is_failed():
            return _service_failure(schedule.error)
        entries = schedule.unwrap()
        makespan = _compute_makespan(entries)
        objective = Fraction(
            selection.cost[0],
            selection.cost[1],
        )
        return Ok(
            GanttSolution(
                name=f"bunch_solution_{registered.name}",
                schedule=entries,
                makespan=makespan,
                objective_value=float(objective),
                resource_utilizations=self._compute_utilizations(
                    schedule=entries,
                    makespan=makespan,
                ),
                is_optimal=(report.solution_presence == "OPTIMAL"),
                iteration_count=self._iteration,
            )
        )

    def _finite_bunch_selection(
        self,
        *,
        solver: str,
    ) -> Result[tuple[BunchSelection, SolveReport], str, Err[str]]:
        """在 Rust 有限活动模型上求解当前束列 / Solve current bunch columns on the Rust finite activity model.

        Args:
            solver: 显式原生后端名 / Explicit native backend name.

        Returns:
            选中列、原始报告或错误 / Selected columns, raw report or error.
        """
        problem = self._require_problem()
        if problem.is_failed():
            return problem  # type: ignore[return-value]
        registered = problem.unwrap()

        # 延迟导入避免 `_binding.gantt_bunch` 反向加载本包的循环 / Deferred to avoid a package cycle.
        from ospf_python._binding.gantt_bunch import solve_bunch_columns

        units = _bunch_column_units(registered)
        if units.is_failed():
            return _service_failure(units.error)
        resource_units, cost_unit = units.unwrap()

        solved = solve_bunch_columns(
            problem=registered,
            columns=tuple(self._active_columns),
            resource_units=resource_units,
            cost_unit=cost_unit,
            max_work=_BUNCH_COLUMN_MAX_WORK,
            solver=solver,
        )
        if solved.is_failed():
            return _service_failure(solved.error)
        output = solved.unwrap()
        report = output.report
        if report.problem_status == "INFEASIBLE":
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=("束列模型不可行 / Bunch-column model is infeasible"),
                )
            )
        if report.solution_presence == "NONE":
            return Failed(
                Err(
                    _code=ErrorCode.NO_SOLUTION,
                    _message=(
                        "束列模型没有可行解 / "
                        "Bunch-column model has no feasible solution"
                    ),
                )
            )
        if report.termination_reason != "COMPLETED":
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=(
                        f"束列求解未完成: {report.termination_reason} / "
                        f"Bunch-column solve did not complete: "
                        f"{report.termination_reason}"
                    ),
                )
            )
        if output.solution.is_failed():
            return _service_failure(output.solution.error)

        return Ok((output.solution.unwrap(), report))

    def extract_bunch_solutions(
        self,
    ) -> Result[tuple[BunchSolution, ...], str, Err[str]]:
        """提取束编组方案 / Extract bunch solutions.

        从求解器结果中读取变量值，构建束编组分配方案。

        Returns:
            束编组方案元组或错误 / Bunch solution tuple or error.
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

        native_solver = self._native_solver_name()
        if native_solver.is_failed():
            return native_solver  # type: ignore[return-value]
        solver_name = native_solver.unwrap()
        if solver_name is not None and self._active_columns:
            selected = self._finite_bunch_selection(solver=solver_name)
            if selected.is_failed():
                return _service_failure(selected.error)
            selection, _ = selected.unwrap()
            return Ok(
                tuple(
                    BunchSolution(
                        bunch_key=column.bunch_key,
                        bunch_assignments=tuple(
                            BunchAssignment(
                                task_key=task_key,
                                start_time=start_time,
                            )
                            for task_key, start_time in column.task_assignments
                        ),
                        total_cost=column.cost,
                        resource_key=column.resource_key,
                    )
                    for column in selection.columns
                )
            )

        triad = self._native_triad(relaxation=False)
        if triad.is_failed():
            return _service_failure(triad.error)
        output = self._solver.solve(triad.unwrap())

        if output.status is SolverStatus.ERROR:
            return Failed(
                Err(
                    _code=ErrorCode.SOLVE_FAILED,
                    _message=("束编组 MIP 求解失败 / Bunch MIP solve failed"),
                )
            )

        solutions: list[BunchSolution] = []
        for col in self._active_columns:
            var_name = f"bunch_{col.bunch_key}"
            var_val = output.values.get(var_name, 0.0)
            if var_val > 0.5:
                assignments = tuple(
                    BunchAssignment(
                        task_key=task_key,
                        start_time=start_time,
                    )
                    for task_key, start_time in col.task_assignments
                )
                solutions.append(
                    BunchSolution(
                        bunch_key=col.bunch_key,
                        bunch_assignments=assignments,
                        total_cost=col.cost,
                        resource_key=col.resource_key,
                    )
                )

        return Ok(tuple(solutions))

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
    def shadow_prices(self) -> dict[str, float]:
        """影子价格字典 / Shadow price dict."""
        return dict(self._shadow_prices)

    @property
    def active_columns(self) -> tuple[BunchColumn, ...]:
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

    def _native_solver_name(
        self,
    ) -> Result[str | None, str, Err[str]]:
        """读取并校验显式原生后端名 / Read and validate the explicit native backend.

        Returns:
            后端名、未配置时的 None 或错误 / Backend name, None when unset, or error.
        """
        native_solver = self._native_solver
        if native_solver is None:
            return Ok(None)
        if not isinstance(native_solver, str) or not native_solver.strip():
            return Failed(
                Err(
                    _code=ErrorCode.ILLEGAL_ARGUMENT,
                    _message=(
                        "原生求解后端名无效 / "
                        "Native solver name must be a non-blank string"
                    ),
                )
            )
        return Ok(native_solver)

    def _require_problem(
        self,
    ) -> Result[GanttProblem, str, Err[str]]:
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
        """从原生模型构建只读求解快照 / Build a read-only native solve snapshot.

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
        return _build_bunch_triad(
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
        new_bunches: tuple[BunchColumn, ...],
    ) -> Result[None, str, Err[str]]:
        """原子校验待添加束列 / Validate a bunch-column batch atomically.

        Args:
            new_bunches: 待添加束编组列 / Bunch columns to add.

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

        existing_keys = {column.bunch_key for column in self._active_columns}
        batch_keys: set[str] = set()
        for column in new_bunches:
            if (
                not isinstance(column.bunch_key, str)
                or not column.bunch_key
                or column.bunch_key in existing_keys
                or column.bunch_key in batch_keys
            ):
                return Failed(
                    Err(
                        _code=ErrorCode.ALREADY_EXIST,
                        _message=(
                            f"束编组列已存在或键为空: "
                            f"{column.bunch_key!r} / "
                            f"Bunch column already exists or has an empty "
                            f"key: {column.bunch_key!r}"
                        ),
                    )
                )
            batch_keys.add(column.bunch_key)

            if not math.isfinite(column.cost):
                return Failed(
                    Err(
                        _code=ErrorCode.ILLEGAL_ARGUMENT,
                        _message=(
                            f"束编组列成本必须有限: "
                            f"{column.bunch_key} / "
                            f"Bunch column cost must be finite: "
                            f"{column.bunch_key}"
                        ),
                    )
                )

            if not isinstance(column.resource_key, str) or not problem.has_resource(
                column.resource_key
            ):
                return Failed(
                    Err(
                        _code=ErrorCode.NOT_FOUND,
                        _message=(
                            f"束编组列引用了未知资源: "
                            f"{column.resource_key!r} / "
                            f"Bunch column references an unknown resource: "
                            f"{column.resource_key!r}"
                        ),
                    )
                )

            task_start_times: dict[str, float] = {}
            for task_key, start_time in column.task_assignments:
                task = problem.task_by_key(task_key)
                if task is None:
                    return Failed(
                        Err(
                            _code=GanttErrors.TASK_NOT_FOUND.value,  # type: ignore[arg-type]
                            _message=(
                                f"束编组列引用了未知任务: {task_key} / "
                                f"Bunch column references unknown task: "
                                f"{task_key}"
                            ),
                        )
                    )
                if not math.isfinite(start_time):
                    return Failed(
                        Err(
                            _code=ErrorCode.ILLEGAL_ARGUMENT,
                            _message=(
                                f"束编组列开始时间必须有限: "
                                f"{column.bunch_key} / "
                                f"Bunch column start time must be finite: "
                                f"{column.bunch_key}"
                            ),
                        )
                    )
                previous_start = task_start_times.setdefault(task_key, start_time)
                if not math.isclose(previous_start, start_time, abs_tol=1e-9):
                    return Failed(
                        Err(
                            _code=ErrorCode.ILLEGAL_ARGUMENT,
                            _message=(
                                f"同一束编组列内任务开始时间不一致: "
                                f"{task_key} / Bunch task start times differ "
                                f"within a column: {task_key}"
                            ),
                        )
                    )
                if start_time < task.earliest_start - 1e-9:
                    return Failed(
                        Err(
                            _code=ErrorCode.ILLEGAL_ARGUMENT,
                            _message=(
                                f"束编组列开始时间早于最早开始时间: "
                                f"{task_key} / Bunch column starts before "
                                f"earliest start: {task_key}"
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
                                f"束编组列结束时间晚于截止时间: "
                                f"{task_key} / Bunch column ends after "
                                f"deadline: {task_key}"
                            ),
                        )
                    )

        return Ok(None)

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

        # 与任务服务同一口径：used_capacity 是资源量，不是任务条数。
        # Same convention as the task service: used_capacity is a resource amount, not a count.
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


def _failure[T](
    code: ErrorCode,
    message: str,
) -> BindingResult[T]:
    """构造带原生来源的绑定失败 / Build a binding failure with native provenance.

    Args:
        code: 错误码 / Error code.
        message: 错误消息 / Error message.

    Returns:
        失败结果 / Failure result.
    """
    return Failed(
        ExErr(
            _code=code,
            _message=message,
            value=FailureContext(
                source="ospf-python",
                category=code.name,
                rust_code=None,
                error_class="DOMAIN_VALIDATION",
            ),
        )
    )


def _bunch_column_units(
    problem: GanttProblem,
) -> BindingResult[tuple[dict[str, Unit], Unit]]:
    """为束列模型创建共享的无量纲资源与成本单位 / Create shared dimensionless native units for the bunch-column model.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.

    Returns:
        资源键到单位的映射与成本单位或绑定失败 / Resource-unit map and cost unit, or a binding failure.
    """
    resource_unit = Unit.create(
        name="scheduling resource",
        symbol="scheduling resource",
        powers=(0,) * 10,
    )
    cost_unit = Unit.create(
        name="scheduling cost",
        symbol="scheduling cost",
        powers=(0,) * 10,
    )
    return resource_unit.flat_map(
        lambda units: cost_unit.map(
            lambda price_unit: (
                {resource.resource_key: units for resource in problem.resources},
                price_unit,
            )
        )
    )


def _schedule_from_bunch_columns(
    *,
    problem: GanttProblem,
    active_columns: tuple[BunchColumn, ...],
) -> BindingResult[tuple[TaskScheduleEntry, ...]]:
    """把选中束列映射为唯一调度表 / Map selected bunch columns to one schedule.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 已选中的束编组列 / Selected bunch columns.

    Returns:
        调度条目或重复覆盖失败 / Schedule entries or a duplicate-coverage failure.
    """
    task_schedule: dict[str, tuple[float, str]] = {}
    for column in active_columns:
        for task_key, start_time in column.task_assignments:
            previous = task_schedule.get(task_key)
            if previous is not None and previous != (start_time, column.resource_key):
                return _failure(
                    ErrorCode.APPLICATION_ERROR,
                    "任务被不同束列重复覆盖 / Task is covered by different bunch modes",
                )
            task_schedule[task_key] = (start_time, column.resource_key)

    return Ok(
        tuple(
            TaskScheduleEntry(
                task_key=task.task_key,
                start_time=task_schedule[task.task_key][0],
                end_time=task_schedule[task.task_key][0] + task.duration,
                assigned_resource=task_schedule[task.task_key][1],
            )
            for task in problem.tasks
            if task.task_key in task_schedule
        )
    )


def _build_triad_model(
    *,
    meta_model: MetaModel,
    active_columns: tuple[BunchColumn, ...],
    constraint_coeffs: tuple[BunchConstraintCoeff, ...],
    relaxation: bool,
) -> object:
    """构建线性三元组模型 / Build linear triad model.

    根据 MetaModel 和约束系数构建可求解的线性规划模型。
    Builds a solvable LP model from the MetaModel and
    constraint coefficients.

    Args:
        meta_model: 元模型 / Meta model.
        active_columns: 活跃束编组列 / Active bunch columns.
        constraint_coeffs: 约束系数 / Constraint coefficients.
        relaxation: 是否为 LP 松弛 / Whether LP relaxation.

    Returns:
        线性三元组模型 / Linear triad model.
    """
    from ospf_python.core.model.intermediate.linear_triad_model import (
        LinearTriadModel,
    )

    variables = list(meta_model.variables.keys())
    objective: dict[str, float] = {}
    constraints: dict[str, dict[str, float]] = {}
    rhs: dict[str, float] = {}
    sense: dict[str, str] = {}
    lower_bounds: dict[str, float] = {}
    upper_bounds: dict[str, float] = {}

    for var_name, var_data in meta_model.variables.items():
        if isinstance(var_data, dict):
            lower_bounds[var_name] = var_data.get("lb", 0.0)
            upper_bounds[var_name] = var_data.get(
                "ub",
                float("inf"),
            )
        else:
            lower_bounds[var_name] = 0.0
            upper_bounds[var_name] = 1.0

    for col in active_columns:
        var_name = f"bunch_{col.bunch_key}"
        objective[var_name] = col.cost

    for cname, cdata in meta_model.constraints.items():
        if isinstance(cdata, dict):
            constraints[cname] = {}
            rhs[cname] = cdata.get("rhs", 0.0)
            sense[cname] = cdata.get("sense", "<=")

    for cc in constraint_coeffs:
        if cc.constraint_name in constraints:
            current = constraints[cc.constraint_name].get(
                cc.variable_name,
                0.0,
            )
            constraints[cc.constraint_name][cc.variable_name] = current + cc.coefficient

    return LinearTriadModel(
        name=meta_model.name,
        variables=variables,
        constraints=constraints,
        objective=objective,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        rhs=rhs,
        sense=sense,
    )


def _build_schedule(
    *,
    problem: GanttProblem,
    active_columns: tuple[BunchColumn, ...],
    values: object,
) -> tuple[TaskScheduleEntry, ...]:
    """构建调度表 / Build schedule.

    从活跃的束编组列中提取每个任务的开始时间和分配资源。

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 活跃束编组列 / Active bunch columns.
        values: 求解器变量值 / Solver variable values.

    Returns:
        调度条目元组 / Schedule entry tuple.
    """
    task_schedule: dict[str, tuple[float, str]] = {}

    for col in active_columns:
        var_name = f"bunch_{col.bunch_key}"
        var_val = getattr(values, "get", lambda k, d=0.0: d)
        if var_val(var_name, 0.0) > 0.5:
            for task_key, start_time in col.task_assignments:
                if task_key not in task_schedule:
                    task_schedule[task_key] = (
                        start_time,
                        col.resource_key,
                    )

    entries: list[TaskScheduleEntry] = []
    for task in problem.tasks:
        if task.task_key in task_schedule:
            start, res_key = task_schedule[task.task_key]
            entries.append(
                TaskScheduleEntry(
                    task_key=task.task_key,
                    start_time=start,
                    end_time=start + task.duration,
                    assigned_resource=res_key,
                )
            )
        else:
            entries.append(
                TaskScheduleEntry(
                    task_key=task.task_key,
                    start_time=0.0,
                    end_time=task.duration,
                    assigned_resource="",
                )
            )

    return tuple(entries)


def _discretize_windows(
    *,
    problem: GanttProblem,
    resource_key: str,
) -> tuple[tuple[float, float], ...]:
    """离散化时间窗口 / Discretize time windows.

    根据任务的开始和结束时间点将时间轴离散化。

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        resource_key: 资源键 / Resource key.

    Returns:
        时间窗口元组 / Time window tuple.
    """
    points: set[float] = set()
    # 本函数对**每个资源**调用一次，所以常数因子被「资源数 × 任务数」放大。
    # 内联需求扫描取代 `task.requires_resource(...)`（后者每次新建生成器表达式），
    # 并把同一任务的时序属性各只读一次。语义相同。
    # Runs once per resource: inline the requirement scan and read each timing attribute once.
    infinite = float("inf")
    for task in problem.tasks:
        required = False
        for requirement_key, _amount in task.resource_requirements:
            if requirement_key == resource_key:
                required = True
                break
        if not required:
            continue
        earliest_start = task.earliest_start
        duration = task.duration
        points.add(earliest_start)
        points.add(earliest_start + duration)
        deadline = task.deadline
        if deadline < infinite:
            points.add(deadline)

    if not points:
        return ()

    sorted_points = sorted(points)
    windows: list[tuple[float, float]] = []
    for i in range(len(sorted_points) - 1):
        ws, we = sorted_points[i], sorted_points[i + 1]
        if we > ws:
            windows.append((ws, we))

    return tuple(windows)


def _capacity_coeff(
    *,
    problem: GanttProblem | None,
    start_time: float,
    task_key: str,
    window_start: float,
    window_end: float,
) -> float:
    """计算容量约束系数 / Compute capacity constraint coefficient.

    如果任务在窗口内占用资源则返回 1.0，否则 0.0。

    Args:
        problem: 甘特问题 / Gantt problem.
        start_time: 任务开始时间 / Task start time.
        task_key: 任务键 / Task key.
        window_start: 窗口起始 / Window start.
        window_end: 窗口结束 / Window end.

    Returns:
        系数值 / Coefficient value.
    """
    if problem is None:
        return 0.0
    task = problem.task_by_key(task_key)
    if task is None:
        return 0.0
    task_end = start_time + task.duration
    if start_time < window_end and task_end > window_start:
        return 1.0
    return 0.0


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
