"""模型构建辅助器 / Model builder helper.

封装列生成中模型构建、影子价格提取和解构建逻辑。
Encapsulates model building, shadow price extraction, and
solution construction logic for column generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    TaskScheduleEntry,
)

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


def build_triad_model(
    *,
    meta_model: MetaModel,
    active_columns: tuple[TaskColumn, ...],
    constraint_coeffs: tuple[ConstraintCoeff, ...],
    relaxation: bool,
) -> LinearTriadModel:
    """构建线性三元组模型 / Build linear triad model.

    根据 MetaModel 和约束系数构建可求解的线性规划模型。
    Builds a solvable LP model from the MetaModel and
    constraint coefficients.

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

    _setup_variable_bounds(
        meta_model=meta_model,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
    )

    _setup_column_objective(
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
    )


def extract_shadow_prices(
    *,
    meta_model: MetaModel,
    constraint_coeffs: tuple[ConstraintCoeff, ...],
    values: SolveValue,
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

        lhs = _compute_constraint_lhs(
            constraint_name=cname,
            constraint_coeffs=constraint_coeffs,
            values=values,
        )
        rhs_val = cdata.get("rhs", 0.0)
        cdata_sense = cdata.get("sense", "<=")

        slack = _compute_slack(
            lhs=lhs,
            rhs=rhs_val,
            sense=cdata_sense,
        )

        prices[cname] = 1.0 if slack < 1e-6 else 0.0

    return prices


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
        if isinstance(var_data, dict):
            lower_bounds[var_name] = var_data.get("lb", 0.0)
            upper_bounds[var_name] = var_data.get("ub", float("inf"))
        else:
            lower_bounds[var_name] = 0.0
            upper_bounds[var_name] = 1.0


def _setup_column_objective(
    *,
    active_columns: tuple[TaskColumn, ...],
    objective: dict[str, float],
) -> None:
    """设置列目标函数 / Setup column objective.

    Args:
        active_columns: 活跃列 / Active columns.
        objective: 目标字典（输出）/ Objective dict (output).
    """
    for col in active_columns:
        var_name = f"col_{col.column_key}"
        objective[var_name] = col.cost


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


def _compute_constraint_lhs(
    *,
    constraint_name: str,
    constraint_coeffs: tuple[ConstraintCoeff, ...],
    values: SolveValue,
) -> float:
    """计算约束左端项 / Compute constraint LHS.

    Args:
        constraint_name: 约束名称 / Constraint name.
        constraint_coeffs: 约束系数 / Constraint coefficients.
        values: 变量值 / Variable values.

    Returns:
        左端项值 / LHS value.
    """
    lhs = 0.0
    for cc in constraint_coeffs:
        if cc.constraint_name == constraint_name:
            var_val = values.get(cc.variable_name, 0.0)
            lhs += cc.coefficient * var_val
    return lhs


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
    for res_key, _ in task.resource_requirements:  # type: ignore[union-attr]
        assign_var = f"assign_{task.task_key}_{res_key}"  # type: ignore[union-attr]
        val = values.get(assign_var, 0.0)
        if val > best_val:
            best_val = val
            assigned_res = res_key
    return assigned_res
