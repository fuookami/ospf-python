"""Gantt task-column bridge and shadow-price native adapter."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self, cast

from ospf_python import _native
from ospf_python._binding.model import _invoke_solve
from ospf_python._binding.result import BindingResult, invoke

if TYPE_CHECKING:
    from ospf_python._binding.control import ProgressCallback, SolveHandle
    from ospf_python._binding.gantt_bunch import TaskSolve
    from ospf_python._binding.quantities import Unit
    from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
        GanttProblem,
    )
    from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
        TaskColumn,
    )

type PricingColumn = tuple[int, int, float]
"""任务、执行器与完整列成本 / Task, executor and complete column cost."""
type PricingPolicy = Callable[[dict[str, Any]], dict[str, Any]]
"""接收认证定价请求并返回共享批次 / Receive a certified request and return a shared batch."""


@dataclass(frozen=True, kw_only=True)
class TaskPricingLpReport:
    """当前任务定价主问题 LP 的原始状态 / Raw state of the current task-pricing master LP."""

    is_optimal: bool
    has_incumbent: bool
    objective: float | None
    termination_reason: str
    problem_status: str


@dataclass(frozen=True, kw_only=True)
class TaskPricingBatch:
    """固定上游任务定价批次 / Pinned upstream task-pricing batch."""

    columns: list[PricingColumn]
    completion: str
    global_scope: bool
    no_improving_columns: bool | None
    children: int


class TaskPricingAlgorithm:
    """无时隙任务-执行器完整定价域；不承诺跨线程调用。

    Unslotted complete task-executor pricing domain; not safe for cross-thread calls.
    """

    def __init__(self, handle: _native.TaskPricingAlgorithm) -> None:
        self._handle = handle

    @classmethod
    def create(
        cls,
        *,
        task_count: int,
        executor_count: int,
        max_iterations: int = 100,
    ) -> BindingResult[Self]:
        """创建固定 revision 的任务定价算法 / Create the pinned-revision task-pricing algorithm."""
        return invoke(
            lambda: _native._create_task_pricing_algorithm(
                task_count=task_count,
                executor_count=executor_count,
                max_iterations=max_iterations,
            )
        ).map(cls)

    def add_columns(
        self, columns: list[PricingColumn]
    ) -> BindingResult[list[PricingColumn]]:
        """添加初始列并返回实际新增列 / Add initial columns and return those actually added."""
        return invoke(lambda: self._handle.add_columns(columns=columns))

    def add_priced_columns(
        self, columns: list[PricingColumn]
    ) -> BindingResult[list[PricingColumn]]:
        """添加已定价列并返回实际新增列 / Add priced columns and return those actually added."""
        return invoke(lambda: self._handle.add_priced_columns(columns=columns))

    def solve_lp(
        self,
        *,
        solver: str,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> BindingResult[TaskPricingLpReport]:
        """求解当前主问题 LP 并保留原始终止状态 / Solve the current master LP and retain raw termination."""
        return _invoke_solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            call=lambda args: self._handle.solve_lp(
                solver=args[0],
                time_limit=args[1],
                cancellation=args[2],
                on_progress=args[3],
            ),
        ).map(
            lambda report: TaskPricingLpReport(
                is_optimal=report[0],
                has_incumbent=report[1],
                objective=report[2],
                termination_reason=report[3],
                problem_status=report[4],
            )
        )

    def generate(self, policy: PricingPolicy) -> BindingResult[TaskPricingBatch]:
        """请求完整定价域批次；只有 EXHAUSTED 才可能认证下界 / Request a complete-domain batch; only EXHAUSTED can certify a bound."""
        return invoke(lambda: self._handle.generate(policy=policy)).map(
            lambda batch: TaskPricingBatch(
                columns=batch[0],
                completion=batch[1],
                global_scope=batch[2],
                no_improving_columns=batch[3],
                children=batch[4],
            )
        )

    def certified_lower_bound(self) -> BindingResult[float | None]:
        """读取当前模型绑定的认证 LP 下界 / Read the certified LP bound bound to the current model."""
        return invoke(self._handle.certified_lower_bound)

    def completion(self) -> str | None:
        """读取最近成功批次的完成状态 / Read the latest successful batch completion."""
        return self._handle.completion()


def __getattr__(name: str) -> object:
    """Expose legacy task result types without re-entering the service package."""
    if name in {"TaskSelection", "TaskSolve"}:
        from ospf_python._binding import gantt_bunch

        return getattr(gantt_bunch, name)
    raise AttributeError(name)


def solve_task_columns(
    *,
    problem: GanttProblem,
    columns: tuple[TaskColumn, ...],
    resource_units: dict[str, Unit],
    max_work: int,
    solver: str,
    time_limit: int | float | None = None,
    cancellation: SolveHandle | None = None,
    on_progress: ProgressCallback | None = None,
    objective: str = "rank",
) -> BindingResult[TaskSolve]:
    """Solve a restricted finite snapshot of task columns.

    Args:
        objective: `rank` preserves the private bridge's makespan-rank
            objective; `makespan_cost` minimizes makespan plus selected-column
            cost in the same exact finite model.
    """
    from ospf_python._binding.gantt_bunch import _solve_columns

    return cast(
        "BindingResult[TaskSolve]",
        _solve_columns(
            problem=problem,
            columns=columns,
            resource_units=resource_units,
            cost_unit=None,
            task_columns=True,
            max_work=max_work,
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            task_objective=objective,
        ),
    )


def extract_shadow_prices(
    *,
    task_count: int,
    dual_values: Mapping[str, float],
    constraint_name_to_index: Mapping[str, int],
) -> dict[int, float]:
    """Extract task duals through the pinned task column-generation algorithm."""
    if task_count < 0:
        raise ValueError("任务数量不能为负数 / Task count must be nonnegative")

    indices = dict(constraint_name_to_index)
    if any(index < 0 for index in indices.values()):
        raise ValueError("约束索引不能为负数 / Constraint indices must be nonnegative")

    dual_vector = [float(dual_values.get(name, 0.0)) for name in indices]
    result, failure = _native._task_shadow_prices(
        task_count=task_count,
        dual_values=dual_vector,
        constraint_name_to_index=indices,
    )
    if failure is not None:
        raise ValueError(failure.message)
    return result or {}


def improving_columns(
    *,
    columns: Mapping[str, tuple[float, Mapping[str, float]]],
    dual_values: Mapping[str, float],
    tolerance: float,
) -> BindingResult[dict[str, bool]]:
    """Exactly compare finite-pool candidate reduced costs in Rust.

    Args:
        columns: 候选列键、成本与行系数 / Candidate keys, costs and row coefficients.
        dual_values: 当前原生 LP 的完整源行对偶 / Complete source-row duals
            from the current native LP.
        tolerance: 严格改善阈值 / Strict improvement threshold.

    Returns:
        候选列是否严格改善或绑定失败 / Whether each candidate strictly
        improves, or a binding failure.
    """
    return invoke(
        lambda: _native._task_improving_columns(
            columns=[
                (key, cost, dict(coefficients))
                for key, (cost, coefficients) in columns.items()
            ],
            dual_values=dict(dual_values),
            tolerance=tolerance,
        )
    )
