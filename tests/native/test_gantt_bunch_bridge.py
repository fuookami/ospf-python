"""旧束列的有限候选桥接 / Finite-candidate bridge for legacy bunch columns."""

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
from ospf_python._binding.gantt_bunch import BunchSolve, solve_bunch_columns
from ospf_python._binding.quantities import Unit
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
    BunchColumn,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_type import TaskType
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from ospf_python._binding.result import BindingResult


@pytest.fixture(params=("scip", "gurobi10", "gurobi11", "gurobi12"))
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def _unit(name: str) -> Unit:
    return Unit.create(name=name, symbol=name, powers=(0,) * 10).unwrap()


def _problem() -> GanttProblem:
    return GanttProblem(
        tasks=(
            Task("a", "A", 0.1, deadline=0.5),
            Task("b", "B", 0.2, earliest_start=0.1, deadline=0.5),
        ),
        resources=(Resource("r", "R", 2.0, availability=((0.0, 0.3), (0.3, 1.0))),),
        precedence_relations=(PrecedenceRelation("a", "b"),),
        time_horizon=1.0,
    )


def _columns(case: int) -> tuple[BunchColumn, ...]:
    definitions = (
        ("early", (("a", 0.0), ("b", 0.1))),
        ("late", (("a", 0.5), ("b", 0.6))),
        ("a", (("a", 0.0),)),
        ("b", (("b", 0.3),)),
        ("twice", (("a", 0.0), ("a", 0.0))),
        ("bad-order", (("a", 0.2), ("b", 0.1))),
        ("empty", ()),
    )
    return tuple(
        BunchColumn(key, members, "r", float(((index + 1) * case + 3 * index) % 7 - 3))
        for index, (key, members) in enumerate(definitions)
    )


def _enumerate(
    *, problem: GanttProblem, columns: tuple[BunchColumn, ...]
) -> dict[frozenset[str], Fraction]:
    tasks = {task.task_key: task for task in problem.tasks}
    resources = {resource.resource_key: resource for resource in problem.resources}
    expected: dict[frozenset[str], Fraction] = {}
    for flags in itertools.product((False, True), repeat=len(columns)):
        selected = [column for column, flag in zip(columns, flags, strict=True) if flag]
        members = [
            (key, column.resource_key, start, start + tasks[key].duration)
            for column in selected
            for key, start in column.task_assignments
        ]
        if any(not any(key == task for key, _, _, _ in members) for task in tasks):
            continue
        if any(
            start < 0
            or start < tasks[key].earliest_start
            or end > tasks[key].deadline
            or end > problem.time_horizon
            or not resources[resource].available_during(start=start, end=end)
            for key, resource, start, end in members
        ):
            continue
        if any(
            left_end + relation.min_gap > right_start
            for relation in problem.precedence_relations
            for key, _, _, left_end in members
            if key == relation.predecessor_key
            for other, _, right_start, _ in members
            if other == relation.successor_key
        ):
            continue
        if any(
            sum(
                r == resource.resource_key and start <= point < end
                for _, r, start, end in members
            )
            > resource.capacity
            for resource in resources.values()
            for _, _, point, _ in members
        ):
            continue
        expected[frozenset(column.bunch_key for column in selected)] = sum(
            (Fraction.from_float(column.cost) for column in selected), Fraction()
        )
    return expected


def _solve(
    *,
    problem: GanttProblem,
    columns: tuple[BunchColumn, ...],
    solver: str,
    cancellation: SolveHandle | None = None,
    max_work: int = 500_000,
) -> BindingResult[BunchSolve]:
    return solve_bunch_columns(
        problem=problem,
        columns=columns,
        resource_units={
            resource.resource_key: _unit(resource.resource_key)
            for resource in problem.resources
        },
        cost_unit=_unit("cost"),
        max_work=max_work,
        solver=solver,
        cancellation=cancellation,
    )


@pytest.mark.parametrize("case", range(6))
def test_actual_columns_match_independent_float_domain_enumeration(
    solver: str, case: int
) -> None:
    problem, columns = _problem(), _columns(case)
    expected = _enumerate(problem=problem, columns=columns)
    solved = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    selected = solved.solution.unwrap()
    keys = frozenset(column.bunch_key for column in selected.columns)
    assert keys in expected
    assert Fraction(*selected.cost) == expected[keys] == min(expected.values())
    assert selected.columns == tuple(
        column for column in columns if column.bunch_key in keys
    )
    assert solved.report.solution_presence == "OPTIMAL"
    assert 0.1 + 0.2 > 0.3
    assert "early" not in keys


@pytest.mark.parametrize("case", range(12))
def test_multiple_resources_and_float_event_order_match_enumeration(
    solver: str, case: int
) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.1, deadline=1.0), Task("b", "B", 0.2, deadline=1.0)),
        resources=(
            Resource("r", "R", 1.0, availability=((0.0, 0.3), (0.3, 1.0))),
            Resource("s", "S", 2.0, availability=((0.0, 1.0),)),
        ),
        precedence_relations=(PrecedenceRelation("a", "b"),),
    )
    definitions = (
        ("a-r", (("a", 0.0),), "r"),
        ("a-s", (("a", 0.1),), "s"),
        ("b-r", (("b", 0.1),), "r"),
        ("b-s", (("b", 0.3),), "s"),
        ("ab-s", (("a", 0.0), ("b", 0.1)), "s"),
        ("overlap", (("a", 0.0), ("b", 0.0)), "s"),
        ("empty", (), "r"),
    )
    columns = tuple(
        BunchColumn(key, members, resource, float(((case + 2) * (index + 1)) % 9 - 4))
        for index, (key, members, resource) in enumerate(definitions)
    )
    expected = _enumerate(problem=problem, columns=columns)
    solved = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    selection = solved.solution.unwrap()
    keys = frozenset(column.bunch_key for column in selection.columns)
    assert keys in expected
    assert Fraction(*selection.cost) == expected[keys] == min(expected.values())


def test_seeded_finite_pools_match_independent_enumeration(solver: str) -> None:
    randomizer = random.Random(20261030)
    for case in range(24):
        problem = GanttProblem(
            tasks=(
                Task("a", "A", randomizer.choice((0.0, 0.1, 0.2)), deadline=1.0),
                Task("b", "B", randomizer.choice((0.0, 0.1, 0.2)), deadline=1.0),
            ),
            resources=(
                Resource(
                    "r",
                    "R",
                    float(randomizer.choice((1, 2))),
                    availability=((0.0, 0.3), (0.3, 1.0)),
                ),
                Resource("s", "S", float(randomizer.choice((1, 2)))),
            ),
            precedence_relations=(
                PrecedenceRelation("a", "b", randomizer.choice((-0.1, 0.0, 0.1))),
            ),
            time_horizon=1.0,
        )
        starts = (-0.1, -0.0, 0.0, 0.1, 0.2, 0.3, 0.6)
        columns = tuple(
            BunchColumn(
                f"{case}/{index}",
                tuple(
                    (randomizer.choice(("a", "b")), randomizer.choice(starts))
                    for _ in range(randomizer.randrange(3))
                ),
                randomizer.choice(("r", "s")),
                randomizer.randrange(-8, 9) / 4,
            )
            for index in range(7)
        )
        expected = _enumerate(problem=problem, columns=columns)
        solved = _solve(problem=problem, columns=columns, solver=solver).unwrap()
        if not expected:
            assert solved.report.problem_status == "INFEASIBLE", case
            assert solved.solution.is_failed(), case
            continue
        selection = solved.solution.unwrap()
        keys = frozenset(column.bunch_key for column in selection.columns)
        assert keys in expected, case
        assert Fraction(*selection.cost) == expected[keys] == min(expected.values()), (
            case
        )


def test_duplicate_members_and_empty_column_are_retained(solver: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.1),),
        resources=(Resource("r", "R", 2.0),),
    )
    columns = (
        BunchColumn("duplicate", (("a", -0.0), ("a", -0.0)), "r", -2.0),
        BunchColumn("empty", (), "r", -1.0),
    )
    selected = (
        _solve(problem=problem, columns=columns, solver=solver)
        .unwrap()
        .solution.unwrap()
    )
    assert selected.columns == columns
    assert len(selected.columns[0].task_assignments) == 2
    assert math.copysign(1.0, selected.columns[0].task_assignments[0][1]) == -1.0
    assert Fraction(*selected.cost) == -3


def test_duplicate_members_consume_separate_units(solver: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.1),), resources=(Resource("r", "R", 1.0),)
    )
    columns = (BunchColumn("duplicate", (("a", 0.0), ("a", 0.0)), "r", 0.0),)
    solved = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    assert solved.report.problem_status == "INFEASIBLE"
    assert solved.solution.is_failed()


def test_compatible_columns_may_cover_one_task_in_one_mode(solver: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.5),), resources=(Resource("r", "R", 2.0),)
    )
    columns = (
        BunchColumn("first", (("a", 0.0),), "r", -1.0),
        BunchColumn("second", (("a", 0.0),), "r", -1.0),
    )
    solved = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    selection = solved.solution.unwrap()
    assert selection.columns == columns
    assert Fraction(*selection.cost) == -2


def test_empty_pool_is_infeasible_not_a_default_schedule(solver: str) -> None:
    solved = _solve(problem=_problem(), columns=(), solver=solver).unwrap()
    assert solved.report.problem_status == "INFEASIBLE"
    assert solved.solution.is_failed()


def test_solve_handle_is_single_attempt(solver: str) -> None:
    handle = SolveHandle()
    result = _solve(
        problem=_problem(), columns=_columns(0), solver=solver, cancellation=handle
    )
    assert result.is_ok()
    assert handle.phase == "FINISHED"
    again = _solve(
        problem=_problem(), columns=_columns(0), solver=solver, cancellation=handle
    )
    assert again.is_failed()
    assert handle.phase == "FINISHED"


def test_matching_unit_requirement_and_touching_intervals(solver: str) -> None:
    problem = GanttProblem(
        tasks=(
            Task("a", "A", 0.1, resource_requirements=(("r", 1.0),)),
            Task("b", "B", 0.2, resource_requirements=(("r", 1.0),)),
        ),
        resources=(Resource("r", "R", 1.0),),
        precedence_relations=(PrecedenceRelation("a", "b"),),
    )
    columns = (
        BunchColumn("a", (("a", 0.0),), "r", 0.1),
        BunchColumn("b", (("b", 0.1),), "r", 0.2),
    )
    selected = (
        _solve(problem=problem, columns=columns, solver=solver)
        .unwrap()
        .solution.unwrap()
    )
    assert selected.columns == columns
    assert Fraction(*selected.cost) == Fraction.from_float(0.1) + Fraction.from_float(
        0.2
    )


def test_snapshot_is_not_changed_by_mutating_sources_during_solve(
    solver: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    resource = Resource("r", "R", 1.0)
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.5),), resources=(resource,), time_horizon=1.0
    )
    column = BunchColumn("a", (("a", 0.0),), "r", 2.0)
    real_solve = solve_activity

    def mutate(**kwargs: Any) -> BindingResult[ActivitySolve]:
        object.__setattr__(resource, "capacity", 0.0)
        object.__setattr__(problem, "time_horizon", 0.0)
        object.__setattr__(column, "cost", 99.0)
        return real_solve(**kwargs)

    monkeypatch.setattr(gantt_bunch, "solve_activity", mutate)
    result = _solve(problem=problem, columns=(column,), solver=solver).unwrap()
    selected = result.solution.unwrap()
    assert selected.columns[0].cost == 2.0
    assert Fraction(*selected.cost) == 2
    assert selected.columns[0] is not column


@pytest.mark.parametrize(
    "corruption",
    ("identity", "interval", "coverage", "sync", "window", "order", "capacity", "cost"),
)
def test_original_domain_recheck_rejects_corrupt_native_selection(
    solver: str, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 1.0, deadline=4.0), Task("b", "B", 1.0)),
        resources=(Resource("r", "R", 1.0),),
        precedence_relations=(PrecedenceRelation("a", "b"),),
        time_horizon=4.0,
    )
    columns = (
        BunchColumn("a", (("a", 0.0),), "r", 0.0),
        BunchColumn("b", (("b", 1.0),), "r", 0.0),
        BunchColumn("late", (("a", 2.0),), "r", 10.0),
        BunchColumn("overlap", (("a", 0.0),), "r", 10.0),
        BunchColumn("window", (("a", 4.0),), "r", 10.0),
        BunchColumn("paired", (("a", 0.0), ("b", 1.0)), "r", 10.0),
    )
    real_solve = solve_activity

    def corrupt(**kwargs: Any) -> BindingResult[ActivitySolve]:
        result = real_solve(**kwargs)
        assert result.is_ok()
        output = result.unwrap()
        assert output.solution.is_ok()
        activities = cast("tuple[Activity, ...]", kwargs["activities"])
        chosen = {"c0m0", "c1m0"}
        if corruption == "coverage":
            chosen.remove("c1m0")
        elif corruption == "sync":
            chosen.add("c5m0")
        elif corruption == "window":
            chosen.add("c4m0")
        elif corruption == "order":
            chosen.add("c2m0")
        elif corruption == "capacity":
            chosen.add("c3m0")
        placements = tuple(
            Placement(
                task=activity.id,
                mode="selected",
                start_ns=activity.modes[0].starts_ns[0],
                end_ns=activity.modes[0].starts_ns[0] + activity.modes[0].duration_ns,
            )
            for activity in activities
            if activity.id in chosen
        )
        if corruption == "identity":
            placements = (replace(placements[0], task="alien"), *placements[1:])
        elif corruption == "interval":
            placements = (replace(placements[0], end_ns=999), *placements[1:])
        cost = 1 if corruption == "cost" else (10 if len(chosen) == 3 else 0)
        fake = Schedule(
            placements=placements,
            cost=(cost, 1),
            cancelled=tuple(
                activity.id for activity in activities if activity.id not in chosen
            ),
        )
        return Ok(replace(output, solution=Ok(fake)))

    monkeypatch.setattr(gantt_bunch, "solve_activity", corrupt)
    result = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    assert isinstance(result.solution, Failed)
    assert result.solution.error.code is ErrorCode.APPLICATION_ERROR
    assert {
        "identity": "Activity identities differ",
        "interval": "Activity interval differs",
        "coverage": "Task is not covered",
        "sync": "Bunch members are not synchronized",
        "window": "Task window is invalid",
        "order": "Precedence is invalid",
        "capacity": "Resource capacity is invalid",
        "cost": "Column cost differs",
    }[corruption] in result.solution.error.message


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("duplicate-task", ErrorCode.ILLEGAL_ARGUMENT),
        ("duplicate-resource", ErrorCode.ILLEGAL_ARGUMENT),
        ("duplicate-column", ErrorCode.ILLEGAL_ARGUMENT),
        ("unknown-task", ErrorCode.ILLEGAL_ARGUMENT),
        ("unknown-resource", ErrorCode.ILLEGAL_ARGUMENT),
        ("assigned-mismatch", ErrorCode.NOT_SUPPORTED),
        ("preemptive", ErrorCode.NOT_SUPPORTED),
        ("nan-start", ErrorCode.ILLEGAL_ARGUMENT),
        ("nan-window", ErrorCode.ILLEGAL_ARGUMENT),
        ("infinite-end", ErrorCode.ILLEGAL_ARGUMENT),
        ("collapsed-end", ErrorCode.DATA_LOSS),
        ("collapsed-gap", ErrorCode.DATA_LOSS),
        ("rounded-zero-end-down", ErrorCode.DATA_LOSS),
        ("rounded-zero-end-up", ErrorCode.DATA_LOSS),
        ("reversed-end", ErrorCode.DATA_LOSS),
        ("rounded-zero-gap", ErrorCode.DATA_LOSS),
        ("rounded-zero-gap-up", ErrorCode.DATA_LOSS),
        ("reversed-positive-gap", ErrorCode.DATA_LOSS),
        ("reversed-negative-gap", ErrorCode.DATA_LOSS),
        ("collapsed-negative-gap", ErrorCode.DATA_LOSS),
        ("budget", ErrorCode.RESOURCE_EXHAUSTED),
    ),
)
def test_rejected_inputs_do_not_start_solver(case: str, code: ErrorCode) -> None:
    problem, columns = _problem(), _columns(0)
    task, resource = problem.tasks[0], problem.resources[0]
    if case == "duplicate-task":
        problem = replace(problem, tasks=problem.tasks + (task,))
    elif case == "duplicate-resource":
        problem = replace(problem, resources=problem.resources + (resource,))
    elif case == "duplicate-column":
        columns += (columns[0],)
    elif case == "unknown-task":
        columns = (replace(columns[0], task_assignments=(("missing", 0.0),)),)
    elif case == "unknown-resource":
        columns = (replace(columns[0], resource_key="missing"),)
    elif case == "assigned-mismatch":
        problem = replace(
            problem,
            resources=problem.resources + (Resource("other", "Other", 1.0),),
            tasks=(
                replace(task, resource_requirements=(("other", 1.0),)),
                problem.tasks[1],
            ),
        )
    elif case == "preemptive":
        problem = replace(
            problem,
            tasks=(replace(task, task_type=TaskType.PREEMPTIVE), problem.tasks[1]),
        )
    elif case == "nan-start":
        columns = (replace(columns[0], task_assignments=(("a", float("nan")),)),)
    elif case == "nan-window":
        problem = replace(
            problem, resources=(replace(resource, availability=((0.0, float("nan")),)),)
        )
    elif case == "infinite-end":
        problem = replace(
            problem, tasks=(replace(task, duration=1e308), problem.tasks[1])
        )
        columns = (replace(columns[0], task_assignments=(("a", 1e308),)),)
    elif case == "collapsed-end":
        problem = replace(
            problem, tasks=(replace(task, duration=0.1), problem.tasks[1])
        )
        columns = (replace(columns[0], task_assignments=(("a", 1e20),)),)
    elif case == "collapsed-gap":
        problem = replace(
            problem,
            tasks=(replace(task, duration=1e6), problem.tasks[1]),
            precedence_relations=(PrecedenceRelation("a", "b", 0.1),),
        )
        columns = (replace(columns[0], task_assignments=(("a", 1e20),)),)
    elif case in ("rounded-zero-end-down", "rounded-zero-end-up", "reversed-end"):
        start = 2**53 + (3 if case == "rounded-zero-end-up" else 1)
        problem = replace(
            problem,
            tasks=(
                replace(task, duration=1.0 if case == "reversed-end" else 0.0),
                problem.tasks[1],
            ),
        )
        columns = (replace(columns[0], task_assignments=(("a", start),)),)
    elif case in (
        "rounded-zero-gap",
        "rounded-zero-gap-up",
        "reversed-positive-gap",
        "reversed-negative-gap",
        "collapsed-negative-gap",
    ):
        start, gap = {
            "rounded-zero-gap": (2**53 + 1, 0.0),
            "rounded-zero-gap-up": (2**53 + 3, 0.0),
            "reversed-positive-gap": (2**53 + 1, 1.0),
            "reversed-negative-gap": (2**53 + 3, -1.0),
            "collapsed-negative-gap": (10**20, -0.1),
        }[case]
        problem = replace(
            problem,
            tasks=(replace(task, duration=0), problem.tasks[1]),
            precedence_relations=(PrecedenceRelation("a", "b", gap),),
        )
        columns = (replace(columns[0], task_assignments=(("a", start),)),)
    handle = SolveHandle()
    result = _solve(
        problem=problem,
        columns=columns,
        solver="scip",
        cancellation=handle,
        max_work=1 if case == "budget" else 500_000,
    )
    assert isinstance(result, Failed)
    assert result.error.code is code
    assert handle.phase == "READY"


def test_non_numeric_member_is_a_result_not_an_exception() -> None:
    columns = (BunchColumn("bad", (("a", cast("float", "0")),), "r", 0.0),)
    assert _solve(problem=_problem(), columns=columns, solver="scip").is_failed()
