"""甘特调度任务应用服务 / Gantt scheduling task application service.

实现 BranchAndPrice 列生成编排，管理完整的列生成生命周期：
注册 -> 增列 -> 删列 -> 刷新影子价格 -> 终止 -> 提取解。
Implements BranchAndPrice column generation orchestration,
managing the full column generation lifecycle: register ->
add_columns -> remove_columns -> refresh_shadow_price ->
finalize -> extract_solution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.core.model.basic.registration_status import (
    RegistrationStatus,
)
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.output.solver_status import SolverStatus
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    GanttSolution,
    TaskScheduleEntry,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    ConstraintCoeff,
    TaskColumn,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_model_builder import (
    build_schedule,
    build_triad_model,
    extract_shadow_prices,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_utilization import (
    ResourceUtilization,
)
from ospf_python.framework.gantt_scheduling.domain.task.error.gantt_errors import (
    GanttErrors,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.core.solver.solver import Solver
    from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
        GanttProblem,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
        ResourceContext,
    )
    from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
        TaskContext,
    )


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
        _meta_model: 元模型 / Meta model.
        _iteration: 当前迭代次数 / Current iteration count.
        _max_iterations: 最大迭代次数 / Maximum iterations.
        _converged: 是否已收敛 / Whether converged.
        _shadow_prices: 影子价格字典 / Shadow price dict.
        _active_columns: 活跃列列表 / Active column list.
        _constraint_coeffs: 约束系数缓存 / Constraint coeff cache.
        _problem: 已注册的问题 / Registered problem.
    """

    def __init__(
        self,
        *,
        solver: Solver,
        task_context: TaskContext,
        resource_context: ResourceContext,
        max_iterations: int = 100,
    ) -> None:
        """初始化任务应用服务 / Initialize task application service.

        Args:
            solver: 求解器实例 / Solver instance.
            task_context: 任务上下文 / Task context.
            resource_context: 资源上下文 / Resource context.
            max_iterations: 最大迭代次数 / Maximum iterations.
        """
        self._solver = solver
        self._task_context = task_context
        self._resource_context = resource_context
        self._max_iterations = max_iterations
        self._meta_model: MetaModel | None = None
        self._iteration: int = 0
        self._converged: bool = False
        self._shadow_prices: dict[str, float] = {}
        self._active_columns: list[TaskColumn] = []
        self._constraint_coeffs: list[ConstraintCoeff] = []
        self._problem: GanttProblem | None = None

    # ==================== 生命周期 / Lifecycle =====================

    def register(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册问题变量和约束 / Register problem variables and constraints.

        创建 MetaModel，注册任务变量（开始时间、分配变量）、
        资源容量约束和优先关系约束，设置最小化完工时间目标。

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.

        Returns:
            注册结果 / Registration result.
        """
        validation = problem.validate()
        if validation.is_failed():
            return validation  # type: ignore[return-value]

        self._problem = problem
        self._meta_model = MetaModel(name=f"cg_{problem.name}")
        self._active_columns.clear()
        self._constraint_coeffs.clear()
        self._shadow_prices.clear()
        self._iteration = 0
        self._converged = False

        for step in (
            self._register_task_variables,
            self._register_capacity_constraints,
            self._register_precedence_constraints,
            self._register_objective,
        ):
            result = step(problem)
            if result.is_failed():
                return result

        return Ok(None)

    def add_columns(
        self,
        new_columns: tuple[TaskColumn, ...],
    ) -> Result[None, str, Err[str]]:
        """新增调度列 / Add new scheduling columns.

        向模型中追加新生成的列变量，更新约束系数。

        Args:
            new_columns: 待添加的列 / Columns to add.

        Returns:
            操作结果 / Operation result.
        """
        if not new_columns:
            return Ok(None)

        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]

        meta_model = model.unwrap()

        for column in new_columns:
            var_name = f"col_{column.column_key}"
            status = meta_model.register_variable(
                name=var_name,
                variable=column,
            )
            if status is RegistrationStatus.ALREADY_EXISTS:
                return Failed(
                    Err(
                        _code=ErrorCode.ALREADY_EXIST,
                        _message=(
                            f"列已存在: {column.column_key} / "
                            f"Column already exists: "
                            f"{column.column_key}"
                        ),
                    )
                )
            self._update_constraints_for_column(
                column=column,
                meta_model=meta_model,
            )
            self._active_columns.append(column)

        return Ok(None)

    def remove_columns(
        self,
        column_keys: tuple[str, ...],
    ) -> Result[None, str, Err[str]]:
        """移除调度列 / Remove scheduling columns.

        从模型中移除不再需要的列变量和相关约束系数。

        Args:
            column_keys: 待移除的列键 / Column keys to remove.

        Returns:
            操作结果 / Operation result.
        """
        if not column_keys:
            return Ok(None)

        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]

        meta_model = model.unwrap()
        key_set = set(column_keys)
        removed_vars: set[str] = set()

        for key in key_set:
            var_name = f"col_{key}"
            if var_name in meta_model.variables:
                del meta_model.variables[var_name]
                removed_vars.add(var_name)

        self._constraint_coeffs = [
            cc for cc in self._constraint_coeffs if cc.variable_name not in removed_vars
        ]
        self._active_columns = [
            c for c in self._active_columns if c.column_key not in key_set
        ]

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
        model = self._require_model()
        if model.is_failed():
            return model  # type: ignore[return-value]

        meta_model = model.unwrap()

        triad = build_triad_model(
            meta_model=meta_model,
            active_columns=tuple(self._active_columns),
            constraint_coeffs=tuple(self._constraint_coeffs),
            relaxation=True,
        )
        output = self._solver.solve(triad)

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

        self._shadow_prices = extract_shadow_prices(
            meta_model=meta_model,
            constraint_coeffs=tuple(self._constraint_coeffs),
            values=output.values,
        )
        self._iteration += 1

        if self._iteration >= self._max_iterations:
            self._converged = True

        return Ok(dict(self._shadow_prices))

    def finalize(self) -> Result[None, str, Err[str]]:
        """终止列生成 / Finalize column generation.

        将分配变量设为整数约束，求解最终 MIP。

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

        Returns:
            调度方案或错误 / Scheduling solution or error.
        """
        if self._meta_model is None or self._problem is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_INITIALIZED,
                    _message=(
                        "模型未注册，请先调用 register / "
                        "Model not registered, call register first"
                    ),
                )
            )

        triad = build_triad_model(
            meta_model=self._meta_model,
            active_columns=tuple(self._active_columns),
            constraint_coeffs=tuple(self._constraint_coeffs),
            relaxation=False,
        )
        output = self._solver.solve(triad)

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
    ) -> Result[MetaModel, str, Err[str]]:
        """获取已注册的元模型 / Get registered meta model.

        Returns:
            元模型或错误 / Meta model or error.
        """
        if self._meta_model is None:
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
        return Ok(self._meta_model)

    def _register_task_variables(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册任务变量 / Register task variables.

        为每个任务注册开始时间和分配二值变量。

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.

        Returns:
            注册结果 / Registration result.
        """
        model = self._meta_model
        assert model is not None

        for task in problem.tasks:
            start_var = f"start_{task.task_key}"
            status = model.register_variable(
                name=start_var,
                variable={
                    "type": "continuous",
                    "lb": task.earliest_start,
                    "ub": task.latest_start,
                },
            )
            if status is not RegistrationStatus.REGISTERED:
                return Failed(
                    Err(
                        _code=ErrorCode.ALREADY_EXIST,
                        _message=(
                            f"变量已存在: {start_var} / "
                            f"Variable already exists: "
                            f"{start_var}"
                        ),
                    )
                )

            for res_key, _ in task.resource_requirements:
                assign_var = f"assign_{task.task_key}_{res_key}"
                model.register_variable(
                    name=assign_var,
                    variable={
                        "type": "binary",
                        "task_key": task.task_key,
                        "resource_key": res_key,
                    },
                )

        return Ok(None)

    def _register_capacity_constraints(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册资源容量约束 / Register resource capacity constraints.

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.

        Returns:
            注册结果 / Registration result.
        """
        model = self._meta_model
        assert model is not None

        for resource in problem.resources:
            windows = _discretize_windows(
                problem=problem,
                resource_key=resource.resource_key,
            )
            for ws, we in windows:
                cname = f"cap_{resource.resource_key}_{ws:.0f}_{we:.0f}"
                model.register_constraint(
                    name=cname,
                    constraint={
                        "type": "capacity",
                        "resource_key": resource.resource_key,
                        "window_start": ws,
                        "window_end": we,
                        "rhs": resource.capacity,
                        "sense": "<=",
                    },
                )

        return Ok(None)

    def _register_precedence_constraints(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册优先关系约束 / Register precedence constraints.

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.

        Returns:
            注册结果 / Registration result.
        """
        model = self._meta_model
        assert model is not None

        for rel in problem.precedence_relations:
            pred = problem.task_by_key(rel.predecessor_key)
            succ = problem.task_by_key(rel.successor_key)
            if pred is None or succ is None:
                return Failed(
                    Err(
                        _code=GanttErrors.TASK_NOT_FOUND.value,  # type: ignore[arg-type]
                        _message=(
                            f"优先关系中任务未找到: "
                            f"{rel.predecessor_key} -> "
                            f"{rel.successor_key} / "
                            f"Task not found in precedence: "
                            f"{rel.predecessor_key} -> "
                            f"{rel.successor_key}"
                        ),
                    )
                )

            cname = f"prec_{rel.predecessor_key}_{rel.successor_key}"
            model.register_constraint(
                name=cname,
                constraint={
                    "type": "precedence",
                    "predecessor_key": rel.predecessor_key,
                    "successor_key": rel.successor_key,
                    "min_gap": pred.duration + rel.min_gap,
                    "sense": ">=",
                },
            )

        return Ok(None)

    def _register_objective(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册目标函数 / Register objective function.

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.

        Returns:
            注册结果 / Registration result.
        """
        model = self._meta_model
        assert model is not None

        model.register_objective(
            name="minimize_makespan",
            objective={
                "type": "minimize",
                "sense": "min",
            },
        )
        return Ok(None)

    def _update_constraints_for_column(
        self,
        *,
        column: TaskColumn,
        meta_model: MetaModel,
    ) -> None:
        """为新列更新约束系数 / Update constraint coefficients for a column.

        Args:
            column: 调度列 / Scheduling column.
            meta_model: 元模型 / Meta model.
        """
        var_name = f"col_{column.column_key}"

        for task_key, res_key, start_time in column.task_assignments:
            for cname, cdata in meta_model.constraints.items():
                if not isinstance(cdata, dict):
                    continue
                ctype = cdata.get("type", "")

                if ctype == "capacity":
                    if cdata.get("resource_key") == res_key:
                        coeff = _capacity_coeff(
                            problem=self._problem,
                            start_time=start_time,
                            task_key=task_key,
                            window_start=cdata["window_start"],
                            window_end=cdata["window_end"],
                        )
                        if coeff > 0.0:
                            self._constraint_coeffs.append(
                                ConstraintCoeff(
                                    constraint_name=cname,
                                    variable_name=var_name,
                                    coefficient=coeff,
                                )
                            )

                elif ctype == "precedence" and task_key == cdata.get("predecessor_key"):
                    self._constraint_coeffs.append(
                        ConstraintCoeff(
                            constraint_name=cname,
                            variable_name=var_name,
                            coefficient=start_time,
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

        utilizations: list[ResourceUtilization] = []
        for resource in self._problem.resources:
            used = sum(
                1.0
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
    for task in problem.tasks:
        if task.requires_resource(resource_key):
            points.add(task.earliest_start)
            points.add(task.earliest_start + task.duration)
            if task.deadline < float("inf"):
                points.add(task.deadline)

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
