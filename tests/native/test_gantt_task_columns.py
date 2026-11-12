"""真实任务列的完成时间目标 / Makespan for actual task columns."""

from __future__ import annotations

import itertools
import math
import random
from dataclasses import replace
from fractions import Fraction
from typing import TYPE_CHECKING, Any, cast

import pytest

from ospf_python import _native
from ospf_python._binding import gantt_bunch
from ospf_python._binding.control import SolveHandle
from ospf_python._binding.gantt_activity import (
    Activity,
    ActivitySolve,
    Placement,
    Schedule,
    solve_activity,
)
from ospf_python._binding.gantt_task import TaskSolve, solve_task_columns
from ospf_python._binding.quantities import Unit
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    TaskColumn,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from ospf_python._binding.control import ProgressCallback
    from ospf_python._binding.result import BindingResult


@pytest.fixture(params=("scip", "gurobi10", "gurobi11", "gurobi12"))
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def _unit(name: str) -> Unit:
    return Unit.create(name=name, symbol=name, powers=(0,) * 10).unwrap()


def _solve(
    *,
    problem: GanttProblem,
    columns: tuple[TaskColumn, ...],
    solver: str,
    objective: str = "rank",
    cancellation: SolveHandle | None = None,
    on_progress: ProgressCallback | None = None,
    max_work: int = 500_000,
) -> BindingResult[TaskSolve]:
    return solve_task_columns(
        problem=problem,
        columns=columns,
        resource_units={
            resource.resource_key: _unit(resource.resource_key)
            for resource in problem.resources
        },
        max_work=max_work,
        solver=solver,
        objective=objective,
        cancellation=cancellation,
        on_progress=on_progress,
    )


def _enumerate(
    *, problem: GanttProblem, columns: tuple[TaskColumn, ...]
) -> dict[frozenset[str], int | float]:
    tasks = {task.task_key: task for task in problem.tasks}
    resources = {resource.resource_key: resource for resource in problem.resources}
    feasible: dict[frozenset[str], int | float] = {}
    for flags in itertools.product((False, True), repeat=len(columns)):
        selected = [column for column, flag in zip(columns, flags, strict=True) if flag]
        members = [
            (
                key,
                start,
                start + tasks[key].duration,
                tasks[key].resource_requirements or ((resource, 1),),
            )
            for column in selected
            for key, resource, start in column.task_assignments
        ]
        if any(sum(key == task for key, _, _, _ in members) != 1 for task in tasks):
            continue
        if any(
            start < 0
            or start < tasks[key].earliest_start
            or end > tasks[key].deadline
            or end > problem.time_horizon
            or any(
                not resources[resource].available_during(start=start, end=end)
                for resource, _ in uses
            )
            for key, start, end, uses in members
        ):
            continue
        if any(
            left_end + relation.min_gap > right_start
            for relation in problem.precedence_relations
            for key, _, left_end, _ in members
            if key == relation.predecessor_key
            for other, right_start, _, _ in members
            if other == relation.successor_key
        ):
            continue
        if any(
            sum(
                (
                    Fraction(amount)
                    for _, start, end, uses in members
                    if start <= point < end
                    for key, amount in uses
                    if key == resource.resource_key
                ),
                Fraction(),
            )
            > Fraction(resource.capacity)
            for resource in resources.values()
            for _, point, _, _ in members
        ):
            continue
        feasible[frozenset(column.column_key for column in selected)] = max(
            (end for _, _, end, _ in members), default=0
        )
    return feasible


def test_actual_task_columns_minimize_makespan_not_column_cost(solver: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.1), Task("b", "B", 0.2, earliest_start=0.1)),
        resources=(Resource("r", "R", 1.0), Resource("s", "S", 1.0)),
        precedence_relations=(PrecedenceRelation("a", "b"),),
        time_horizon=3.0,
    )
    columns = (
        TaskColumn("early", (("a", "r", 0.0), ("b", "s", 0.1)), 100.0),
        TaskColumn("late", (("a", "s", 1.0), ("b", "r", 1.1)), -100.0),
        TaskColumn("duplicate", (("a", "r", 0.0), ("a", "s", 0.0)), -200.0),
        TaskColumn("empty", (), -500.0),
    )
    expected = _enumerate(problem=problem, columns=columns)
    output = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    selection = output.solution.unwrap()
    keys = frozenset(column.column_key for column in selection.columns)
    assert keys in expected
    assert selection.makespan == expected[keys] == min(expected.values()) == 0.1 + 0.2
    assert "early" in keys and "late" not in keys and "duplicate" not in keys
    assert selection.columns == tuple(
        column for column in columns if column.column_key in keys
    )
    assert output.report.solution_presence == "OPTIMAL"


def test_makespan_cost_objective_trades_finish_time_for_column_cost(
    solver: str,
) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 1.0),),
        resources=(Resource("r", "R", 1.0),),
        time_horizon=10.0,
    )
    columns = (
        TaskColumn("early", (("a", "r", 0.0),), 10.0),
        TaskColumn("late", (("a", "r", 4.0),), 1.0),
    )

    output = _solve(
        problem=problem,
        columns=columns,
        solver=solver,
        objective="makespan_cost",
    ).unwrap()
    selection = output.solution.unwrap()

    assert selection.columns == (columns[1],)
    assert selection.makespan == 5.0
    assert output.report.objective == 6.0
    assert output.report.solution_presence == "OPTIMAL"


def test_makespan_cost_merges_multiple_resources_for_one_task(solver: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 1.0),),
        resources=(Resource("r", "R", 1.0), Resource("s", "S", 1.0)),
    )
    columns = (TaskColumn("both", (("a", "r", 0.0), ("a", "s", 0.0)), 0.0),)

    selection = (
        _solve(
            problem=problem,
            columns=columns,
            solver=solver,
            objective="makespan_cost",
        )
        .unwrap()
        .solution.unwrap()
    )

    assert selection.columns == columns
    assert selection.makespan == 1.0


def test_makespan_cost_checks_joint_capacity_after_merging(solver: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 1.0), Task("b", "B", 1.0)),
        resources=(Resource("r", "R", 1.0), Resource("s", "S", 1.0)),
    )
    columns = (
        TaskColumn(
            "over-capacity",
            (("a", "r", 0.0), ("a", "s", 0.0), ("b", "r", 0.0)),
            -10.0,
        ),
        TaskColumn("feasible", (("a", "s", 0.0), ("b", "r", 0.0)), 0.0),
    )

    output = _solve(
        problem=problem,
        columns=columns,
        solver=solver,
        objective="makespan_cost",
    ).unwrap()
    selection = output.solution.unwrap()

    assert selection.columns == (columns[1],)
    assert selection.makespan == 1.0
    assert output.report.objective == 1.0


def test_makespan_cost_rejects_duplicate_task_resource_assignments() -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 1.0, resource_requirements=(("r", 1.0),)),),
        resources=(Resource("r", "R", 1.0),),
    )
    columns = (TaskColumn("duplicate", (("a", "r", 0.0), ("a", "r", 0.0)), 0.0),)

    result = _solve(
        problem=problem,
        columns=columns,
        solver="scip",
        objective="makespan_cost",
    )

    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert "Duplicate task-resource assignment" in result.error.message


def test_task_columns_reject_unknown_objective() -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 1.0),),
        resources=(Resource("r", "R", 1.0),),
    )
    columns = (TaskColumn("a", (("a", "r", 0.0),), 0.0),)

    result = _solve(
        problem=problem,
        columns=columns,
        solver="scip",
        objective="unknown",
    )

    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_sub_tolerance_makespan_difference_is_not_rounded_away(solver: str) -> None:
    earlier = 1.0
    later = math.nextafter(earlier, math.inf)
    problem = GanttProblem(
        tasks=(Task("a", "A", 0),), resources=(Resource("r", "R", 1.0),)
    )
    columns = (
        TaskColumn("earlier", (("a", "r", earlier),), 100.0),
        TaskColumn("later", (("a", "r", later),), -100.0),
    )
    selection = (
        _solve(problem=problem, columns=columns, solver=solver)
        .unwrap()
        .solution.unwrap()
    )
    assert selection.columns == (columns[0],)
    assert selection.makespan == earlier


def test_integer_time_does_not_require_float64_conversion(solver: str) -> None:
    start = 2**53 + 1
    problem = GanttProblem(
        tasks=(Task("a", "A", 0),), resources=(Resource("r", "R", 1.0),)
    )
    columns = (TaskColumn("a", (("a", "r", start),), 0.0),)
    selection = (
        _solve(problem=problem, columns=columns, solver=solver)
        .unwrap()
        .solution.unwrap()
    )
    assert selection.columns == columns
    assert selection.makespan == start and type(selection.makespan) is int


def test_zero_finish_and_large_metadata_do_not_become_model_cost(solver: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0),), resources=(Resource("r", "R", 1.0),)
    )
    columns = (TaskColumn("a", (("a", "r", 0),), 10**400, -(10**400)),)
    output = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    assert output.report.objective == 0
    assert output.solution.unwrap().columns == columns
    assert output.solution.unwrap().makespan == 0


def test_seeded_task_pools_match_independent_enumeration(solver: str) -> None:
    randomizer = random.Random(20261030)
    feasible = infeasible = 0
    for case in range(24):
        problem = GanttProblem(
            tasks=(
                Task("a", "A", randomizer.choice((0.0, 0.25, 0.5))),
                Task(
                    "b",
                    "B",
                    randomizer.choice((0.0, 0.25, 0.5)),
                    resource_requirements=(("r", 0.25), ("s", 0.5), ("r", 0.25)),
                ),
            ),
            resources=(
                Resource("r", "R", randomizer.choice((0.5, 1.0, 1.5))),
                Resource("s", "S", 1.0, availability=((0.0, 1.0), (1.0, 2.0))),
            ),
            precedence_relations=(PrecedenceRelation("a", "b"),),
            time_horizon=2.0,
        )
        columns = tuple(
            TaskColumn(
                f"{case}/{index}",
                tuple(
                    (
                        randomizer.choice(("a", "b")),
                        randomizer.choice(("r", "s")),
                        randomizer.choice((0.0, 0.5, 0.75, 1.0, 1.5)),
                    )
                    for _ in range(randomizer.randrange(3))
                ),
                randomizer.randrange(-8, 9) / 4,
            )
            for index in range(7)
        )
        expected = _enumerate(problem=problem, columns=columns)
        output = _solve(problem=problem, columns=columns, solver=solver).unwrap()
        if not expected:
            infeasible += 1
            assert output.report.problem_status == "INFEASIBLE", case
            assert output.solution.is_failed(), case
            continue
        feasible += 1
        selection = output.solution.unwrap()
        keys = frozenset(column.column_key for column in selection.columns)
        assert keys in expected, case
        assert selection.makespan == expected[keys] == min(expected.values()), case
    assert feasible and infeasible


@pytest.mark.parametrize(
    "case", ("unknown-resource", "unknown-task", "duplicate", "mismatch", "budget")
)
def test_rejected_inputs_keep_the_cancellation_handle_ready(case: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.5, resource_requirements=(("r", 1.0),)),),
        resources=(Resource("r", "R", 1.0), Resource("s", "S", 1.0)),
    )
    columns: tuple[TaskColumn, ...] = (TaskColumn("a", (("a", "r", 0.0),), 0.0),)
    if case == "unknown-resource":
        columns = (replace(columns[0], task_assignments=(("a", "missing", 0.0),)),)
    elif case == "unknown-task":
        columns = (replace(columns[0], task_assignments=(("missing", "r", 0.0),)),)
    elif case == "duplicate":
        columns += columns
    elif case == "mismatch":
        columns = (replace(columns[0], task_assignments=(("a", "s", 0.0),)),)
    handle = SolveHandle()
    result = _solve(
        problem=problem,
        columns=columns,
        solver="scip",
        cancellation=handle,
        max_work=1 if case == "budget" else 500_000,
    )
    assert isinstance(result, Failed)
    assert result.error.code is (
        ErrorCode.NOT_SUPPORTED
        if case == "mismatch"
        else ErrorCode.RESOURCE_EXHAUSTED
        if case == "budget"
        else ErrorCode.ILLEGAL_ARGUMENT
    )
    assert handle.phase == "READY"


@pytest.mark.parametrize("pre_cancel", (False, True))
def test_task_solve_handle_is_single_attempt(solver: str, pre_cancel: bool) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.5),), resources=(Resource("r", "R", 1.0),)
    )
    columns = (TaskColumn("a", (("a", "r", 0.0),), 0.0),)
    handle = SolveHandle()
    events: list[Any] = []
    if pre_cancel:
        assert handle.cancel(reason="task pool test").unwrap()
    output = _solve(
        problem=problem,
        columns=columns,
        solver=solver,
        cancellation=handle,
        on_progress=events.append,
    ).unwrap()
    if pre_cancel:
        assert output.report.termination_reason == "CANCELLED"
        assert output.solution.is_failed()
        assert handle.cancellation_preceded_completion
    else:
        assert output.solution.unwrap().columns == columns
        assert events and events[-1].terminal
    assert handle.phase == "FINISHED"
    assert _solve(
        problem=problem, columns=columns, solver=solver, cancellation=handle
    ).is_failed()


def test_snapshot_survives_source_mutation(
    solver: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = Task("a", "A", 0.5, resource_requirements=(("r", 1.0), ("s", 1.0)))
    secondary = Resource("s", "S", 1.0, availability=((0.0, 1.0),))
    problem = GanttProblem(
        tasks=(task,), resources=(Resource("r", "R", 1.0), secondary)
    )
    column = TaskColumn("a", (("a", "r", 0.0),), 2.0)

    def mutate(**kwargs: Any) -> BindingResult[ActivitySolve]:
        object.__setattr__(task, "duration", 10.0)
        object.__setattr__(task, "resource_requirements", (("r", 100.0),))
        object.__setattr__(secondary, "capacity", 0.0)
        object.__setattr__(secondary, "availability", ((1.0, 2.0),))
        object.__setattr__(column, "cost", 99.0)
        return solve_activity(**kwargs)

    monkeypatch.setattr(gantt_bunch, "solve_activity", mutate)
    selection = (
        _solve(problem=problem, columns=(column,), solver=solver)
        .unwrap()
        .solution.unwrap()
    )
    assert selection.makespan == 0.5
    assert selection.columns[0].cost == 2.0 and selection.columns[0] is not column


def test_source_recheck_rejects_forged_coverage(
    solver: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.5),), resources=(Resource("r", "R", 2.0),)
    )
    columns = (
        TaskColumn("a1", (("a", "r", 0.0),), 0.0),
        TaskColumn("a2", (("a", "r", 0.0),), 0.0),
    )

    def corrupt(**kwargs: Any) -> BindingResult[ActivitySolve]:
        output = solve_activity(**kwargs).unwrap()
        good = output.solution.unwrap()
        activities = cast("tuple[Activity, ...]", kwargs["activities"])
        chosen = {placement.task for placement in good.placements}
        additional = next(
            activity
            for activity in activities
            if activity.id.startswith("c") and activity.id not in chosen
        )
        mode = additional.modes[0]
        extra = Placement(
            task=additional.id,
            mode=mode.id,
            start_ns=mode.starts_ns[0],
            end_ns=mode.starts_ns[0] + mode.duration_ns,
        )
        fake = Schedule(
            placements=(*good.placements, extra),
            cost=good.cost,
            cancelled=tuple(key for key in good.cancelled if key != additional.id),
        )
        return Ok(replace(output, solution=Ok(fake)))

    monkeypatch.setattr(gantt_bunch, "solve_activity", corrupt)
    result = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    assert isinstance(result.solution, Failed)
    assert result.solution.error.code is ErrorCode.APPLICATION_ERROR
    assert "exactly once" in result.solution.error.message


@pytest.mark.parametrize(
    "corruption", ("identity", "interval", "prefix", "low", "cost", "higher")
)
def test_makespan_levels_are_rechecked_in_the_source_domain(
    solver: str, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0),), resources=(Resource("r", "R", 1.0),)
    )
    columns = (
        TaskColumn("early", (("a", "r", 1),), 10.0),
        TaskColumn("late", (("a", "r", 2),), -10.0),
        TaskColumn("blocked", (("a", "r", -1),), -20.0),
    )

    def corrupt(**kwargs: Any) -> BindingResult[ActivitySolve]:
        output = solve_activity(**kwargs).unwrap()
        good = output.solution.unwrap()
        activities = cast("tuple[Activity, ...]", kwargs["activities"])
        selected = {placement.task: placement for placement in good.placements}
        cancelled = set(good.cancelled)
        assert "level/1" in selected and "level/2" in cancelled
        assert selected["level/1"].start_ns == 1

        def select_level() -> None:
            level = next(item for item in activities if item.id == "level/2")
            start = level.modes[0].starts_ns[0]
            selected[level.id] = Placement(
                task=level.id, mode="selected", start_ns=start, end_ns=start
            )
            cancelled.remove(level.id)

        cost = good.cost
        report = output.report
        if corruption == "identity":
            selected["level/1"] = replace(selected["level/1"], task="alien")
        elif corruption == "interval":
            selected["level/1"] = replace(selected["level/1"], end_ns=99)
        elif corruption in ("prefix", "low"):
            del selected["level/1"]
            cancelled.add("level/1")
            if corruption == "prefix":
                select_level()
            else:
                cost = (0, 1)
        elif corruption == "cost":
            cost = (2, 1)
        else:
            select_level()
            cost = (2, 1)
            report = replace(report, solution_presence="FEASIBLE", objective=2.0)
        fake = Schedule(
            placements=tuple(selected.values()), cost=cost, cancelled=tuple(cancelled)
        )
        return Ok(replace(output, report=report, solution=Ok(fake)))

    monkeypatch.setattr(gantt_bunch, "solve_activity", corrupt)
    result = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    if corruption == "higher":
        assert result.report.solution_presence == "FEASIBLE"
        assert result.report.objective == 2.0
        assert result.solution.unwrap().columns == (columns[0],)
        assert result.solution.unwrap().makespan == 1
    else:
        assert isinstance(result.solution, Failed)
        assert result.solution.error.code is ErrorCode.APPLICATION_ERROR
        assert {
            "identity": "Activity identities differ",
            "interval": "Makespan level interval is invalid",
            "prefix": "Makespan levels are invalid",
            "low": "Makespan level is too low",
            "cost": "Makespan rank objective is invalid",
        }[corruption] in result.solution.error.message
