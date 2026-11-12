"""模型构建辅助器 / Model builder helper.

封装列生成中模型构建、影子价格提取和解构建逻辑。
Encapsulates model building, shadow price extraction, and
solution construction logic for column generation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TYPE_CHECKING

from ospf_python._binding.gantt_task import (
    extract_shadow_prices as _extract_native_task_shadow_prices,
)
from ospf_python._binding.model import (
    ConstraintSpec,
    LinearTriadExport,
    LinearVariableExport,
    MetaModelFloat64,
    VariableSpec,
)
from ospf_python._binding.result import BindingResult, invalid
from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    TaskScheduleEntry,
)
from ospf_python.utils.functional.result import Ok

if TYPE_CHECKING:
    from ospf_python.core.model.mechanism.meta_model import MetaModel
    from ospf_python.core.solver.value.solve_value import SolveValue
    from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
        GanttProblem,
    )
    from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
        ConstraintCoeff,
        TaskColumn,
    )

_EVENT_DECIMALS = 12


def _build_native_task_model(
    *,
    problem: GanttProblem,
    active_columns: tuple[TaskColumn, ...],
    window_columns: tuple[TaskColumn, ...] | None = None,
) -> BindingResult[MetaModelFloat64]:
    """在 Rust 所有者中构建任务模型 / Build the task model on the Rust owner.

    模型结构只写入原生 `MetaModelFloat64`。全部输入注册成功后才返回模型；
    任一失败都会关闭临时模型，不发布半成品状态。
    The structure is written only to the native `MetaModelFloat64`. A model is
    returned only after every input is registered; any failure closes the
    temporary model instead of publishing partial state.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 活跃列 / Active columns.
        window_columns: 固定容量窗口事件集的列；省略时等于活跃列 /
            Columns defining the fixed capacity-window event set; defaults to
            active columns.

    Returns:
        原生模型或绑定失败 / Native model or binding failure.
    """
    created = MetaModelFloat64.create(f"cg_{problem.name}")
    if created.is_failed():
        return created
    model = created.unwrap()

    variable_specs = _task_variable_specs(
        problem=problem,
        active_columns=active_columns,
    )
    variables = model.add_variables(variable_specs)
    if variables.is_failed():
        _close_model(model)
        return variables

    handles = dict(
        zip(
            (spec.name for spec in variable_specs),
            variables.unwrap(),
            strict=True,
        )
    )
    constraints, rhs, senses = _task_constraint_structure(
        problem=problem,
        active_columns=active_columns,
        window_columns=(active_columns if window_columns is None else window_columns),
    )
    constraints_result = model.add_constraints(
        [
            ConstraintSpec(
                name=name,
                terms=[
                    (handles[variable_name], coefficient)
                    for variable_name, coefficient in terms.items()
                ],
                relation=senses[name],
                rhs=rhs[name],
            )
            for name, terms in constraints.items()
        ]
    )
    if constraints_result.is_failed():
        _close_model(model)
        return constraints_result

    objective_terms = [(handles["makespan"], 1.0)]
    objective_terms.extend(
        (handles[f"col_{column.column_key}"], column.cost) for column in active_columns
    )
    objective = model.set_objective(
        terms=objective_terms,
        sense="minimize",
        name="minimize_makespan",
    )
    if objective.is_failed():
        _close_model(model)
        return objective
    return Ok(model)


def _task_variable_specs(
    *,
    problem: GanttProblem,
    active_columns: tuple[TaskColumn, ...],
) -> list[VariableSpec]:
    """构建任务变量输入 / Build task-variable inputs.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 活跃列 / Active columns.

    Returns:
        变量输入快照 / Variable input snapshots.
    """
    specs: list[VariableSpec] = []
    for task in problem.tasks:
        latest_start = task.latest_start
        specs.append(
            VariableSpec(
                name=f"start_{task.task_key}",
                kind="continuous",
                lower=task.earliest_start,
                upper=latest_start if math.isfinite(latest_start) else None,
            )
        )
        specs.extend(
            VariableSpec(
                name=f"assign_{task.task_key}_{resource_key}",
                kind="binary",
            )
            for resource_key in task.resource_keys
        )
    specs.append(VariableSpec(name="makespan", kind="continuous", lower=0.0))
    specs.extend(
        VariableSpec(
            name=f"col_{column.column_key}",
            kind="binary",
        )
        for column in active_columns
    )
    return specs


def _task_constraint_structure(
    *,
    problem: GanttProblem,
    active_columns: tuple[TaskColumn, ...],
    window_columns: tuple[TaskColumn, ...] | None = None,
) -> tuple[dict[str, dict[str, float]], dict[str, float], dict[str, str]]:
    """构建完整任务约束结构 / Build the complete task-row structure.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 活跃列 / Active columns.
        window_columns: 容量窗口事件集 / Capacity-window event columns.

    Returns:
        约束系数、右端项和方向 / Constraint coefficients, RHS and senses.
    """
    terms: dict[str, dict[str, float]] = {}
    rhs: dict[str, float] = {}
    senses: dict[str, str] = {}
    task_indices = {task.task_key: index for index, task in enumerate(problem.tasks)}

    for index, _task in enumerate(problem.tasks):
        name = f"task_compilation_{index}"
        terms[name] = {}
        rhs[name] = 1.0
        senses[name] = "=="

    capacity_windows: dict[str, tuple[str, float, float]] = {}
    for resource in problem.resources:
        for window_start, window_end in _discretize_windows(
            problem=problem,
            resource_key=resource.resource_key,
            active_columns=(
                active_columns if window_columns is None else window_columns
            ),
        ):
            name = f"cap_{resource.resource_key}_{window_start:g}_{window_end:g}"
            capacity_windows[name] = (
                resource.resource_key,
                window_start,
                window_end,
            )
            terms[name] = {}
            rhs[name] = resource.capacity
            senses[name] = "<="

    for relation in problem.precedence_relations:
        predecessor = problem.task_by_key(relation.predecessor_key)
        if predecessor is None:
            continue
        name = f"prec_{relation.predecessor_key}_{relation.successor_key}"
        terms[name] = {
            f"start_{relation.successor_key}": 1.0,
            f"start_{relation.predecessor_key}": -1.0,
        }
        rhs[name] = predecessor.duration + relation.min_gap
        senses[name] = ">="

    for index, task in enumerate(problem.tasks):
        name = f"makespan_task_{index}"
        terms[name] = {
            "makespan": 1.0,
            f"start_{task.task_key}": -1.0,
        }
        rhs[name] = task.duration
        senses[name] = ">="

    for task in problem.tasks:
        start_link = f"start_link_{task.task_key}"
        terms[start_link] = {f"start_{task.task_key}": 1.0}
        rhs[start_link] = 0.0
        senses[start_link] = "=="
        for resource_key in task.resource_keys:
            assign_link = f"assign_link_{task.task_key}_{resource_key}"
            terms[assign_link] = {f"assign_{task.task_key}_{resource_key}": 1.0}
            rhs[assign_link] = 0.0
            senses[assign_link] = "=="

    for column in active_columns:
        variable_name = f"col_{column.column_key}"
        seen_tasks: set[str] = set()
        for task_key, resource_key, start_time in column.task_assignments:
            task_index = task_indices.get(task_key)
            if task_index is None:
                continue
            if task_key not in seen_tasks:
                seen_tasks.add(task_key)
                terms[f"task_compilation_{task_index}"][variable_name] = 1.0
                if start_time != 0.0:
                    terms[f"start_link_{task_key}"][variable_name] = -start_time

            assign_link = f"assign_link_{task_key}_{resource_key}"
            if assign_link in terms:
                terms[assign_link][variable_name] = -1.0

            for name, (
                capacity_resource,
                window_start,
                window_end,
            ) in capacity_windows.items():
                if capacity_resource != resource_key:
                    continue
                coefficient = _capacity_coeff(
                    problem=problem,
                    start_time=start_time,
                    task_key=task_key,
                    resource_key=resource_key,
                    window_start=window_start,
                    window_end=window_end,
                )
                if coefficient > 0.0:
                    terms[name][variable_name] = (
                        terms[name].get(variable_name, 0.0) + coefficient
                    )

    return terms, rhs, senses


def _task_column_coefficients(
    *,
    problem: GanttProblem,
    column: TaskColumn,
    window_columns: tuple[TaskColumn, ...],
) -> dict[str, float]:
    """读取候选列在固定行结构中的系数 / Read candidate coefficients in the fixed row structure.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        column: 候选列 / Candidate column.
        window_columns: 固定容量窗口事件集的列 / Columns defining the fixed
            capacity-window event set.

    Returns:
        行名到候选变量系数 / Row names mapped to candidate-variable coefficients.
    """
    terms, _, _ = _task_constraint_structure(
        problem=problem,
        active_columns=(column,),
        window_columns=window_columns,
    )
    variable_name = f"col_{column.column_key}"
    return {
        name: coefficients[variable_name]
        for name, coefficients in terms.items()
        if variable_name in coefficients
    }


def _build_triad_from_export(
    *,
    exported: LinearTriadExport,
    relaxation: bool,
) -> BindingResult[LinearTriadModel]:
    """从原生快照物化求解三元组 / Materialize a solver triad from native state.

    Args:
        exported: 原生线性结构快照 / Native linear-structure snapshot.
        relaxation: 是否取消整数性但保留边界 / Whether to relax integrality
            while preserving bounds.

    Returns:
        独立三元组或合同失败 / Detached triad or contract failure.
    """
    if exported.sense != "minimize":
        return invalid(
            f"原生模型必须最小化 / Native model must minimize: {exported.sense}"
        )
    if exported.constant != 0.0:
        return invalid(
            "原生模型目标常数必须为零 / Native objective constant must be zero: "
            f"{exported.constant}"
        )

    variables: list[str] = []
    lower_bounds: dict[str, float] = {}
    upper_bounds: dict[str, float] = {}
    variable_types: dict[str, str] = {}
    for variable in exported.variables:
        if variable.name in variable_types:
            return invalid(
                f"原生变量名重复 / Duplicate native variable name: {variable.name}"
            )
        if variable.kind not in {"continuous", "integer", "binary"}:
            return invalid(
                "不支持的原生变量类型 / Unsupported native variable kind: "
                f"{variable.kind}"
            )
        variables.append(variable.name)
        lower_bounds[variable.name] = 0.0 if variable.lower is None else variable.lower
        upper_bounds[variable.name] = _exported_upper_bound(variable)
        variable_types[variable.name] = "continuous" if relaxation else variable.kind

    constraints: dict[str, dict[str, float]] = {}
    rhs: dict[str, float] = {}
    senses: dict[str, str] = {}
    known_variables = set(variables)
    for row in exported.rows:
        if row.name in constraints:
            return invalid(
                f"原生约束名重复 / Duplicate native constraint name: {row.name}"
            )
        if row.relation not in {"<=", ">=", "=="}:
            return invalid(
                f"不支持的约束方向 / Unsupported row relation: {row.relation}"
            )
        unknown = set(row.coefficients) - known_variables
        if unknown:
            return invalid(
                "约束引用未知变量 / Constraint references unknown variables: "
                + ", ".join(sorted(unknown))
            )
        constraints[row.name] = dict(row.coefficients)
        rhs[row.name] = row.rhs
        senses[row.name] = row.relation

    unknown_objective = set(exported.objective) - known_variables
    if unknown_objective:
        return invalid(
            "目标引用未知变量 / Objective references unknown variables: "
            + ", ".join(sorted(unknown_objective))
        )

    return Ok(
        LinearTriadModel(
            name=exported.name,
            variables=variables,
            constraints=constraints,
            objective=dict(exported.objective),
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds,
            rhs=rhs,
            sense=senses,
            variable_types=variable_types,
        )
    )


def _exported_upper_bound(variable: LinearVariableExport) -> float:
    """按变量类型解释原生空上界 / Interpret an empty native upper bound.

    Args:
        variable: 原生变量快照 / Native variable snapshot.

    Returns:
        物化上界 / Materialized upper bound.
    """
    if variable.upper is not None:
        return variable.upper
    return 1.0 if variable.kind == "binary" else float("inf")


def _close_model(model: MetaModelFloat64) -> None:
    """关闭临时原生模型并保留主错误 / Close a temporary model, preserving the primary error.

    Args:
        model: 待关闭模型 / Model to close.
    """
    model.close()


def _discretize_windows(
    *,
    problem: GanttProblem,
    resource_key: str,
    active_columns: tuple[TaskColumn, ...],
) -> tuple[tuple[float, float], ...]:
    """按任务和列事件点离散化容量窗口。

    Discretize capacity windows at task and candidate-column events.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        resource_key: 资源键 / Resource key.
        active_columns: 活跃列 / Active columns.

    Returns:
        时间窗口元组 / Time-window tuple.
    """
    points: set[float] = set()
    # 每次调用都要遍历全部任务，而本函数对**每个资源**调用一次——所以这里的常数因子
    # 会被「资源数 × 任务数」放大。两处收紧：
    #
    # 1. 用内联循环判断「该任务是否需要本资源」，不再调用
    #    `task.requires_resource(...)`——后者每次都新建一个生成器表达式。
    #    语义相同：都是「任一需求键相等即真」，且都是首次命中即停。
    # 2. 同一任务的 `earliest_start` / `duration` / `latest_start` / `deadline`
    #    各只读一次（它们都是 property 或字段，原来每次访问都重新求值）。
    #
    # This runs once per resource, so its constant factor is multiplied by
    # (resources x tasks). Two tightenings: an inline requirement scan instead of
    # `task.requires_resource(...)` (which allocates a generator per call), and reading
    # each task's timing attributes once instead of up to four times.
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
        latest_start = task.latest_start
        if latest_start < infinite:
            points.add(latest_start)
            points.add(latest_start + duration)
        deadline = task.deadline
        if deadline < infinite:
            points.add(deadline)

    for column in active_columns:
        for task_key, assignment_resource, start_time in column.task_assignments:
            if assignment_resource != resource_key:
                continue
            task = problem.task_by_key(task_key)
            if task is None or not task.requires_resource(resource_key):
                continue
            points.add(start_time)
            points.add(start_time + task.duration)

    if not points:
        return ()
    if problem.time_horizon < float("inf"):
        points.add(problem.time_horizon)

    # 消除 duration 加法产生的亚纳秒浮点噪声。
    # Remove sub-nanosecond floating-point noise from duration addition.
    normalized_points = {round(point, _EVENT_DECIMALS) + 0.0 for point in points}
    sorted_points = sorted(normalized_points)
    return tuple(
        (window_start, window_end)
        for window_start, window_end in zip(
            sorted_points,
            sorted_points[1:],
            strict=False,
        )
        if window_end > window_start
    )


def _capacity_coeff(
    *,
    problem: GanttProblem | None,
    start_time: float,
    task_key: str,
    resource_key: str,
    window_start: float,
    window_end: float,
) -> float:
    """计算容量约束系数 / Compute a capacity coefficient.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        start_time: 任务开始时间 / Task start time.
        task_key: 任务键 / Task key.
        resource_key: 资源键 / Resource key.
        window_start: 窗口起始 / Window start.
        window_end: 窗口结束 / Window end.

    Returns:
        重叠时的资源需求量，否则为零 / Demand on overlap, otherwise zero.
    """
    if problem is None:
        return 0.0
    task = problem.task_by_key(task_key)
    if task is None:
        return 0.0
    task_end = start_time + task.duration
    if start_time < window_end and task_end > window_start:
        return task.resource_demand(resource_key)
    return 0.0


def build_triad_model(
    *,
    meta_model: MetaModel,
    active_columns: tuple[TaskColumn, ...],
    constraint_coeffs: tuple[ConstraintCoeff, ...],
    relaxation: bool,
) -> LinearTriadModel:
    """从旧 Python 元模型构建参考三元组 / Build a legacy reference triad.

    `TaskApplicationService` 已改用原生 `MetaModelFloat64` 导出，本函数只保留
    给不经过服务默认权威路径的旧合同和参考测试。
    `TaskApplicationService` now uses a native `MetaModelFloat64` export; this
    function remains only for legacy contracts and reference tests outside the
    service's default authority path.

    Args:
        meta_model: 元模型 / Meta model.
        active_columns: 活跃列 / Active columns.
        constraint_coeffs: 约束系数 / Constraint coefficients.
        relaxation: 是否为 LP 松弛 / Whether LP relaxation.

    Returns:
        线性三元组模型 / Linear triad model.
    """
    variables = list(meta_model.variables.keys())
    objective: dict[str, float] = {}
    constraints: dict[str, dict[str, float]] = {}
    rhs: dict[str, float] = {}
    sense: dict[str, str] = {}
    lower_bounds: dict[str, float] = {}
    upper_bounds: dict[str, float] = {}
    variable_types: dict[str, str] = {}

    _setup_variable_types(
        meta_model=meta_model,
        relaxation=relaxation,
        variable_types=variable_types,
    )

    _setup_variable_bounds(
        meta_model=meta_model,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
    )

    _setup_objective(
        meta_model=meta_model,
        active_columns=active_columns,
        objective=objective,
    )

    _setup_constraint_structure(
        meta_model=meta_model,
        constraints=constraints,
        rhs=rhs,
        sense=sense,
    )

    _populate_constraint_coefficients(
        constraint_coeffs=constraint_coeffs,
        constraints=constraints,
    )

    return LinearTriadModel(
        name=meta_model.name,
        variables=variables,
        constraints=constraints,
        objective=objective,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        rhs=rhs,
        sense=sense,
        variable_types=variable_types,
    )


def extract_shadow_prices(
    *,
    meta_model: MetaModel,
    constraint_coeffs: tuple[ConstraintCoeff, ...],
    values: SolveValue,
    dual_values: Mapping[str, float] | None = None,
    task_count: int | None = None,
) -> dict[str, float]:
    """提取影子价格 / Extract shadow prices.

    提供真实约束对偶时，委托固定 Rust 任务列生成算法，只返回
    `task_compilation_*` 非零对偶。未提供对偶时，保留旧松弛标记兼容路径；
    该路径不是影子价格，也不计入原生迁移验收。
    With real duals, delegates to the pinned Rust task column-generation
    algorithm and returns only nonzero `task_compilation_*` duals. Without
    duals, the legacy slack-flag path remains for compatibility and is not
    treated as shadow-price or migration acceptance evidence.

    Args:
        meta_model: 元模型 / Meta model.
        constraint_coeffs: 约束系数 / Constraint coefficients.
        values: 求解器变量值 / Solver variable values.
        dual_values: 约束名到真实对偶值的映射 / Constraint-name dual map.
        task_count: 任务数量；省略时从任务行名称推断 /
            Task count; inferred from task-row names when omitted.

    Returns:
        影子价格字典 / Shadow price dict.
    """
    constraint_names = [
        name for name, data in meta_model.constraints.items() if isinstance(data, dict)
    ]
    if dual_values is not None:
        unknown = sorted(set(dual_values) - set(constraint_names))
        if unknown:
            raise ValueError(
                "对偶值包含未知约束 / Dual values contain unknown constraints: "
                + ", ".join(unknown)
            )
        inferred_task_count = _task_count_from_constraints(constraint_names)
        native_count = inferred_task_count if task_count is None else task_count
        native_prices = _extract_native_task_shadow_prices(
            task_count=native_count,
            dual_values=dual_values,
            constraint_name_to_index={
                name: index for index, name in enumerate(constraint_names)
            },
        )
        return {
            f"task_compilation_{index}": price
            for index, price in sorted(native_prices.items())
        }

    # 决定 3（2026-11-11 用户裁决 A）：没有真实对偶时必须报错，不能把松弛标记当影子价格。
    # 紧约束记为 1.0 / 松弛记为 0.0 是"是否紧"的指示量，与边际价格在数值和量纲上都不同；
    # 静默返回会让调用方拿到错数字且无任何信号。本模块级函数生产调用方为 0，
    # 所以抛 ValueError 不改变任何实际调用路径的行为。
    # Decision 3: without real duals this MUST fail instead of returning tightness flags.
    # Tightness (1.0/0.0) is not a marginal price; this module-level function has 0 production
    # callers, so raising ValueError changes no live call path.
    raise ValueError(
        "未提供真实对偶，无法给出影子价格 / Shadow prices require real dual values: "
        "the slack-tightness flags (1.0/0.0) are NOT shadow prices. "
        "Pass dual_values from the solver output instead."
    )


def _extract_triad_shadow_prices(
    *,
    triad: LinearTriadModel,
    values: SolveValue,
    dual_values: Mapping[str, float] | None = None,
    task_count: int | None = None,
) -> BindingResult[dict[str, float]]:
    """从原生导出三元组提取影子价格 / Extract shadow prices from a native triad.

    Args:
        triad: 原生模型导出后的三元组 / Triad materialized from native state.
        values: 求解器变量值 / Solver variable values.
        dual_values: 约束名到真实对偶值的映射 / Constraint-name dual map.
        task_count: 任务数量；省略时从任务行名称推断 / Task count, inferred
            from canonical task-row names when omitted.

    Returns:
        非零任务编译价格或失败 / Nonzero task-compilation prices or failure.
    """
    constraint_names = list(triad.constraints)
    if dual_values is not None:
        unknown = sorted(set(dual_values) - set(constraint_names))
        if unknown:
            return invalid(
                "对偶值包含未知约束 / Dual values contain unknown constraints: "
                + ", ".join(unknown)
            )
        native_count = (
            _task_count_from_constraints(constraint_names)
            if task_count is None
            else task_count
        )
        try:
            native_prices = _extract_native_task_shadow_prices(
                task_count=native_count,
                dual_values=dual_values,
                constraint_name_to_index={
                    name: index for index, name in enumerate(constraint_names)
                },
            )
        except ValueError as error:
            return invalid(
                f"影子价格提取失败 / Shadow-price extraction failed: {error}"
            )
        return Ok(
            {
                f"task_compilation_{index}": price
                for index, price in sorted(native_prices.items())
            }
        )

    prices: dict[str, float] = {}
    for name, coefficients in triad.constraints.items():
        lhs = sum(
            coefficient * values.get(variable, 0.0)
            for variable, coefficient in coefficients.items()
        )
        slack = _compute_slack(
            lhs=lhs,
            rhs=triad.rhs[name],
            sense=triad.sense[name],
        )
        prices[name] = 1.0 if slack < 1e-6 else 0.0
    return Ok(prices)


def _task_count_from_constraints(constraint_names: list[str]) -> int:
    """Infer the contiguous task compilation count from canonical row names."""
    indices: list[int] = []
    prefix = "task_compilation_"
    for name in constraint_names:
        if not name.startswith(prefix):
            continue
        suffix = name.removeprefix(prefix)
        if suffix.isascii() and suffix.isdecimal() and str(int(suffix)) == suffix:
            indices.append(int(suffix))
    return max(indices, default=-1) + 1


def build_schedule(
    *,
    problem: GanttProblem,
    values: SolveValue,
) -> tuple[TaskScheduleEntry, ...]:
    """构建调度表 / Build schedule.

    从变量值中提取每个任务的开始时间和分配资源。
    Extracts start time and assigned resource for each
    task from variable values.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        values: 求解器变量值 / Solver variable values.

    Returns:
        调度条目元组 / Schedule entry tuple.
    """
    entries: list[TaskScheduleEntry] = []
    for task in problem.tasks:
        start_var = f"start_{task.task_key}"
        start_time = values.get(start_var, 0.0)

        assigned_res = _find_assigned_resource(
            task=task,
            values=values,
        )

        entries.append(
            TaskScheduleEntry(
                task_key=task.task_key,
                start_time=start_time,
                end_time=start_time + task.duration,
                assigned_resource=assigned_res,
            )
        )

    return tuple(entries)


# ==================== 内部辅助 / Internal helpers ====================


def _setup_variable_bounds(
    *,
    meta_model: MetaModel,
    lower_bounds: dict[str, float],
    upper_bounds: dict[str, float],
) -> None:
    """设置变量边界 / Setup variable bounds.

    Args:
        meta_model: 元模型 / Meta model.
        lower_bounds: 下界字典（输出）/ Lower bounds (output).
        upper_bounds: 上界字典（输出）/ Upper bounds (output).
    """
    for var_name, var_data in meta_model.variables.items():
        is_binary = _declared_variable_type(var_data) == "binary"
        if isinstance(var_data, dict):
            lower_bounds[var_name] = var_data.get("lb", 0.0)
            upper_bounds[var_name] = var_data.get(
                "ub",
                1.0 if is_binary else float("inf"),
            )
        else:
            lower_bounds[var_name] = 0.0
            upper_bounds[var_name] = 1.0 if is_binary else float("inf")


def _setup_variable_types(
    *,
    meta_model: MetaModel,
    relaxation: bool,
    variable_types: dict[str, str],
) -> None:
    """设置变量类型 / Setup variable types.

    LP 松弛输出全连续变量；最终求解保留注册类型，未声明的列对象按二元变量处理。
    LP relaxation emits continuous variables; final solves preserve registered
    types, and undeclared column objects are treated as binary.

    Args:
        meta_model: 元模型 / Meta model.
        relaxation: 是否为 LP 松弛 / Whether LP relaxation.
        variable_types: 变量类型字典（输出）/ Variable types (output).
    """
    for var_name, var_data in meta_model.variables.items():
        if relaxation:
            variable_types[var_name] = "continuous"
            continue
        variable_types[var_name] = _declared_variable_type(var_data)


def _declared_variable_type(variable: object) -> str:
    """读取注册变量类型 / Read a registered variable type."""
    if isinstance(variable, dict):
        raw_type: object = variable.get("type", "continuous")
    else:
        raw_type = getattr(variable, "type", "binary")

    value = getattr(raw_type, "value", raw_type)
    if isinstance(value, str):
        return value.strip().lower()
    return ""


def _setup_objective(
    *,
    meta_model: MetaModel,
    active_columns: tuple[TaskColumn, ...],
    objective: dict[str, float],
) -> None:
    """设置目标函数 / Setup objective.

    列成本与元模型声明的目标都进入同一个线性目标。当前任务模型声明
    `makespan` 系数为 1，因此目标为“完工时间 + 被选列成本”。
    Column costs and objectives declared by the meta model enter one linear
    objective. The current task model declares a unit `makespan` coefficient,
    so the objective is makespan plus selected-column cost.

    Args:
        meta_model: 元模型 / Meta model.
        active_columns: 活跃列 / Active columns.
        objective: 目标字典（输出）/ Objective dict (output).
    """
    for col in active_columns:
        var_name = f"col_{col.column_key}"
        objective[var_name] = objective.get(var_name, 0.0) + col.cost

    for objective_data in meta_model.objectives.values():
        if not isinstance(objective_data, dict):
            continue
        variable_name = objective_data.get("variable")
        if not isinstance(variable_name, str) or not variable_name:
            continue
        if variable_name not in meta_model.variables:
            continue
        coefficient = objective_data.get("coefficient", 1.0)
        if not isinstance(coefficient, (int, float)):
            continue
        objective[variable_name] = objective.get(variable_name, 0.0) + float(
            coefficient
        )


def _setup_constraint_structure(
    *,
    meta_model: MetaModel,
    constraints: dict[str, dict[str, float]],
    rhs: dict[str, float],
    sense: dict[str, str],
) -> None:
    """设置约束结构 / Setup constraint structure.

    Args:
        meta_model: 元模型 / Meta model.
        constraints: 约束字典（输出）/ Constraints (output).
        rhs: 右端项字典（输出）/ RHS (output).
        sense: 方向字典（输出）/ Sense (output).
    """
    for cname, cdata in meta_model.constraints.items():
        if isinstance(cdata, dict):
            constraints[cname] = {}
            rhs[cname] = cdata.get("rhs", 0.0)
            sense[cname] = cdata.get("sense", "<=")


def _populate_constraint_coefficients(
    *,
    constraint_coeffs: tuple[ConstraintCoeff, ...],
    constraints: dict[str, dict[str, float]],
) -> None:
    """填充约束系数 / Populate constraint coefficients.

    Args:
        constraint_coeffs: 约束系数 / Constraint coefficients.
        constraints: 约束字典（输出）/ Constraints (output).
    """
    for cc in constraint_coeffs:
        if cc.constraint_name in constraints:
            current = constraints[cc.constraint_name].get(cc.variable_name, 0.0)
            constraints[cc.constraint_name][cc.variable_name] = current + cc.coefficient


def _compute_slack(
    *,
    lhs: float,
    rhs: float,
    sense: str,
) -> float:
    """计算松弛量 / Compute slack.

    Args:
        lhs: 左端项 / Left-hand side.
        rhs: 右端项 / Right-hand side.
        sense: 约束方向 / Constraint sense.

    Returns:
        松弛量 / Slack value.
    """
    if sense == "<=":
        return rhs - lhs
    if sense == ">=":
        return lhs - rhs
    return abs(lhs - rhs)


def _find_assigned_resource(
    *,
    task: object,
    values: SolveValue,
) -> str:
    """查找分配的资源 / Find assigned resource.

    Args:
        task: 任务对象 / Task object.
        values: 变量值 / Variable values.

    Returns:
        分配的资源键 / Assigned resource key.
    """
    assigned_res = ""
    best_val = 0.0
    for res_key, _ in task.resource_requirements:  # type: ignore[attr-defined]
        assign_var = f"assign_{task.task_key}_{res_key}"  # type: ignore[attr-defined]
        val = values.get(assign_var, 0.0)
        if val > best_val:
            best_val = val
            assigned_res = res_key
    return assigned_res
