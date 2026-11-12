"""真实束列的联合资源 / Joint resources for actual bunch columns."""

from __future__ import annotations

import itertools
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


def _problem(crew_capacity: float) -> GanttProblem:
    return GanttProblem(
        tasks=(
            Task(
                "a",
                "A",
                0.5,
                deadline=3.0,
                resource_requirements=(("crew", 0.75), ("machine", 1.0)),
            ),
            Task(
                "b",
                "B",
                0.5,
                earliest_start=0.5,
                deadline=3.0,
                resource_requirements=(("crew", 0.75), ("machine", 1.0)),
            ),
            Task(
                "c",
                "C",
                0.5,
                earliest_start=0.5,
                deadline=3.5,
                resource_requirements=(("crew", 0.5), ("machine", 1.5)),
            ),
        ),
        resources=(
            Resource(
                "crew", "Crew", crew_capacity, availability=((0.0, 1.5), (1.5, 4.0))
            ),
            Resource("machine", "Machine", 2.5, availability=((0.0, 4.0),)),
        ),
        precedence_relations=(PrecedenceRelation("a", "b"),),
        time_horizon=4.0,
    )


def _columns(case: int) -> tuple[BunchColumn, ...]:
    definitions = (
        ("ab-early", (("a", 0.0), ("b", 0.5))),
        ("ab-late", (("a", 2.0), ("b", 2.5))),
        ("a", (("a", 0.0),)),
        ("b", (("b", 0.5),)),
        ("c-first", (("c", 1.0),)),
        ("c-cross", (("c", 1.25),)),
        ("c-late", (("c", 2.0),)),
        ("empty", ()),
    )
    return tuple(
        BunchColumn(key, members, "machine", ((case + 2) * (index + 1) % 9 - 4) / 4)
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
            (
                key,
                start,
                start + tasks[key].duration,
                tasks[key].resource_requirements or ((column.resource_key, 1.0),),
            )
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
        expected[frozenset(column.bunch_key for column in selected)] = sum(
            (Fraction(column.cost) for column in selected), Fraction()
        )
    return expected


@pytest.mark.parametrize("case", range(8))
def test_actual_joint_columns_match_exact_subset_oracle(solver: str, case: int) -> None:
    problem = _problem(crew_capacity=1.0 if case % 2 == 0 else 1.25)
    columns = _columns(case)
    expected = _enumerate(problem=problem, columns=columns)
    solved = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    selected = solved.solution.unwrap()
    keys = frozenset(column.bunch_key for column in selected.columns)
    assert keys in expected
    assert Fraction(*selected.cost) == expected[keys] == min(expected.values())
    assert "c-cross" not in keys
    assert selected.columns == tuple(
        column for column in columns if column.bunch_key in keys
    )


def test_seeded_joint_pools_match_exact_subset_oracle(solver: str) -> None:
    randomizer = random.Random(20261030)
    feasible = infeasible = 0
    for case in range(24):
        problem = GanttProblem(
            tasks=tuple(
                Task(
                    key,
                    key.upper(),
                    randomizer.choice((0.0, 0.25, 0.5)),
                    deadline=2.0,
                    resource_requirements=(
                        ("r", randomizer.choice((0.0, 0.25, 0.5, 1.0))),
                        ("crew", randomizer.choice((0.0, 0.25, 0.5, 1.0))),
                        ("r", randomizer.choice((0.0, 0.25))),
                    ),
                )
                for key in ("a", "b")
            ),
            resources=(
                Resource("r", "R", randomizer.choice((0.5, 1.0, 1.5))),
                Resource(
                    "crew",
                    "Crew",
                    randomizer.choice((0.5, 1.0, 1.5)),
                    availability=((0.0, 1.0), (1.0, 2.0)),
                ),
            ),
            precedence_relations=(PrecedenceRelation("a", "b"),),
            time_horizon=2.0,
        )
        columns = tuple(
            BunchColumn(
                f"{case}/{index}",
                tuple(
                    (
                        randomizer.choice(("a", "b")),
                        randomizer.choice((0.0, 0.5, 0.75, 1.0, 1.5)),
                    )
                    for _ in range(randomizer.randrange(3))
                ),
                randomizer.choice(("r", "crew")),
                randomizer.randrange(-8, 9) / 4,
            )
            for index in range(7)
        )
        expected = _enumerate(problem=problem, columns=columns)
        solved = _solve(problem=problem, columns=columns, solver=solver).unwrap()
        if not expected:
            infeasible += 1
            assert solved.report.problem_status == "INFEASIBLE", case
            assert solved.solution.is_failed(), case
            continue
        feasible += 1
        selection = solved.solution.unwrap()
        keys = frozenset(column.bunch_key for column in selection.columns)
        assert keys in expected, case
        assert Fraction(*selection.cost) == expected[keys] == min(expected.values()), (
            case
        )
    assert feasible and infeasible


def test_duplicate_requirements_are_added_without_deduplication(solver: str) -> None:
    task = Task(
        "a",
        "A",
        0.5,
        resource_requirements=(("r", 0.25), ("crew", 0.5), ("r", 0.75), ("crew", 0.5)),
    )
    problem = GanttProblem(
        tasks=(task,),
        resources=(Resource("r", "R", 1.0), Resource("crew", "Crew", 1.0)),
    )
    columns = (BunchColumn("a", (("a", 0.0),), "r", 0.0),)
    assert (
        _solve(problem=problem, columns=columns, solver=solver)
        .unwrap()
        .solution.unwrap()
        .columns
        == columns
    )
    overloaded = replace(
        problem,
        resources=(problem.resources[0], replace(problem.resources[1], capacity=0.75)),
    )
    solved = _solve(problem=overloaded, columns=columns, solver=solver).unwrap()
    assert solved.report.problem_status == "INFEASIBLE"
    assert solved.solution.is_failed()


@pytest.mark.parametrize("closed_resource", ("r", "crew"))
def test_zero_quantity_retains_explicit_calendar_requirement(
    solver: str, closed_resource: str
) -> None:
    windows = ((1.0, 2.0),)
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.5, resource_requirements=(("r", 0.0), ("crew", 0.0))),),
        resources=(
            Resource(
                "r", "R", 0.0, availability=windows if closed_resource == "r" else ()
            ),
            Resource(
                "crew",
                "Crew",
                0.0,
                availability=windows if closed_resource == "crew" else (),
            ),
        ),
    )
    columns = (
        BunchColumn("outside", (("a", 0.0),), "r", -1.0),
        BunchColumn("inside", (("a", 1.0),), "r", 1.0),
    )
    selected = (
        _solve(problem=problem, columns=columns, solver=solver)
        .unwrap()
        .solution.unwrap()
    )
    assert selected.columns == (columns[1],)


def test_zero_duration_does_not_register_large_aggregate(solver: str) -> None:
    problem = GanttProblem(
        tasks=(
            Task("a", "A", 0.0, resource_requirements=(("r", 1e308), ("r", 1e308))),
        ),
        resources=(Resource("r", "R", 0.0, availability=((1.0, 2.0),)),),
    )
    columns = (
        BunchColumn("outside", (("a", 0.0),), "r", -1.0),
        BunchColumn("inside", (("a", 1.0),), "r", 1.0),
    )
    selected = (
        _solve(problem=problem, columns=columns, solver=solver)
        .unwrap()
        .solution.unwrap()
    )
    assert selected.columns == (columns[1],)


def test_zero_duration_rejects_individual_float_overflow() -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.0, resource_requirements=(("r", 2**1024),)),),
        resources=(Resource("r", "R", 0.0),),
    )
    columns = (BunchColumn("a", (("a", 0.0),), "r", 0.0),)
    handle = SolveHandle()
    result = _solve(
        problem=problem, columns=columns, solver="scip", cancellation=handle
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.DATA_LOSS
    assert handle.phase == "READY"


@pytest.mark.parametrize(
    "case",
    (
        "negative",
        "nan",
        "infinite",
        "unknown",
        "unassigned",
        "inexact-aggregate",
        "inexact-integer",
        "overflow-integer",
        "overflow-aggregate",
    ),
)
def test_invalid_or_inexact_joint_requirements_never_start_backend(case: str) -> None:
    uses: tuple[tuple[str, float], ...] = (("r", 1.0), ("crew", 0.5))
    if case == "negative":
        uses = (("r", 1.0), ("crew", -0.5))
    elif case == "nan":
        uses = (("r", 1.0), ("crew", float("nan")))
    elif case == "infinite":
        uses = (("r", 1.0), ("crew", float("inf")))
    elif case == "unknown":
        uses = (("r", 1.0), ("missing", 0.5))
    elif case == "unassigned":
        uses = (("crew", 0.5),)
    elif case == "inexact-aggregate":
        uses = (("r", 0.1), ("r", 0.2), ("crew", 0.5))
    elif case == "inexact-integer":
        uses = (("r", 2**53 + 1), ("crew", 0.5))
    elif case == "overflow-integer":
        uses = (("r", 2**1024), ("crew", 0.5))
    elif case == "overflow-aggregate":
        uses = (("r", 1e308), ("r", 1e308), ("crew", 0.5))
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.5, resource_requirements=uses),),
        resources=(Resource("r", "R", 1.0), Resource("crew", "Crew", 1.0)),
    )
    columns = (BunchColumn("a", (("a", 0.0),), "r", 0.0),)
    handle = SolveHandle()
    result = _solve(
        problem=problem, columns=columns, solver="scip", cancellation=handle
    )
    assert isinstance(result, Failed)
    assert result.error.code is (
        ErrorCode.DATA_LOSS
        if case
        in (
            "inexact-aggregate",
            "inexact-integer",
            "overflow-integer",
            "overflow-aggregate",
        )
        else ErrorCode.NOT_SUPPORTED
        if case == "unassigned"
        else ErrorCode.ILLEGAL_ARGUMENT
    )
    assert handle.phase == "READY"


def test_secondary_resource_snapshots_are_isolated(
    solver: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    crew = Resource("crew", "Crew", 1.0, availability=((0.0, 1.0),))
    task = Task("a", "A", 0.5, resource_requirements=(("r", 1.0), ("crew", 1.0)))
    problem = GanttProblem(
        tasks=(task,),
        resources=(Resource("r", "R", 1.0), crew),
    )
    columns = (BunchColumn("a", (("a", 0.0),), "r", 0.0),)

    def mutate(**kwargs: Any) -> BindingResult[ActivitySolve]:
        object.__setattr__(crew, "capacity", 0.0)
        object.__setattr__(crew, "availability", ((1.0, 2.0),))
        object.__setattr__(task, "resource_requirements", (("r", 100.0),))
        return solve_activity(**kwargs)

    monkeypatch.setattr(gantt_bunch, "solve_activity", mutate)
    assert (
        _solve(problem=problem, columns=columns, solver=solver)
        .unwrap()
        .solution.unwrap()
        .columns
        == columns
    )


def test_source_recheck_rejects_secondary_capacity_violation(
    solver: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    uses = (("r", 1.0), ("crew", 1.0))
    problem = GanttProblem(
        tasks=(
            Task("a", "A", 0.5, resource_requirements=uses),
            Task("b", "B", 0.5, resource_requirements=uses),
        ),
        resources=(Resource("r", "R", 3.0), Resource("crew", "Crew", 1.0)),
    )
    columns = (
        BunchColumn("a", (("a", 0.0),), "r", 0.0),
        BunchColumn("b-late", (("b", 1.0),), "r", 0.0),
        BunchColumn("b-overlap", (("b", 0.0),), "r", 10.0),
    )

    def corrupt(**kwargs: Any) -> BindingResult[ActivitySolve]:
        result = solve_activity(**kwargs).unwrap()
        assert result.solution.is_ok()
        activities = cast("tuple[Activity, ...]", kwargs["activities"])
        placements = tuple(
            Placement(
                task=activity.id,
                mode="selected",
                start_ns=activity.modes[0].starts_ns[0],
                end_ns=activity.modes[0].starts_ns[0] + activity.modes[0].duration_ns,
            )
            for activity in activities
        )
        fake = Schedule(placements=placements, cost=(10, 1), cancelled=())
        return Ok(replace(result, solution=Ok(fake)))

    monkeypatch.setattr(gantt_bunch, "solve_activity", corrupt)
    result = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    assert isinstance(result.solution, Failed)
    assert result.solution.error.code is ErrorCode.APPLICATION_ERROR
    assert "Resource capacity is invalid" in result.solution.error.message


def test_source_capacity_recheck_uses_exact_binary_sum(
    solver: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    tiny = 2**-54
    assert 1.0 + tiny == 1.0
    problem = GanttProblem(
        tasks=(
            Task("a", "A", 0.5, resource_requirements=(("r", 1.0),)),
            Task("b", "B", 0.5, resource_requirements=(("r", tiny),)),
        ),
        resources=(Resource("r", "R", 1.0),),
    )
    columns = (
        BunchColumn("a", (("a", 0.0),), "r", 0.0),
        BunchColumn("b-late", (("b", 1.0),), "r", 0.0),
        BunchColumn("b-overlap", (("b", 0.0),), "r", 10.0),
    )

    def corrupt(**kwargs: Any) -> BindingResult[ActivitySolve]:
        output = solve_activity(**kwargs).unwrap()
        assert output.solution.is_ok()
        activities = cast("tuple[Activity, ...]", kwargs["activities"])
        placements = tuple(
            Placement(
                task=activity.id,
                mode="selected",
                start_ns=activity.modes[0].starts_ns[0],
                end_ns=activity.modes[0].starts_ns[0] + activity.modes[0].duration_ns,
            )
            for activity in (activities[0], activities[2])
        )
        fake = Schedule(
            placements=placements, cost=(10, 1), cancelled=(activities[1].id,)
        )
        return Ok(replace(output, solution=Ok(fake)))

    monkeypatch.setattr(gantt_bunch, "solve_activity", corrupt)
    result = _solve(problem=problem, columns=columns, solver=solver).unwrap()
    assert isinstance(result.solution, Failed)
    assert result.solution.error.code is ErrorCode.APPLICATION_ERROR
    assert "Resource capacity is invalid" in result.solution.error.message


def test_joint_requirement_work_is_budgeted_before_activity_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 0.5, resource_requirements=(("r", 0.0),) * 100),),
        resources=(Resource("r", "R", 1.0),),
    )
    columns = (BunchColumn("a", (("a", 0.0),), "r", 0.0),)
    handle = SolveHandle()

    def unexpected(**kwargs: Any) -> BindingResult[ActivitySolve]:
        pytest.fail("Activity model must not start after the bunch budget is exceeded")

    monkeypatch.setattr(gantt_bunch, "solve_activity", unexpected)
    result = _solve(
        problem=problem,
        columns=columns,
        solver="scip",
        cancellation=handle,
        max_work=50,
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.RESOURCE_EXHAUSTED
    assert handle.phase == "READY"
