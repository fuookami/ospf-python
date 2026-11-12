"""固定 Rust 有限候选活动调度；不替代公共 Gantt 服务。

Finite-candidate activity scheduling from pinned Rust; not the public Gantt service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python import _native
from ospf_python._binding.model import SolveReport, _invoke_solve, _report
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import BindingResult, invalid, invoke

if TYPE_CHECKING:
    from ospf_python._binding.control import ProgressCallback, SolveHandle


@dataclass(frozen=True, kw_only=True)
class Resource:
    """容量及不可用区间；数值使用所声明的单位 / Capacity and unavailable intervals in the declared unit."""

    id: str
    capacity: Rational
    unit: Unit
    unavailable_ns: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, kw_only=True)
class Mode:
    """完整有限开始域及全时段联合资源 / Complete finite starts and full-duration joint resources."""

    id: str
    duration_ns: int
    starts_ns: tuple[int, ...]
    resources: tuple[tuple[str, Rational], ...]
    cost: Rational


@dataclass(frozen=True, kw_only=True)
class Activity:
    """活动及其替代模式；仅显式取消费允许取消 / Activity with alternatives and explicit optional cancellation."""

    id: str
    modes: tuple[Mode, ...]
    cancellation_cost: Rational | None = None


@dataclass(frozen=True, kw_only=True)
class Precedence:
    """前驱完成到后继开始的最小间隔 / Minimum finish-to-start lag."""

    predecessor: str
    successor: str
    min_gap_ns: int = 0


@dataclass(frozen=True, kw_only=True)
class Row:
    """候选系数和界使用共同单位 / Choice coefficients and bounds share one unit.

    Attributes:
        id: 行身份 / Row identity.
        unit: 行系数与界的单位 / Unit of coefficients and bounds.
        coefficients: 任务、模式、开始纳秒及系数 / Task, mode, start in nanoseconds and coefficient.
        cancellation_coefficients: 可取消任务及系数 / Cancellable task and coefficient.
        lower: 可选下界 / Optional lower bound.
        upper: 可选上界 / Optional upper bound.
    """

    id: str
    unit: Unit
    coefficients: tuple[tuple[str, str, int, Rational], ...]
    cancellation_coefficients: tuple[tuple[str, Rational], ...] = ()
    lower: Rational | None = None
    upper: Rational | None = None


@dataclass(frozen=True, kw_only=True)
class Placement:
    """已复核的候选身份与时间 / Validated candidate identity and interval."""

    task: str
    mode: str
    start_ns: int
    end_ns: int


@dataclass(frozen=True, kw_only=True)
class Schedule:
    """原域复核结果；不是最优性证书 / Native-domain validated result, not an optimality certificate."""

    placements: tuple[Placement, ...]
    cost: tuple[int, int]
    cancelled: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ActivitySolve:
    """原始后端报告与独立领域复核 / Raw backend report and separate domain validation."""

    report: SolveReport
    solution: BindingResult[Schedule]


def _pair(value: object) -> bool:
    return (
        type(value) is tuple
        and len(value) == 2
        and all(type(item) is int for item in value)
    )


def solve_activity(
    *,
    horizon_ns: tuple[int, int],
    resources: tuple[Resource, ...],
    activities: tuple[Activity, ...],
    dependencies: tuple[Precedence, ...],
    rows: tuple[Row, ...] = (),
    cost_unit: Unit,
    max_work: int,
    solver: str,
    time_limit: int | float | None = None,
    cancellation: SolveHandle | None = None,
    on_progress: ProgressCallback | None = None,
) -> BindingResult[ActivitySolve]:
    """求解完整声明的有限候选，时间为相对同一原点的整数纳秒。

    Solve the complete declared finite candidates using integer nanoseconds from one origin.

    Args:
        horizon_ns: 有限区间两端 / Finite horizon endpoints.
        resources: 资源与其量的共同单位 / Resources and their common quantity units.
        activities: 活动、完整开始域和可选取消费 / Activities, complete start domains and optional cancellation costs.
        dependencies: 完成到开始的最小间隔 / Minimum finish-to-start lags.
        rows: 业务扩展行 / Business extension rows.
        cost_unit: 所有模式费用的共同单位 / Common unit of all mode costs.
        max_work: 建模工作量保守估算上限，不是时间或内存保证 / Conservative model-work estimate limit, not a time or memory guarantee.
        solver: 显式编译的后端 / Explicit compiled backend.
        time_limit: 后端时限，不覆盖建模或复核 / Backend limit, excluding preparation and validation.
        cancellation: 单次后端取消句柄 / Single-attempt backend cancellation handle.
        on_progress: 后端只读进度回调 / Read-only backend progress callback.

    Returns:
        原始报告及独立复核，或输入/环境失败 / Raw report and separate validation, or input/environment failure.
    """
    if (
        not _pair(horizon_ns)
        or type(resources) is not tuple
        or type(activities) is not tuple
        or type(dependencies) is not tuple
        or type(rows) is not tuple
        or type(cost_unit) is not Unit
        or type(max_work) is not int
        or type(solver) is not str
    ):
        return invalid("无效活动调度输入 / Invalid activity scheduling input")
    native_resources: list[_native._ActivityResource] = []
    for resource in resources:
        if (
            type(resource) is not Resource
            or type(resource.id) is not str
            or type(resource.capacity) is not Rational
            or type(resource.unit) is not Unit
            or type(resource.unavailable_ns) is not tuple
            or not all(_pair(interval) for interval in resource.unavailable_ns)
        ):
            return invalid("无效活动资源 / Invalid activity resource")
        native_resources.append(
            (
                resource.id,
                resource.capacity._handle,
                resource.unit._handle,
                list(resource.unavailable_ns),
            )
        )
    native_activities: list[_native._ActivityInput] = []
    for activity in activities:
        if type(activity) is not Activity or type(activity.id) is not str:
            return invalid("无效活动 / Invalid activity")
        if type(activity.modes) is not tuple or (
            activity.cancellation_cost is not None
            and type(activity.cancellation_cost) is not Rational
        ):
            return invalid("无效活动模式 / Invalid activity modes")
        modes: list[_native._ActivityMode] = []
        for mode in activity.modes:
            if (
                type(mode) is not Mode
                or type(mode.id) is not str
                or type(mode.duration_ns) is not int
                or type(mode.starts_ns) is not tuple
                or any(type(start) is not int for start in mode.starts_ns)
                or type(mode.resources) is not tuple
                or type(mode.cost) is not Rational
            ):
                return invalid("无效活动模式 / Invalid activity mode")
            uses: list[tuple[str, _native.Rational]] = []
            for use in mode.resources:
                if (
                    type(use) is not tuple
                    or len(use) != 2
                    or type(use[0]) is not str
                    or type(use[1]) is not Rational
                ):
                    return invalid("无效资源用量 / Invalid resource usage")
                uses.append((use[0], use[1]._handle))
            modes.append(
                (
                    mode.id,
                    mode.duration_ns,
                    list(mode.starts_ns),
                    uses,
                    mode.cost._handle,
                )
            )
        native_activities.append(
            (
                activity.id,
                modes,
                None
                if activity.cancellation_cost is None
                else activity.cancellation_cost._handle,
            )
        )
    if any(
        type(item) is not Precedence
        or type(item.predecessor) is not str
        or type(item.successor) is not str
        or type(item.min_gap_ns) is not int
        for item in dependencies
    ):
        return invalid("无效先后关系 / Invalid precedence")
    native_rows: list[_native._ActivityRow] = []
    for row in rows:
        if (
            type(row) is not Row
            or type(row.id) is not str
            or type(row.unit) is not Unit
            or type(row.coefficients) is not tuple
            or type(row.cancellation_coefficients) is not tuple
            or (row.lower is not None and type(row.lower) is not Rational)
            or (row.upper is not None and type(row.upper) is not Rational)
        ):
            return invalid("无效活动扩展行 / Invalid activity extension row")
        coefficients: list[tuple[str, str, int, _native.Rational]] = []
        for term in row.coefficients:
            if (
                type(term) is not tuple
                or len(term) != 4
                or type(term[0]) is not str
                or type(term[1]) is not str
                or type(term[2]) is not int
                or type(term[3]) is not Rational
            ):
                return invalid("无效活动行系数 / Invalid activity row coefficient")
            coefficients.append((term[0], term[1], term[2], term[3]._handle))
        cancellations: list[tuple[str, _native.Rational]] = []
        for cancellation_term in row.cancellation_coefficients:
            if (
                type(cancellation_term) is not tuple
                or len(cancellation_term) != 2
                or type(cancellation_term[0]) is not str
                or type(cancellation_term[1]) is not Rational
            ):
                return invalid(
                    "无效活动行取消系数 / Invalid activity row cancellation coefficient"
                )
            cancellations.append((cancellation_term[0], cancellation_term[1]._handle))
        native_rows.append(
            (
                row.id,
                row.unit._handle,
                coefficients,
                cancellations,
                None if row.lower is None else row.lower._handle,
                None if row.upper is None else row.upper._handle,
            )
        )
    result = _invoke_solve(
        solver=solver,
        time_limit=time_limit,
        cancellation=cancellation,
        on_progress=on_progress,
        call=lambda args: _native._solve_activity(
            horizon=horizon_ns,
            resources=native_resources,
            activities=native_activities,
            dependencies=[
                (item.predecessor, item.successor, item.min_gap_ns)
                for item in dependencies
            ],
            rows=native_rows,
            cost_unit=cost_unit._handle,
            max_work=max_work,
            solver=args[0],
            time_limit=args[1],
            cancellation=args[2],
            on_progress=args[3],
        ),
    )
    return result.map(
        lambda value: ActivitySolve(
            report=_report(identity=value[0], generation=0, raw=value[1]),
            solution=invoke(lambda: (value[2], value[3])).map(
                lambda schedule: Schedule(
                    placements=tuple(
                        Placement(task=task, mode=mode, start_ns=start, end_ns=end)
                        for task, mode, start, end in schedule[0]
                    ),
                    cost=schedule[1],
                    cancelled=tuple(schedule[2]),
                )
            ),
        )
    )
