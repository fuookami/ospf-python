"""甘特调度束编组应用服务 / Gantt scheduling bunch application service.

实现 BranchAndPrice 列生成编排，管理束编组的完整列生成生命周期：
注册 -> 增列 -> 删列 -> 刷新影子价格 -> 终止 -> 提取解。
Implements BranchAndPrice column generation orchestration for
bunches, managing the full column generation lifecycle: register
-> add_columns -> remove_columns -> refresh_shadow_price ->
finalize -> extract_solution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.core.model.basic.registration_status import (
    RegistrationStatus,
)
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.output.solver_status import SolverStatus
from ospf_python.framework.gantt_scheduling.application.model.bunch.bunch_solution import (
    BunchAssignment,
    BunchSolution,
)
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    GanttSolution,
    TaskScheduleEntry,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
    BunchColumn,
    BunchConstraintCoeff,
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
    from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
        BunchGenerationContext,
    )
    from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
        ResourceContext,
    )
    from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
        TaskContext,
    )


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
        bunch_context: BunchGenerationContext,
        max_iterations: int = 100,
    ) -> None:
        """初始化束编组应用服务 / Initialize bunch application service.

        Args:
            solver: 求解器实例 / Solver instance.
            task_context: 任务上下文 / Task context.
            resource_context: 资源上下文 / Resource context.
            bunch_context: 束编组上下文 / Bunch context.
            max_iterations: 最大迭代次数 / Maximum iterations.
        """
        self._solver = solver
        self._task_context = task_context
        self._resource_context = resource_context
        self._bunch_context = bunch_context
        self._max_iterations = max_iterations
        self._meta_model: MetaModel | None = None
        self._iteration: int = 0
        self._converged: bool = False
        self._shadow_prices: dict[str, float] = {}
        self._active_columns: list[BunchColumn] = []
        self._constraint_coeffs: list[BunchConstraintCoeff] = []
        self._problem: GanttProblem | None = None

    # ==================== 生命周期 / Lifecycle =====================

    def register(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册问题变量和约束 / Register problem variables and constraints.

        创建 MetaModel，注册束编组变量、资源容量约束
        和优先关系约束，设置最小化完工时间目标。

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.

        Returns:
            注册结果 / Registration result.
        """
        validation = problem.validate()
        if validation.is_failed():
            return validation

        self._problem = problem
        self._meta_model = MetaModel(
            name=f"bunch_cg_{problem.name}",
        )
        self._active_columns.clear()
        self._constraint_coeffs.clear()
        self._shadow_prices.clear()
        self._iteration = 0
        self._converged = False

        for step in (
            self._register_bunch_variables,
            self._register_capacity_constraints,
            self._register_precedence_constraints,
            self._register_demand_constraints,
            self._register_objective,
        ):
            result = step(problem)
            if result.is_failed():
                return result

        return Ok(None)

    def add_columns(
        self,
        new_bunches: tuple[BunchColumn, ...],
    ) -> Result[None, str, Err[str]]:
        """新增束编组列 / Add new bunch columns.

        向模型中追加新生成的束编组列变量，更新约束系数。

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

        meta_model = model.unwrap()

        for column in new_bunches:
            var_name = f"bunch_{column.bunch_key}"
            status = meta_model.register_variable(
                name=var_name,
                variable=column,
            )
            if status is RegistrationStatus.ALREADY_EXISTS:
                return Failed(
                    Err(
                        _code=ErrorCode.ALREADY_EXIST,
                        _message=(
                            f"束编组列已存在: {column.bunch_key} / "
                            f"Bunch column already exists: "
                            f"{column.bunch_key}"
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
        bunch_keys: tuple[str, ...],
    ) -> Result[None, str, Err[str]]:
        """移除束编组列 / Remove bunch columns.

        从模型中移除不再需要的束编组列变量和相关约束系数。

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

        meta_model = model.unwrap()
        key_set = set(bunch_keys)
        removed_vars: set[str] = set()

        for key in key_set:
            var_name = f"bunch_{key}"
            if var_name in meta_model.variables:
                del meta_model.variables[var_name]
                removed_vars.add(var_name)

        self._constraint_coeffs = [
            cc for cc in self._constraint_coeffs if cc.variable_name not in removed_vars
        ]
        self._active_columns = [
            c for c in self._active_columns if c.bunch_key not in key_set
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

        triad = _build_triad_model(
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

        self._shadow_prices = _extract_shadow_prices(
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

        Returns:
            调度方案或错误 / Scheduling solution or error.
        """
        if self._meta_model is None or self._problem is None:
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

        triad = _build_triad_model(
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

    def extract_bunch_solutions(
        self,
    ) -> Result[tuple[BunchSolution, ...], str, Err[str]]:
        """提取束编组方案 / Extract bunch solutions.

        从求解器结果中读取变量值，构建束编组分配方案。

        Returns:
            束编组方案元组或错误 / Bunch solution tuple or error.
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

        triad = _build_triad_model(
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

    def _register_bunch_variables(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册束编组变量 / Register bunch variables.

        为每个任务注册开始时间连续变量。

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
                        _code=(
                            GanttErrors.TASK_NOT_FOUND.value  # type: ignore[arg-type]
                        ),
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

    def _register_demand_constraints(
        self,
        problem: GanttProblem,
    ) -> Result[None, str, Err[str]]:
        """注册需求覆盖约束 / Register demand coverage constraints.

        确保每个任务至少被一个束编组列覆盖。
        Ensures each task is covered by at least one bunch column.

        Args:
            problem: 甘特调度问题 / Gantt scheduling problem.

        Returns:
            注册结果 / Registration result.
        """
        model = self._meta_model
        assert model is not None

        for task in problem.tasks:
            cname = f"demand_{task.task_key}"
            model.register_constraint(
                name=cname,
                constraint={
                    "type": "demand",
                    "task_key": task.task_key,
                    "rhs": 1.0,
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
            name="minimize_bunch_cost",
            objective={
                "type": "minimize",
                "sense": "min",
            },
        )
        return Ok(None)

    def _update_constraints_for_column(
        self,
        *,
        column: BunchColumn,
        meta_model: MetaModel,
    ) -> None:
        """为新列更新约束系数 / Update constraint coefficients for a column.

        Args:
            column: 束编组列 / Bunch column.
            meta_model: 元模型 / Meta model.
        """
        var_name = f"bunch_{column.bunch_key}"

        for task_key, start_time in column.task_assignments:
            for cname, cdata in meta_model.constraints.items():
                if not isinstance(cdata, dict):
                    continue
                ctype = cdata.get("type", "")

                if ctype == "capacity":
                    if cdata.get("resource_key") == column.resource_key:
                        coeff = _capacity_coeff(
                            problem=self._problem,
                            start_time=start_time,
                            task_key=task_key,
                            window_start=cdata["window_start"],
                            window_end=cdata["window_end"],
                        )
                        if coeff > 0.0:
                            self._constraint_coeffs.append(
                                BunchConstraintCoeff(
                                    constraint_name=cname,
                                    variable_name=var_name,
                                    coefficient=coeff,
                                )
                            )

                elif ctype == "precedence" and task_key == cdata.get("predecessor_key"):
                    self._constraint_coeffs.append(
                        BunchConstraintCoeff(
                            constraint_name=cname,
                            variable_name=var_name,
                            coefficient=start_time,
                        )
                    )

                elif ctype == "demand" and task_key == cdata.get("task_key"):
                    self._constraint_coeffs.append(
                        BunchConstraintCoeff(
                            constraint_name=cname,
                            variable_name=var_name,
                            coefficient=1.0,
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


def _extract_shadow_prices(
    *,
    meta_model: MetaModel,
    constraint_coeffs: tuple[BunchConstraintCoeff, ...],
    values: object,
) -> dict[str, float]:
    """提取影子价格 / Extract shadow prices.

    从求解器输出推断约束的影子价格。
    当约束紧致（松弛为 0）时记为 1.0。
    Infers shadow prices from solver output. Records 1.0
    when a constraint is tight (zero slack).

    Args:
        meta_model: 元模型 / Meta model.
        constraint_coeffs: 约束系数 / Constraint coefficients.
        values: 求解器变量值 / Solver variable values.

    Returns:
        影子价格字典 / Shadow price dict.
    """
    prices: dict[str, float] = {}

    for cname, cdata in meta_model.constraints.items():
        if not isinstance(cdata, dict):
            continue

        lhs = 0.0
        for cc in constraint_coeffs:
            if cc.constraint_name == cname:
                var_val = getattr(values, "get", lambda k, d=0.0: d)
                lhs += cc.coefficient * var_val(
                    cc.variable_name,
                    0.0,
                )

        rhs_val = cdata.get("rhs", 0.0)
        cdata_sense = cdata.get("sense", "<=")

        if cdata_sense == "<=":
            slack = rhs_val - lhs
        elif cdata_sense == ">=":
            slack = lhs - rhs_val
        else:
            slack = abs(lhs - rhs_val)

        prices[cname] = 1.0 if slack < 1e-6 else 0.0

    return prices


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
