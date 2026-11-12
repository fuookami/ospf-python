"""旧束列与任务列的受限 Rust 活动桥接；不替代公共服务。

Restricted legacy-column bridge to Rust activity scheduling, not the public service.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, TypeGuard, cast

from ospf_python._binding.gantt_activity import (
    Activity,
    Mode,
    Row,
    Schedule,
    solve_activity,
)
from ospf_python._binding.gantt_activity import (
    Resource as ActivityResource,
)
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import (
    BindingResult,
    FailureContext,
    invalid,
    unsupported,
)
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
    BunchColumn,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    TaskColumn,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_type import TaskType
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from ospf_python._binding.control import ProgressCallback, SolveHandle
    from ospf_python._binding.model import SolveReport


@dataclass(frozen=True, kw_only=True)
class BunchSelection:
    """原始列快照和精确费用，不是全局最优证书 / Original column snapshots and exact cost, not a global optimality certificate.

    Attributes:
        columns: 所选列，保留输入顺序与成员 / Selected columns in input order with their members.
        cost: 所选列费用的精确分子与分母 / Exact numerator and denominator of selected costs.
    """

    columns: tuple[BunchColumn, ...]
    cost: tuple[int, int]


@dataclass(frozen=True, kw_only=True)
class BunchSolve:
    """原始模型报告与分离的原域复核 / Raw model report and separate source-domain validation.

    Attributes:
        report: 有限列模型的原始后端报告 / Raw backend report for the finite-column model.
        solution: 复核后的列，或不可发布的原因 / Validated selection or reason it cannot be published.
    """

    report: SolveReport
    solution: BindingResult[BunchSelection]


@dataclass(frozen=True, kw_only=True)
class TaskSelection:
    """原始任务列和原域完成时间 / Original task columns and source-domain makespan.

    Attributes:
        columns: 所选列，保留输入顺序 / Selected columns in input order.
        makespan: 最晚完成时间，使用输入的 Python 秒口径 / Latest completion in the input's Python seconds.
    """

    columns: tuple[TaskColumn, ...]
    makespan: int | float


@dataclass(frozen=True, kw_only=True)
class TaskSolve:
    """原始层级模型报告与原域复核 / Raw ordinal-model report and source-domain validation.

    Attributes:
        report: 有限模型的原始报告，目标为内部层级而非秒 / Raw finite-model report whose objective is an internal rank, not seconds.
        solution: 复核后的任务列或失败 / Validated task columns or failure.
    """

    report: SolveReport
    solution: BindingResult[TaskSelection]


@dataclass(frozen=True, kw_only=True)
class _Member:
    activity: str
    task: str
    requirements: tuple[tuple[str, int | float], ...]
    start: int | float
    end: int | float
    earliest: int | float
    deadline: int | float
    availability: tuple[tuple[tuple[float, float], ...], ...]


def _number(value: object, *, finite: bool = False) -> TypeGuard[int | float]:
    return type(value) is int or (
        type(value) is float
        and not math.isnan(value)
        and (not finite or math.isfinite(value))
    )


def _failure[T](code: ErrorCode, message: str) -> BindingResult[T]:
    return Failed(
        ExErr(
            _code=code,
            _message=message,
            value=FailureContext(
                source="ospf-python",
                category=code.name,
                rust_code=None,
                error_class="DOMAIN_VALIDATION"
                if code is ErrorCode.APPLICATION_ERROR
                else "BOUNDARY",
            ),
        )
    )


def _rational(value: int | float | Fraction) -> BindingResult[Rational]:
    if isinstance(value, int):
        return Rational.from_value(value)
    if isinstance(value, Fraction):
        return Rational.from_value(value)
    return Rational.from_float(value)


def _level_cost(levels: tuple[int | float, ...], index: int) -> BindingResult[Rational]:
    """返回层级前缀的精确增量 / Return the exact increment for a level prefix."""
    current = Fraction(levels[index])
    previous = Fraction(levels[index - 1]) if index else Fraction(0)
    return _rational(current - previous)


def _allowed(member: _Member, horizon: int | float) -> bool:
    return (
        member.start >= 0
        and member.start >= member.earliest
        and member.end <= member.deadline
        and member.end <= horizon
        and all(
            not windows
            or any(
                start <= member.start and member.end <= end for start, end in windows
            )
            for windows in member.availability
        )
    )


def _selection(
    *,
    schedule: Schedule,
    columns: tuple[BunchColumn | TaskColumn, ...],
    groups: tuple[tuple[_Member, ...], ...],
    ticks: dict[int | float, int],
    tasks: tuple[str, ...],
    capacities: dict[str, int | float],
    relations: tuple[tuple[str, str, int | float], ...],
    horizon: int | float,
    levels: tuple[int | float, ...] | None,
    task_objective: str,
) -> BindingResult[BunchSelection | TaskSelection]:
    placements = {item.task: item for item in schedule.placements}
    cancelled = set(schedule.cancelled)
    level_ids = (
        () if levels is None else tuple(f"level/{i + 1}" for i in range(len(levels)))
    )
    identities = {member.activity for group in groups for member in group} | set(
        level_ids
    )
    if (
        len(placements) != len(schedule.placements)
        or len(cancelled) != len(schedule.cancelled)
        or set(placements) & cancelled
        or set(placements) | cancelled != identities
    ):
        return _failure(
            ErrorCode.APPLICATION_ERROR, "活动身份不一致 / Activity identities differ"
        )
    level_flags = [key in placements for key in level_ids]
    if any(
        flag and not level_flags[index - 1]
        for index, flag in enumerate(level_flags)
        if index
    ):
        return _failure(
            ErrorCode.APPLICATION_ERROR,
            "完成时间层级无效 / Makespan levels are invalid",
        )
    if any(
        placements[key].mode != "selected"
        or placements[key].start_ns != ticks[0]
        or placements[key].end_ns != ticks[0]
        for key in level_ids
        if key in placements
    ):
        return _failure(
            ErrorCode.APPLICATION_ERROR,
            "完成时间层级区间无效 / Makespan level interval is invalid",
        )
    selected: list[BunchColumn | TaskColumn] = []
    chosen: list[_Member] = []
    for column, group in zip(columns, groups, strict=True):
        flags = [member.activity in placements for member in group]
        if any(flags) and not all(flags):
            return _failure(
                ErrorCode.APPLICATION_ERROR,
                "束成员未同步 / Bunch members are not synchronized",
            )
        if not all(flags):
            continue
        selected.append(column)
        for member in group:
            placement = placements[member.activity]
            if (
                placement.mode != "selected"
                or placement.start_ns != ticks[member.start]
                or placement.end_ns != ticks[member.end]
            ):
                return _failure(
                    ErrorCode.APPLICATION_ERROR,
                    "活动区间不一致 / Activity interval differs",
                )
            if member.task:
                chosen.append(member)
    if levels is None:
        if any(not any(member.task == task for member in chosen) for task in tasks):
            return _failure(
                ErrorCode.APPLICATION_ERROR, "任务未覆盖 / Task is not covered"
            )
    elif any(sum(member.task == task for member in chosen) != 1 for task in tasks):
        return _failure(
            ErrorCode.APPLICATION_ERROR,
            "任务未恰好覆盖一次 / Task must be covered exactly once",
        )
    if any(not _allowed(member, horizon) for member in chosen):
        return _failure(
            ErrorCode.APPLICATION_ERROR, "任务窗口无效 / Task window is invalid"
        )
    if any(
        left.end + gap > right.start
        for predecessor, successor, gap in relations
        for left in chosen
        if left.task == predecessor
        for right in chosen
        if right.task == successor
    ):
        return _failure(
            ErrorCode.APPLICATION_ERROR, "先后关系无效 / Precedence is invalid"
        )
    if any(
        sum(
            (
                Fraction(amount)
                for member in chosen
                if member.start <= point.start < member.end
                for key, amount in member.requirements
                if key == resource
            ),
            Fraction(),
        )
        > Fraction(capacity)
        for resource, capacity in capacities.items()
        for point in chosen
    ):
        return _failure(
            ErrorCode.APPLICATION_ERROR, "资源容量无效 / Resource capacity is invalid"
        )
    if levels is not None:
        makespan = max((member.end for member in chosen), default=0)
        rank = sum(level_flags)
        if any(member.end > (levels[rank - 1] if rank else 0) for member in chosen):
            return _failure(
                ErrorCode.APPLICATION_ERROR,
                "完成时间层级过低 / Makespan level is too low",
            )
        if task_objective == "rank":
            if schedule.cost != (rank, 1):
                return _failure(
                    ErrorCode.APPLICATION_ERROR,
                    "完成时间层级目标无效 / Makespan rank objective is invalid",
                )
        else:
            expected = Fraction(makespan) + sum(
                (Fraction(column.cost) for column in selected),
                Fraction(),
            )
            if schedule.cost != (expected.numerator, expected.denominator):
                return _failure(
                    ErrorCode.APPLICATION_ERROR,
                    "完工时间与列成本目标不一致 / Makespan-plus-column-cost objective differs",
                )
        return Ok(
            TaskSelection(
                columns=cast("tuple[TaskColumn, ...]", tuple(selected)),
                makespan=makespan,
            )
        )
    cost = sum((Fraction(column.cost) for column in selected), Fraction())
    if (cost.numerator, cost.denominator) != schedule.cost:
        return _failure(
            ErrorCode.APPLICATION_ERROR, "列费用不一致 / Column cost differs"
        )
    return Ok(
        BunchSelection(
            columns=cast("tuple[BunchColumn, ...]", tuple(selected)), cost=schedule.cost
        )
    )


def solve_bunch_columns(
    *,
    problem: GanttProblem,
    columns: tuple[BunchColumn, ...],
    resource_units: dict[str, Unit],
    cost_unit: Unit,
    max_work: int,
    solver: str,
    time_limit: int | float | None = None,
    cancellation: SolveHandle | None = None,
    on_progress: ProgressCallback | None = None,
) -> BindingResult[BunchSolve]:
    """求解受限的真实束列快照，不执行列生成或替换公共服务。

    Solve a restricted snapshot of real bunch columns, without column generation.
    无显式需求时占用指定资源的一个声明单位；否则使用包含指定资源的全部需求。
    Without explicit requirements each member uses one assigned-resource unit;
    otherwise all declared uses, including the assigned resource, apply jointly.
    Non-fixed tasks are rejected. Event ranks are internal order coordinates,
    not physical nanoseconds. Original float intervals and identities are retained.

    Args:
        problem: 原始甘特问题 / Original Gantt problem.
        columns: 完整有限束列 / Complete finite bunch columns.
        resource_units: 每种资源的单位 / Unit for each resource.
        cost_unit: 全部列费用的单位 / Common unit for all column costs.
        max_work: 保守工作估算上限，并非时间或内存保证 / Conservative work estimate, not a time or memory guarantee.
        solver: 显式选择的 Rust 后端 / Explicit Rust backend.
        time_limit: 后端时限 / Backend time limit.
        cancellation: 单次求解取消句柄 / Single-attempt cancellation handle.
        on_progress: 后端进度回调 / Backend progress callback.

    Returns:
        有限模型报告及原域复核，或边界失败 / Finite-model report and source-domain validation, or boundary failure.
    """
    return cast(
        "BindingResult[BunchSolve]",
        _solve_columns(
            problem=problem,
            columns=columns,
            resource_units=resource_units,
            cost_unit=cost_unit,
            task_columns=False,
            max_work=max_work,
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
        ),
    )


def _solve_columns(
    *,
    problem: GanttProblem,
    columns: tuple[BunchColumn | TaskColumn, ...],
    resource_units: dict[str, Unit],
    cost_unit: Unit | None,
    task_columns: bool,
    max_work: int,
    solver: str,
    time_limit: int | float | None,
    cancellation: SolveHandle | None,
    on_progress: ProgressCallback | None,
    task_objective: str = "rank",
) -> BindingResult[BunchSolve | TaskSolve]:
    if (
        type(problem) is not GanttProblem
        or type(columns) is not tuple
        or type(resource_units) is not dict
        or (not task_columns and (type(cost_unit) is not Unit or cost_unit.is_affine))
        or type(max_work) is not int
        or max_work <= 0
        or max_work > 2 * sys.maxsize + 1
        or type(solver) is not str
        or task_objective not in {"rank", "makespan_cost"}
        or type(problem.tasks) is not tuple
        or type(problem.resources) is not tuple
        or type(problem.precedence_relations) is not tuple
        or not _number(problem.time_horizon)
        or problem.time_horizon < 0
    ):
        return invalid("无效束列问题 / Invalid bunch-column problem")
    if not problem.tasks or any(type(task) is not Task for task in problem.tasks):
        return invalid("无效任务集合 / Invalid tasks")
    if any(type(resource) is not Resource for resource in problem.resources):
        return invalid("无效资源集合 / Invalid resources")
    tasks = {
        task.task_key: task
        for task in problem.tasks
        if type(task.task_key) is str and task.task_key
    }
    resources = {
        resource.resource_key: resource
        for resource in problem.resources
        if type(resource.resource_key) is str and resource.resource_key
    }
    if len(tasks) != len(problem.tasks) or len(resources) != len(problem.resources):
        return invalid(
            "任务或资源身份重复或无效 / Duplicate or invalid task or resource identity"
        )
    if (
        any(type(key) is not str for key in resource_units)
        or set(resource_units) != set(resources)
        or any(
            type(unit) is not Unit or unit.is_affine for unit in resource_units.values()
        )
    ):
        return invalid("资源单位无效 / Invalid resource units")
    requirements: dict[str, tuple[tuple[str, int | float], ...]] = {}
    for key, task in tasks.items():
        if task.task_type is not TaskType.FIXED:
            return unsupported(
                "仅支持固定时长任务 / Only fixed-duration tasks are supported"
            )
        if (
            not _number(task.duration, finite=True)
            or task.duration < 0
            or not _number(task.earliest_start)
            or not _number(task.deadline)
            or type(task.resource_requirements) is not tuple
        ):
            return invalid(
                "无效任务时间或资源需求 / Invalid task times or resource requirements"
            )
        for requirement in task.resource_requirements:
            if (
                type(requirement) is not tuple
                or len(requirement) != 2
                or type(requirement[0]) is not str
                or requirement[0] not in resources
                or not _number(requirement[1], finite=True)
                or requirement[1] < 0
            ):
                return invalid("无效任务资源需求 / Invalid task resource requirement")
        requirements[key] = task.resource_requirements
    for resource in resources.values():
        if (
            not _number(resource.capacity, finite=True)
            or resource.capacity < 0
            or type(resource.availability) is not tuple
            or any(
                type(window) is not tuple
                or len(window) != 2
                or not _number(window[0])
                or not _number(window[1])
                or window[0] > window[1]
                for window in resource.availability
            )
        ):
            return invalid(
                "无效资源容量或时间窗 / Invalid resource capacity or availability"
            )
    horizon = problem.time_horizon
    capacities = {key: resource.capacity for key, resource in resources.items()}
    availability = {key: resource.availability for key, resource in resources.items()}
    relations: list[tuple[str, str, int | float]] = []
    for relation in problem.precedence_relations:
        if (
            type(relation) is not PrecedenceRelation
            or type(relation.predecessor_key) is not str
            or type(relation.successor_key) is not str
            or relation.predecessor_key not in tasks
            or relation.successor_key not in tasks
            or not _number(relation.min_gap, finite=True)
        ):
            return invalid("无效先后关系 / Invalid precedence")
        relations.append(
            (relation.predecessor_key, relation.successor_key, relation.min_gap)
        )
    expected_type = TaskColumn if task_columns else BunchColumn
    if any(
        type(column) is not expected_type or type(column.task_assignments) is not tuple
        for column in columns
    ):
        return invalid("无效调度列 / Invalid scheduling column")
    work_items = sum(max(1, len(column.task_assignments)) for column in columns)
    windows = sum(len(value) for value in availability.values())
    max_uses = max(1, max(len(value) for value in requirements.values()))
    if (
        work_items * work_items * (len(relations) + len(resources) * max_uses + 1)
        + work_items * (len(tasks) + windows * max_uses + max_uses)
        + windows
        + len(tasks)
        + len(resources)
        + sum(len(value) for value in requirements.values())
        + (work_items * (work_items + 4) if task_columns else 0)
        > max_work
    ):
        return _failure(
            ErrorCode.RESOURCE_EXHAUSTED,
            "调度列模型超出预算 / Scheduling column model exceeds budget",
        )
    seen: set[str] = set()
    snapshots: list[BunchColumn | TaskColumn] = []
    groups: list[tuple[_Member, ...]] = []
    for column_index, column in enumerate(columns):
        if isinstance(column, BunchColumn):
            column_key = column.bunch_key
            if (
                type(column.resource_key) is not str
                or column.resource_key not in resources
            ):
                return invalid("无效指定资源 / Invalid assigned resource")
            snapshot: BunchColumn | TaskColumn = BunchColumn(
                column.bunch_key,
                column.task_assignments,
                column.resource_key,
                column.cost,
                column.reduced_cost,
            )
        else:
            column_key = column.column_key
            snapshot = TaskColumn(
                column.column_key,
                column.task_assignments,
                column.cost,
                column.reduced_cost,
            )
        if (
            type(column_key) is not str
            or not column_key
            or column_key in seen
            or not _number(column.cost, finite=True)
            or not _number(column.reduced_cost, finite=True)
        ):
            return invalid("列身份或费用无效 / Invalid column identity or cost")
        seen.add(column_key)
        snapshots.append(snapshot)
        members: list[_Member] = []
        for member_index, assignment in enumerate(column.task_assignments):
            if (
                type(assignment) is not tuple
                or len(assignment) != (3 if task_columns else 2)
                or type(assignment[0]) is not str
                or assignment[0] not in tasks
            ):
                return invalid("列成员无效 / Invalid column member")
            task_key = assignment[0]
            assigned: object
            start: object
            if isinstance(column, BunchColumn):
                assigned = column.resource_key
                start = assignment[1]
            else:
                assigned = assignment[1]
                start = assignment[2]
            if (
                type(assigned) is not str
                or assigned not in resources
                or not _number(start, finite=True)
            ):
                return invalid("列成员资源或时间无效 / Invalid member resource or time")
            task = tasks[task_key]
            uses = requirements[task_key]
            if uses and not any(key == assigned for key, _ in uses):
                return unsupported(
                    "指定资源与任务需求不一致 / Assigned resource differs from task requirement"
                )
            if not uses:
                uses = ((assigned, 1),)
            try:
                end = start + task.duration
            except OverflowError:
                return invalid("任务结束时间溢出 / Task end time overflows")
            if not _number(end, finite=True):
                return invalid("任务结束时间必须有限 / Task end time must be finite")
            if (task.duration == 0 and end != start) or (
                task.duration > 0 and end <= start
            ):
                return _failure(
                    ErrorCode.DATA_LOSS,
                    "浮点加法丢失任务时长 / Float addition loses task duration",
                )
            # 上游在无损门禁前转换有限值；先拦截溢出。 / Upstream converts before its exactness gate; reject overflow first.
            totals: dict[str, Fraction] = {}
            for key, amount in uses:
                exact_use = Fraction(amount)
                if exact_use > sys.float_info.max:
                    return _failure(
                        ErrorCode.DATA_LOSS,
                        "资源用量超出 Float64 / Resource usage exceeds Float64",
                    )
                if end > start:
                    totals[key] = totals.get(key, Fraction()) + exact_use
                    if totals[key] > sys.float_info.max:
                        return _failure(
                            ErrorCode.DATA_LOSS,
                            "资源用量超出 Float64 / Resource usage exceeds Float64",
                        )
            members.append(
                _Member(
                    activity=f"c{column_index}m{member_index}",
                    task=task_key,
                    requirements=uses,
                    start=start,
                    end=end,
                    earliest=task.earliest_start,
                    deadline=task.deadline,
                    availability=tuple(availability[key] for key, _ in uses),
                )
            )
        if not members:
            members.append(
                _Member(
                    activity=f"c{column_index}m0",
                    task="",
                    requirements=(),
                    start=0,
                    end=0,
                    earliest=0,
                    deadline=0,
                    availability=(),
                )
            )
        groups.append(tuple(members))
    if task_columns and task_objective == "makespan_cost":
        merged_groups: list[tuple[_Member, ...]] = []
        for group in groups:
            merged_members: list[_Member] = []
            task_indexes: dict[str, int] = {}
            for member in group:
                if not member.task:
                    merged_members.append(member)
                    continue
                previous_index = task_indexes.get(member.task)
                if previous_index is None:
                    task_indexes[member.task] = len(merged_members)
                    merged_members.append(member)
                    continue
                previous = merged_members[previous_index]
                if previous.start != member.start or previous.end != member.end:
                    return invalid(
                        "同一列内任务开始时间不一致 / Task starts differ within a column"
                    )
                if requirements[member.task]:
                    if previous.requirements != member.requirements:
                        return invalid(
                            "同一列内任务资源需求不一致 / Task requirements differ within a column"
                        )
                    return invalid(
                        "同一列内任务资源分配重复 / Duplicate task-resource assignment"
                    )
                uses = tuple(
                    dict.fromkeys((*previous.requirements, *member.requirements))
                )
                if len(uses) != len(previous.requirements) + len(member.requirements):
                    return invalid(
                        "同一列内任务资源分配重复 / Duplicate task-resource assignment"
                    )
                merged_members[previous_index] = _Member(
                    activity=previous.activity,
                    task=previous.task,
                    requirements=uses,
                    start=previous.start,
                    end=previous.end,
                    earliest=previous.earliest,
                    deadline=previous.deadline,
                    availability=tuple(
                        dict.fromkeys((*previous.availability, *member.availability))
                    ),
                )
            merged_groups.append(tuple(merged_members))
        groups = merged_groups
    members = [member for group in groups for member in group if member.task]
    incompatible: list[tuple[_Member, _Member]] = []
    for predecessor, successor, gap in relations:
        for left in members:
            if left.task != predecessor:
                continue
            try:
                end_with_gap = left.end + gap
            except OverflowError:
                return invalid("先后关系时间溢出 / Precedence time overflows")
            if not _number(end_with_gap, finite=True):
                return invalid("先后关系时间必须有限 / Precedence time must be finite")
            if (
                (gap == 0 and end_with_gap != left.end)
                or (gap > 0 and end_with_gap <= left.end)
                or (gap < 0 and end_with_gap >= left.end)
            ):
                return _failure(
                    ErrorCode.DATA_LOSS,
                    "浮点加法丢失先后间隔 / Float addition loses precedence gap",
                )
            incompatible.extend(
                (left, right)
                for right in members
                if right.task == successor and end_with_gap > right.start
            )
    # 仅将区间端点的次序编码入临时模型，不把坐标导出为实际时间。 / Encode only endpoint ordering; never export these coordinates as real time.
    points = sorted(
        {0, *(member.start for member in members), *(member.end for member in members)}
    )
    ticks = {point: index for index, point in enumerate(points)}
    levels = (
        tuple(sorted({member.end for member in members if member.end > 0}))
        if task_columns
        else None
    )
    level_index = {} if levels is None else {value: i for i, value in enumerate(levels)}
    zero_result, one_result, minus_result = (_rational(value) for value in (0, 1, -1))
    row_unit_result = Unit.create(
        name="scheduling row", symbol="scheduling row", powers=(0,) * 10
    )
    for result in (zero_result, one_result, minus_result, row_unit_result):
        if isinstance(result, Failed):
            return Failed(result.error)
    zero, one, minus = zero_result.unwrap(), one_result.unwrap(), minus_result.unwrap()
    row_unit = row_unit_result.unwrap()
    native_resources = []
    for key, value in capacities.items():
        capacity = _rational(value)
        if isinstance(capacity, Failed):
            return Failed(capacity.error)
        native_resources.append(
            ActivityResource(
                id=key, capacity=capacity.unwrap(), unit=resource_units[key]
            )
        )
    activities: list[Activity] = []
    rows: list[Row] = []
    for index, (column, group) in enumerate(zip(snapshots, groups, strict=True)):
        cost = _rational(
            0 if task_columns and task_objective == "rank" else column.cost
        )
        if isinstance(cost, Failed):
            return Failed(cost.error)
        anchor = group[0]
        for member_index, member in enumerate(group):
            native_uses: list[tuple[str, Rational]] = []
            for key, amount in member.requirements:
                amount_result = _rational(amount)
                if isinstance(amount_result, Failed):
                    return Failed(amount_result.error)
                native_uses.append((key, amount_result.unwrap()))
            activities.append(
                Activity(
                    id=member.activity,
                    modes=(
                        Mode(
                            id="selected",
                            duration_ns=ticks[member.end] - ticks[member.start],
                            starts_ns=(ticks[member.start],),
                            resources=tuple(native_uses),
                            cost=(
                                cost.unwrap()
                                if member_index == 0
                                and (
                                    not task_columns
                                    or task_objective == "makespan_cost"
                                )
                                else zero
                            ),
                        ),
                    ),
                    cancellation_cost=zero,
                )
            )
            if member_index:
                rows.append(
                    Row(
                        id=f"link/{index}/{member_index}",
                        unit=row_unit,
                        coefficients=(
                            (anchor.activity, "selected", ticks[anchor.start], one),
                            (member.activity, "selected", ticks[member.start], minus),
                        ),
                        lower=zero,
                        upper=zero,
                    )
                )
            if levels is not None and member.task and member.end > 0:
                level = level_index[member.end] + 1
                rows.append(
                    Row(
                        id=f"finish/{index}/{member_index}",
                        unit=row_unit,
                        coefficients=(
                            (member.activity, "selected", ticks[member.start], one),
                            (f"level/{level}", "selected", ticks[0], minus),
                        ),
                        upper=zero,
                    )
                )
        if any(not _allowed(member, horizon) for member in group if member.task):
            rows.append(
                Row(
                    id=f"blocked/{index}",
                    unit=row_unit,
                    coefficients=(
                        (anchor.activity, "selected", ticks[anchor.start], one),
                    ),
                    upper=zero,
                )
            )
    for index, task_key in enumerate(tasks):
        rows.append(
            Row(
                id=f"coverage/{index}",
                unit=row_unit,
                coefficients=tuple(
                    (member.activity, "selected", ticks[member.start], one)
                    for member in members
                    if member.task == task_key
                ),
                lower=one,
                upper=one if task_columns else None,
            )
        )
    if levels is not None:
        for index in range(len(levels)):
            level_id = f"level/{index + 1}"
            if task_objective == "rank":
                level_cost = one
            else:
                cost_result = _level_cost(levels, index)
                if isinstance(cost_result, Failed):
                    return Failed(cost_result.error)
                level_cost = cost_result.unwrap()
            activities.append(
                Activity(
                    id=level_id,
                    modes=(
                        Mode(
                            id="selected",
                            duration_ns=0,
                            starts_ns=(ticks[0],),
                            resources=(),
                            cost=level_cost,
                        ),
                    ),
                    cancellation_cost=zero,
                )
            )
            if index:
                rows.append(
                    Row(
                        id=f"level-prefix/{index + 1}",
                        unit=row_unit,
                        coefficients=(
                            (level_id, "selected", ticks[0], one),
                            (f"level/{index}", "selected", ticks[0], minus),
                        ),
                        upper=zero,
                    )
                )
    for index, (left, right) in enumerate(incompatible):
        terms: tuple[tuple[str, str, int, Rational], ...] = (
            (left.activity, "selected", ticks[left.start], one),
        )
        if left.activity != right.activity:
            terms += ((right.activity, "selected", ticks[right.start], one),)
            upper = one
        else:
            upper = zero
        rows.append(
            Row(
                id=f"precedence/{index}", unit=row_unit, coefficients=terms, upper=upper
            )
        )
    solved = solve_activity(
        horizon_ns=(0, max(1, len(points) - 1)),
        resources=tuple(native_resources),
        activities=tuple(activities),
        dependencies=(),
        rows=tuple(rows),
        cost_unit=row_unit if task_columns else cast("Unit", cost_unit),
        max_work=max_work,
        solver=solver,
        time_limit=time_limit,
        cancellation=cancellation,
        on_progress=on_progress,
    )
    if isinstance(solved, Failed):
        return Failed(solved.error)
    output = solved.unwrap()
    selection = output.solution.flat_map(
        lambda schedule: _selection(
            schedule=schedule,
            columns=tuple(snapshots),
            groups=tuple(groups),
            ticks=ticks,
            tasks=tuple(tasks),
            capacities=capacities,
            relations=tuple(relations),
            horizon=horizon,
            levels=levels,
            task_objective=task_objective,
        )
    )
    if task_columns:
        return Ok(
            TaskSolve(
                report=output.report,
                solution=cast("BindingResult[TaskSelection]", selection),
            )
        )
    return Ok(
        BunchSolve(
            report=output.report,
            solution=cast("BindingResult[BunchSelection]", selection),
        )
    )
