"""束编组模型构建器 / Bunch-model builder.

把束编组变量、覆盖/容量/优先关系行和目标写入 Rust 持有的
`MetaModelFloat64`，并从只读线性快照构造求解三元组。
Writes bunch variables, coverage/capacity/precedence rows and the objective to
a Rust-owned `MetaModelFloat64`, then builds a solver triad from its read-only
linear snapshot.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ospf_python._binding.model import (
    ConstraintSpec,
    LinearTriadExport,
    MetaModelFloat64,
    VariableSpec,
)
from ospf_python._binding.result import BindingResult, invalid
from ospf_python.framework.gantt_scheduling.application.service.task.task_model_builder import (
    _build_triad_from_export,
)
from ospf_python.utils.functional.result import Ok

if TYPE_CHECKING:
    from ospf_python.core.model.intermediate.linear_triad_model import (
        LinearTriadModel,
    )
    from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
        GanttProblem,
    )
    from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
        BunchColumn,
    )

_CoverOccurrence = tuple[int, str, float, str]
_CoverMode = tuple[float, str, tuple[tuple[int, str], ...]]
_EVENT_DECIMALS = 12


def _build_native_bunch_model(
    *,
    problem: GanttProblem,
    active_columns: tuple[BunchColumn, ...],
) -> BindingResult[MetaModelFloat64]:
    """在 Rust 所有者中构建束编组模型 / Build the bunch model on its Rust owner.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 活跃束编组列 / Active bunch columns.

    Returns:
        完整原生模型或绑定失败 / Complete native model or binding failure.
    """
    created = MetaModelFloat64.create(f"bunch_cg_{problem.name}")
    if created.is_failed():
        return created
    model = created.unwrap()

    variable_specs = _bunch_variable_specs(
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
    constraints, rhs, senses = _bunch_constraint_structure(
        problem=problem,
        active_columns=active_columns,
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

    objective = model.set_objective(
        terms=[
            (handles[f"bunch_{column.bunch_key}"], column.cost)
            for column in active_columns
        ],
        sense="minimize",
        name="minimize_bunch_cost",
    )
    if objective.is_failed():
        _close_model(model)
        return objective
    return Ok(model)


def _bunch_variable_specs(
    *,
    problem: GanttProblem,
    active_columns: tuple[BunchColumn, ...],
) -> list[VariableSpec]:
    """构建束编组变量输入 / Build bunch-variable inputs.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 活跃束编组列 / Active bunch columns.

    Returns:
        变量输入快照 / Variable input snapshots.
    """
    specs = [
        VariableSpec(
            name=f"start_{task.task_key}",
            kind="continuous",
            lower=task.earliest_start,
            upper=(task.latest_start if math.isfinite(task.latest_start) else None),
        )
        for task in problem.tasks
    ]
    specs.extend(
        VariableSpec(
            name=f"covered_{task.task_key}",
            kind="binary",
        )
        for task in problem.tasks
    )
    cover_modes = _cover_modes(
        problem=problem,
        active_columns=active_columns,
    )
    for task_index, task in enumerate(problem.tasks):
        specs.extend(
            VariableSpec(
                name=f"cover_mode_{task_index}_{mode_index}",
                kind="binary",
            )
            for mode_index in range(len(cover_modes[task.task_key]))
        )
    specs.extend(
        VariableSpec(
            name=f"bunch_{column.bunch_key}",
            kind="binary",
        )
        for column in active_columns
    )
    return specs


def _bunch_constraint_structure(
    *,
    problem: GanttProblem,
    active_columns: tuple[BunchColumn, ...],
) -> tuple[dict[str, dict[str, float]], dict[str, float], dict[str, str]]:
    """构建束编组约束结构 / Build the bunch-row structure.

    同一列内多个成员落在同一窗口时，容量系数按成员对该资源的真实需求量
    累加而不是覆盖。任务可被多个兼容列覆盖：按
    `(start, resource)` 建立覆盖模式，列只能激活自身模式，每个任务最多激活
    一个模式，开始变量由激活模式桥接。这样多个开始和资源都一致的列可同时
    被选，而不同模式互斥；满足后所有任务之间的优先关系可通过连续开始变量
    全局校验。
    Capacity coefficients add each member's actual demand for the affected
    resource when several members of one column overlap the same window
    instead of overwriting one another. A task may be covered by multiple
    compatible columns; coverage modes group columns by `(start, resource)`, each
    column activates only its mode, each task has at most one active mode, and
    the start variable is bridged through that mode. Compatible columns can
    therefore remain selected together while distinct modes are mutually
    exclusive. Precedence can then be checked globally over the linked
    continuous start variables.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 活跃束编组列 / Active bunch columns.

    Returns:
        系数、右端项和方向 / Coefficients, right-hand sides and senses.
    """
    terms: dict[str, dict[str, float]] = {}
    rhs: dict[str, float] = {}
    senses: dict[str, str] = {}

    cover_modes = _cover_modes(
        problem=problem,
        active_columns=active_columns,
    )

    capacity_windows: dict[str, tuple[str, float, float]] = {}
    # 一次遍历把任务与列按资源分组，避免每资源各扫一遍全量
    # （那是 O(资源 × (任务 + 列×分配))）。分组的总代价是
    # O(任务 × 每任务需求数 + 列×分配)，与资源数无关。
    #
    # Group tasks and columns by resource once, instead of rescanning everything per
    # resource: O(tasks x requirements + entries) instead of
    # O(resources x (tasks + columns x assignments)).
    tasks_by_resource: dict[str, list[Any]] = {}
    for task in problem.tasks:
        for requirement_key, _amount in task.resource_requirements:
            tasks_by_resource.setdefault(requirement_key, []).append(task)
    columns_by_resource: dict[str, list[BunchColumn]] = {}
    for column in active_columns:
        columns_by_resource.setdefault(column.resource_key, []).append(column)

    for resource in problem.resources:
        resource_key = resource.resource_key
        for window_start, window_end in _discretize_windows(
            problem=problem,
            resource_key=resource_key,
            active_columns=active_columns,
            tasks=tuple(tasks_by_resource.get(resource_key, ())),
            columns=tuple(columns_by_resource.get(resource_key, ())),
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

    for task_index, task in enumerate(problem.tasks):
        name = f"demand_{task.task_key}"
        terms[name] = {}
        rhs[name] = 1.0
        senses[name] = ">="

        covered_name = f"covered_{task.task_key}"
        task_modes = cover_modes[task.task_key]
        for _, _, members in task_modes:
            for _, variable_name in members:
                terms[name][variable_name] = terms[name].get(variable_name, 0.0) + 1.0

        presence_row = f"cover_presence_{task_index}"
        terms[presence_row] = {covered_name: 1.0}
        for mode_index, _ in enumerate(task_modes):
            terms[presence_row][f"cover_mode_{task_index}_{mode_index}"] = -1.0
        rhs[presence_row] = 0.0
        senses[presence_row] = "=="

        for mode_index, (_, _, members) in enumerate(task_modes):
            mode_name = f"cover_mode_{task_index}_{mode_index}"
            for column_index, variable_name in members:
                link_row = f"cover_link_{task_index}_{column_index}"
                terms[link_row] = {
                    variable_name: 1.0,
                    mode_name: -1.0,
                }
                rhs[link_row] = 0.0
                senses[link_row] = "<="

            members_row = f"cover_mode_members_{task_index}_{mode_index}"
            terms[members_row] = {mode_name: 1.0}
            for _, variable_name in members:
                terms[members_row][variable_name] = (
                    terms[members_row].get(variable_name, 0.0) - 1.0
                )
            rhs[members_row] = 0.0
            senses[members_row] = "<="

        if len(task_modes) > 1:
            exclusive_row = f"cover_mode_exclusive_{task_index}"
            terms[exclusive_row] = {
                f"cover_mode_{task_index}_{mode_index}": 1.0
                for mode_index in range(len(task_modes))
            }
            rhs[exclusive_row] = 1.0
            senses[exclusive_row] = "<="

        bridge_row = f"start_bridge_{task_index}"
        terms[bridge_row] = {f"start_{task.task_key}": 1.0}
        for mode_index, (mode_start, _, _) in enumerate(task_modes):
            if mode_start != 0.0:
                terms[bridge_row][f"cover_mode_{task_index}_{mode_index}"] = -mode_start
        rhs[bridge_row] = 0.0
        senses[bridge_row] = "=="

    for column in active_columns:
        variable_name = f"bunch_{column.bunch_key}"
        for task_key, start_time in column.task_assignments:
            for (
                name,
                (resource_key, window_start, window_end),
            ) in capacity_windows.items():
                if resource_key != column.resource_key:
                    continue
                coefficient = _capacity_coeff(
                    problem=problem,
                    resource_key=resource_key,
                    start_time=start_time,
                    task_key=task_key,
                    window_start=window_start,
                    window_end=window_end,
                )
                if coefficient > 0.0:
                    terms[name][variable_name] = (
                        terms[name].get(variable_name, 0.0) + coefficient
                    )

    return terms, rhs, senses


def _cover_modes(
    *,
    problem: GanttProblem,
    active_columns: tuple[BunchColumn, ...],
) -> dict[str, tuple[_CoverMode, ...]]:
    """按开始和资源分组覆盖列 / Group covering columns by start and resource.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        active_columns: 活跃束编组列 / Active bunch columns.

    Returns:
        每个任务的覆盖模式 / Coverage modes for each task.
    """
    occurrences: dict[str, list[_CoverOccurrence]] = {
        task.task_key: [] for task in problem.tasks
    }
    for column_index, column in enumerate(active_columns):
        variable_name = f"bunch_{column.bunch_key}"
        seen_tasks: set[str] = set()
        for task_key, start_time in column.task_assignments:
            if task_key not in occurrences or task_key in seen_tasks:
                continue
            seen_tasks.add(task_key)
            occurrences[task_key].append(
                (
                    column_index,
                    variable_name,
                    start_time,
                    column.resource_key,
                )
            )

    modes: dict[str, tuple[_CoverMode, ...]] = {}
    for task in problem.tasks:
        grouped: dict[tuple[float, str], list[tuple[int, str]]] = {}
        for column_index, variable_name, start_time, resource_key in occurrences[
            task.task_key
        ]:
            grouped.setdefault((start_time, resource_key), []).append(
                (column_index, variable_name)
            )
        modes[task.task_key] = tuple(
            (start_time, resource_key, tuple(members))
            for (start_time, resource_key), members in grouped.items()
        )
    return modes


def _extract_bunch_shadow_prices(
    *,
    triad: LinearTriadModel,
    values: Mapping[str, float],
    dual_values: Mapping[str, float] | None = None,
) -> BindingResult[dict[str, float]]:
    """提取束编组影子价格 / Extract bunch shadow prices.

    有真实对偶时返回后端给出的约束价格；没有对偶时仅保留可识别的 0/1
    紧约束兼容标记，不冒充边际价格。
    Returns backend constraint prices when real duals exist. Without duals it
    preserves only the identifiable 0/1 tight-row compatibility flags rather
    than presenting them as marginal prices.

    Args:
        triad: 从原生模型导出的求解三元组 / Solver triad exported from native state.
        values: 变量值映射 / Variable-value mapping.
        dual_values: 约束名到真实对偶值的映射 / Constraint-name dual map.

    Returns:
        价格字典或合同失败 / Price dictionary or contract failure.
    """
    constraint_names = set(triad.constraints)
    if dual_values is not None:
        unknown = sorted(set(dual_values) - constraint_names)
        if unknown:
            return invalid(
                "对偶值包含未知约束 / Dual values contain unknown constraints: "
                + ", ".join(unknown)
            )
        return Ok(dict(dual_values))

    prices: dict[str, float] = {}
    for name, coefficients in triad.constraints.items():
        lhs = sum(
            coefficient * values.get(variable, 0.0)
            for variable, coefficient in coefficients.items()
        )
        if triad.sense[name] == "<=":
            slack = triad.rhs[name] - lhs
        elif triad.sense[name] == ">=":
            slack = lhs - triad.rhs[name]
        else:
            slack = abs(lhs - triad.rhs[name])
        prices[name] = 1.0 if slack < 1e-6 else 0.0
    return Ok(prices)


def _build_bunch_triad(
    *,
    exported: LinearTriadExport,
    relaxation: bool,
) -> BindingResult[LinearTriadModel]:
    """从原生快照构建束编组三元组 / Build a bunch triad from native state.

    Args:
        exported: 原生线性结构快照 / Native linear-structure snapshot.
        relaxation: 是否取消整数性但保留边界 / Whether to relax integrality
            while preserving bounds.

    Returns:
        独立三元组或合同失败 / Detached triad or contract failure.
    """
    return _build_triad_from_export(exported=exported, relaxation=relaxation)


def _close_model(model: MetaModelFloat64) -> None:
    """关闭临时原生模型 / Close a temporary native model.

    Args:
        model: 待关闭模型 / Model to close.
    """
    model.close()


def _discretize_windows(
    *,
    problem: GanttProblem,
    resource_key: str,
    active_columns: tuple[BunchColumn, ...],
    tasks: tuple[Any, ...] | None = None,
    columns: tuple[BunchColumn, ...] | None = None,
) -> tuple[tuple[float, float], ...]:
    """按任务和列事件点离散化容量窗口。

    Discretize capacity windows at task and candidate-column events.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        resource_key: 资源键 / Resource key.
        active_columns: 活跃束编组列 / Active bunch columns.
        tasks: 已按该资源预筛的任务 / Tasks pre-filtered to this resource.
        columns: 已按该资源预筛的列 / Columns pre-filtered to this resource.

    Returns:
        时间窗口元组 / Time-window tuple.

    **为什么有 `tasks` / `columns` 两个可选参数**：本函数对**每个资源**调用一次，
    若每次遍历全部任务与全部列，总代价是 O(资源 × (任务 + 列×分配))。
    调用方可以先用一次遍历把任务与列按资源分组，再逐资源传入——这样总代价降到
    O(任务 × 每任务需求数 + 列×分配)。传 `None` 时行为与原来完全一致。

    The optional `tasks` / `columns` let the caller group once by resource, turning
    O(resources x (tasks + columns x assignments)) into O(tasks x requirements + entries).
    Passing `None` behaves exactly as before.
    """
    points: set[float] = set()
    # 本函数对**每个资源**调用一次，所以这里的常数因子会被「资源数 × 任务数」放大。
    # 用内联循环取代 `task.requires_resource(...)`（后者每次新建生成器表达式），
    # 并把同一任务的时序属性各只读一次。语义相同。
    # Runs once per resource, so the constant factor is multiplied by
    # (resources x tasks): inline the requirement scan and read each timing attribute once.
    infinite = float("inf")
    for task in problem.tasks if tasks is None else tasks:
        if tasks is None:
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

    for column in active_columns if columns is None else columns:
        if columns is None and column.resource_key != resource_key:
            continue
        for task_key, start_time in column.task_assignments:
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
    problem: GanttProblem,
    resource_key: str,
    start_time: float,
    task_key: str,
    window_start: float,
    window_end: float,
) -> float:
    """计算束容量系数 / Compute the bunch-capacity coefficient.

    Args:
        problem: 甘特调度问题 / Gantt scheduling problem.
        resource_key: 资源键 / Resource key.
        start_time: 任务开始时间 / Task start time.
        task_key: 任务键 / Task key.
        window_start: 窗口起始 / Window start.
        window_end: 窗口结束 / Window end.

    Returns:
        重叠时为任务的资源需求量，否则为零 / Task resource demand on
        overlap, otherwise zero.
    """
    task = problem.task_by_key(task_key)
    if task is None:
        return 0.0
    task_end = start_time + task.duration
    if start_time >= window_end or task_end <= window_start:
        return 0.0
    return task.resource_demand(resource_key)
