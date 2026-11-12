"""实际旧列的受限表达对照 / Restricted encoding of actual legacy columns."""

from __future__ import annotations

import itertools
import math
from fractions import Fraction
from typing import TYPE_CHECKING

import pytest

from ospf_python import _native
from ospf_python._binding.gantt_activity import (
    Activity,
    ActivitySolve,
    Mode,
    Precedence,
    Row,
    solve_activity,
)
from ospf_python._binding.gantt_activity import (
    Resource as ActivityResource,
)
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_application_service import (
    BunchApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
    BunchColumn,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import (
    TaskApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    TaskColumn,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
    BunchGenerationContext,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
    ResourceContext,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
    TaskContext,
)

if TYPE_CHECKING:
    from ospf_python.core.model.intermediate.linear_triad_model import LinearTriadModel

type Column = TaskColumn | BunchColumn
type Assignment = tuple[str, str, float]


@pytest.fixture(params=("scip", "gurobi10", "gurobi11", "gurobi12"))
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def _ratio(value: float) -> Fraction:
    return Fraction.from_float(value)


def _nanoseconds(value: float) -> int:
    scaled = _ratio(value) * 1_000_000_000
    assert scaled.denominator == 1
    return scaled.numerator


def _rational(value: float) -> Rational:
    return Rational.from_float(value).unwrap()


def _unit(name: str) -> Unit:
    return Unit.create(name=name, symbol=name, powers=(0,) * 10).unwrap()


def _identity(column: Column) -> str:
    return column.column_key if isinstance(column, TaskColumn) else column.bunch_key


def _assignments(column: Column) -> tuple[Assignment, ...]:
    if isinstance(column, TaskColumn):
        return column.task_assignments
    return tuple(
        (task, column.resource_key, start) for task, start in column.task_assignments
    )


def _problem(*, capacity: float = 1.0) -> GanttProblem:
    return GanttProblem(
        name="actual-legacy-columns",
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
            Resource("crew", "Crew", capacity, availability=((0.0, 1.5), (1.5, 4.0))),
            Resource("machine", "Machine", 2.5, availability=((0.0, 4.0),)),
        ),
        precedence_relations=(PrecedenceRelation("a", "b"),),
        time_horizon=4.0,
    )


def _columns(*, bunch: bool, case: int) -> tuple[Column, ...]:
    definitions = (
        ("ab-early", (("a", 0.0), ("b", 0.5)), 3.0),
        ("ab-late", (("a", 2.0), ("b", 2.5)), 0.0),
        ("ab-overlap", (("a", 0.0), ("b", 0.0)), -9.0),
        ("a", (("a", 0.0),), 0.5),
        ("b", (("b", 0.5),), 0.5),
        ("c-first", (("c", 1.0),), 0.5),
        ("c-late", (("c", 3.0),), 1.0),
        ("c-cross", (("c", 1.25),), -50.0),
        ("c-overlap", (("c", 0.5),), 0.25),
        ("c-overlap-a", (("c", 2.0),), -10.0),
        ("c-early", (("c", 0.0),), -80.0),
        ("c-deadline", (("c", 3.5),), -90.0),
    )
    columns: list[Column] = []
    for index, (name, assignments, base) in enumerate(definitions):
        cost = base + ((case * (index + 1)) % 5) * 0.25
        if bunch:
            columns.append(BunchColumn(name, assignments, "machine", cost))
        else:
            columns.append(
                TaskColumn(
                    name,
                    tuple((task, "machine", start) for task, start in assignments),
                    cost,
                )
            )
    return tuple(columns)


def _enumerate(
    *, problem: GanttProblem, columns: tuple[Column, ...]
) -> dict[frozenset[str], tuple[Fraction, Fraction]]:
    tasks = {task.task_key: task for task in problem.tasks}
    resources = {resource.resource_key: resource for resource in problem.resources}
    feasible: dict[frozenset[str], tuple[Fraction, Fraction]] = {}
    for flags in itertools.product((False, True), repeat=len(columns)):
        selected = [column for column, flag in zip(columns, flags, strict=True) if flag]
        assignments = [entry for column in selected for entry in _assignments(column)]
        if any(sum(key == task for key, _, _ in assignments) != 1 for task in tasks):
            continue
        intervals = {
            key: (_ratio(start), _ratio(start) + _ratio(tasks[key].duration))
            for key, _, start in assignments
        }
        if any(
            start < _ratio(tasks[key].earliest_start)
            or end > _ratio(tasks[key].deadline)
            or end > _ratio(problem.time_horizon)
            for key, (start, end) in intervals.items()
        ):
            continue
        if any(
            intervals[relation.successor_key][0]
            < intervals[relation.predecessor_key][1] + _ratio(relation.min_gap)
            for relation in problem.precedence_relations
        ):
            continue
        if any(
            resource.availability
            and not any(
                _ratio(left) <= intervals[key][0] and intervals[key][1] <= _ratio(right)
                for left, right in resource.availability
            )
            for key in intervals
            for resource_key, _ in tasks[key].resource_requirements
            for resource in (resources[resource_key],)
        ):
            continue
        points = {point for interval in intervals.values() for point in interval}
        if any(
            sum(
                (
                    _ratio(amount)
                    for key, (start, end) in intervals.items()
                    if start <= point < end
                    for resource_key, amount in tasks[key].resource_requirements
                    if resource_key == resource.resource_key
                ),
                Fraction(),
            )
            > _ratio(resource.capacity)
            for resource in resources.values()
            for point in points
        ):
            continue
        feasible[frozenset(map(_identity, selected))] = (
            sum((_ratio(column.cost) for column in selected), Fraction()),
            max(end for _, end in intervals.values()),
        )
    return feasible


def _solve_encoding(
    *,
    problem: GanttProblem,
    columns: tuple[Column, ...],
    solver: str,
    ban_windows: bool,
    ban_task_windows: bool = True,
) -> ActivitySolve:
    one, zero = _rational(1.0), _rational(0.0)
    units = {
        resource.resource_key: _unit(resource.resource_key)
        for resource in problem.resources
    }
    tasks = {task.task_key: task for task in problem.tasks}
    resources = {resource.resource_key: resource for resource in problem.resources}
    activities = tuple(
        Activity(
            id=task.task_key,
            modes=tuple(
                Mode(
                    id=_identity(column),
                    duration_ns=_nanoseconds(task.duration),
                    starts_ns=(_nanoseconds(start),),
                    resources=tuple(
                        (key, _rational(amount))
                        for key, amount in task.resource_requirements
                    ),
                    cost=_rational(column.cost)
                    if assignments[0][0] == task.task_key
                    else zero,
                )
                for column in columns
                for assignments in (_assignments(column),)
                for key, _, start in assignments
                if key == task.task_key
            ),
        )
        for task in problem.tasks
    )
    row_unit = _unit("rows")
    rows = []
    for column in columns:
        assignments = _assignments(column)
        anchor, _, anchor_start = assignments[0]
        for task, _, start in assignments[1:]:
            rows.append(
                Row(
                    id=f"link-{_identity(column)}-{task}",
                    unit=row_unit,
                    coefficients=(
                        (anchor, _identity(column), _nanoseconds(anchor_start), one),
                        (task, _identity(column), _nanoseconds(start), _rational(-1.0)),
                    ),
                    lower=zero,
                    upper=zero,
                )
            )
        outside_task_window = ban_task_windows and any(
            _ratio(start) < _ratio(tasks[key].earliest_start)
            or _ratio(start) + _ratio(tasks[key].duration) > _ratio(tasks[key].deadline)
            for key, _, start in assignments
        )
        outside_resource_window = ban_windows and any(
            not resources[resource].available_during(
                start=start, end=start + tasks[key].duration
            )
            for key, _, start in assignments
            for resource, _ in tasks[key].resource_requirements
        )
        if outside_task_window or outside_resource_window:
            rows.append(
                Row(
                    id=f"unavailable-{_identity(column)}",
                    unit=row_unit,
                    coefficients=(
                        (anchor, _identity(column), _nanoseconds(anchor_start), one),
                    ),
                    upper=zero,
                )
            )
    return solve_activity(
        horizon_ns=(0, _nanoseconds(problem.time_horizon)),
        resources=tuple(
            ActivityResource(
                id=resource.resource_key,
                capacity=_rational(resource.capacity),
                unit=units[resource.resource_key],
            )
            for resource in problem.resources
        ),
        activities=activities,
        dependencies=tuple(
            Precedence(
                predecessor=relation.predecessor_key,
                successor=relation.successor_key,
                min_gap_ns=_nanoseconds(relation.min_gap),
            )
            for relation in problem.precedence_relations
        ),
        rows=tuple(rows),
        cost_unit=_unit("cost"),
        max_work=500_000,
        solver=solver,
    ).unwrap()


@pytest.mark.parametrize("bunch", (False, True))
@pytest.mark.parametrize("case", range(4))
def test_actual_legacy_columns_against_exact_subset_oracle(
    solver: str, bunch: bool, case: int
) -> None:
    problem = _problem(capacity=1.0 if case % 2 == 0 else 1.25)
    columns = _columns(bunch=bunch, case=case)
    expected = _enumerate(problem=problem, columns=columns)
    solved = _solve_encoding(
        problem=problem, columns=columns, solver=solver, ban_windows=True
    )
    solution = solved.solution.unwrap()
    names = frozenset(placement.mode for placement in solution.placements)
    assert names in expected
    assert (
        Fraction(*solution.cost)
        == expected[names][0]
        == min(cost for cost, _ in expected.values())
    )
    assert solved.report.solution_presence == "OPTIMAL"
    assert sorted((p.task, p.mode, p.start_ns) for p in solution.placements) == sorted(
        (task, _identity(column), _nanoseconds(start))
        for column in columns
        if _identity(column) in names
        for task, _, start in _assignments(column)
    )
    tasks = {task.task_key: task for task in problem.tasks}
    assert all(
        placement.end_ns
        == placement.start_ns + _nanoseconds(tasks[placement.task].duration)
        for placement in solution.placements
    )
    assert all(
        resource == "machine"
        for column in columns
        if _identity(column) in names
        for _, resource, _ in _assignments(column)
    )
    if case == 0:
        assert expected[names][1] > min(makespan for _, makespan in expected.values())


@pytest.mark.parametrize("bunch", (False, True))
def test_ignoring_joint_resource_capacity_changes_the_chosen_column(
    solver: str, bunch: bool
) -> None:
    problem = _problem(capacity=1.0)
    columns = _columns(bunch=bunch, case=0)
    relaxed = _solve_encoding(
        problem=_problem(capacity=10.0),
        columns=columns,
        solver=solver,
        ban_windows=True,
    )
    selected = frozenset(p.mode for p in relaxed.solution.unwrap().placements)
    assert {"ab-late", "c-overlap-a"} <= selected
    assert selected not in _enumerate(problem=problem, columns=columns)


@pytest.mark.parametrize("bunch", (False, True))
def test_actual_legacy_columns_can_have_no_feasible_subset(
    solver: str, bunch: bool
) -> None:
    problem = _problem(capacity=0.5)
    columns = _columns(bunch=bunch, case=0)
    assert not _enumerate(problem=problem, columns=columns)
    result = _solve_encoding(
        problem=problem, columns=columns, solver=solver, ban_windows=True
    )
    assert result.report.problem_status == "INFEASIBLE"
    assert result.solution.is_failed()


@pytest.mark.parametrize("bunch", (False, True))
def test_merging_adjacent_availability_windows_accepts_invalid_legacy_column(
    solver: str, bunch: bool
) -> None:
    problem = _problem()
    columns = _columns(bunch=bunch, case=0)
    crew = problem.resources[0]
    assert crew.is_available_at(1.25) and crew.is_available_at(1.75)
    assert not crew.available_during(start=1.25, end=1.75)
    naive = _solve_encoding(
        problem=problem, columns=columns, solver=solver, ban_windows=False
    )
    selected = frozenset(p.mode for p in naive.solution.unwrap().placements)
    assert "c-cross" in selected
    assert selected not in _enumerate(problem=problem, columns=columns)


@pytest.mark.parametrize("bunch", (False, True))
def test_ignoring_task_windows_accepts_invalid_legacy_column(
    solver: str, bunch: bool
) -> None:
    problem = _problem()
    columns = _columns(bunch=bunch, case=0)
    naive = _solve_encoding(
        problem=problem,
        columns=columns,
        solver=solver,
        ban_windows=True,
        ban_task_windows=False,
    )
    selected = frozenset(p.mode for p in naive.solution.unwrap().placements)
    assert "c-deadline" in selected
    assert selected not in _enumerate(problem=problem, columns=columns)


def test_bunch_demand_row_is_at_least_one_with_mode_exclusivity(solver: str) -> None:
    problem = GanttProblem(
        tasks=(Task("a", "A", 1.0, deadline=2.0, resource_requirements=(("r", 1.0),)),),
        resources=(Resource("r", "R", 1.0),),
        time_horizon=2.0,
    )
    service = BunchApplicationService(
        solver=MockSolver(),
        task_context=TaskContext(),
        resource_context=ResourceContext(),
        bunch_context=BunchGenerationContext(),
    )
    columns = (
        BunchColumn("first", (("a", 0.0),), "r", -1.0),
        BunchColumn("second", (("a", 1.0),), "r", -1.0),
        BunchColumn("empty", (), "r", -1.0),
    )
    assert service.register(problem).is_ok()
    assert service.add_columns(columns).is_ok()
    model: LinearTriadModel = service._native_triad(relaxation=False).unwrap()
    assert model.sense["demand_a"] == ">="
    assert model.rhs["demand_a"] == 1.0
    assert model.constraints["demand_a"] == {"bunch_first": 1.0, "bunch_second": 1.0}
    for name, row in model.constraints.items():
        if not name.startswith("cap_"):
            continue
        lhs = sum(
            value for variable, value in row.items() if variable.startswith("bunch_")
        )
        if model.sense[name] == "<=":
            assert lhs <= model.rhs[name]
        elif model.sense[name] == ">=":
            assert lhs >= model.rhs[name]
    assert sum(model.objective.values()) == -3.0
    assert columns[-1].is_empty
    assert all("bunch_empty" not in row for row in model.constraints.values())

    native = MetaModelFloat64.create("legacy-set-cover-observation").unwrap()
    try:
        names = tuple(model.variables)
        handles = native.add_variables(
            [
                VariableSpec(
                    name=name,
                    kind=model.variable_types[name],
                    lower=model.lower_bounds[name],
                    upper=(
                        None
                        if not math.isfinite(model.upper_bounds[name])
                        else model.upper_bounds[name]
                    ),
                )
                for name in names
            ]
        ).unwrap()
        variables = dict(zip(names, handles, strict=True))
        native.add_constraints(
            [
                ConstraintSpec(
                    name=name,
                    terms=[(variables[key], value) for key, value in row.items()],
                    relation=model.sense[name],
                    rhs=model.rhs[name],
                )
                for name, row in model.constraints.items()
            ]
        ).unwrap()
        native.set_objective(
            terms=[(variables[key], value) for key, value in model.objective.items()],
            sense="minimize",
        ).unwrap()
        report = native.solve(solver=solver).unwrap()
        values = dict(zip(names, report.values, strict=True))
        assert values["bunch_first"] + values["bunch_second"] == pytest.approx(1.0)
        assert values["bunch_empty"] == pytest.approx(1.0)
        assert report.objective == pytest.approx(-2.0)
    finally:
        native.close().unwrap()

    activity = Activity(
        id="a",
        modes=tuple(
            Mode(
                id=column.bunch_key,
                duration_ns=_nanoseconds(1.0),
                starts_ns=(_nanoseconds(column.task_assignments[0][1]),),
                resources=(),
                cost=_rational(column.cost),
            )
            for column in columns
            if column.task_assignments
        ),
    )
    exactly_one = solve_activity(
        horizon_ns=(0, _nanoseconds(2.0)),
        resources=(),
        activities=(activity,),
        dependencies=(),
        cost_unit=_unit("cost"),
        max_work=1000,
        solver=solver,
    ).unwrap()
    assert Fraction(*exactly_one.solution.unwrap().cost) == -1


def test_float_seconds_do_not_implicitly_mean_rounded_nanoseconds() -> None:
    for value in (0.1, 1e-9):
        assert (value * 1_000_000_000).is_integer()
        assert (_ratio(value) * 1_000_000_000).denominator != 1
    assert _nanoseconds(0.125) == 125_000_000
    assert float("-0.0").as_integer_ratio() == (0, 1)


def test_legacy_validation_rejects_duplicate_task_column_members() -> None:
    resource = Resource("r", "R", 1.0)
    problem = GanttProblem(
        tasks=(Task("a", "A", 1.0, resource_requirements=(("r", 1.0),)),),
        resources=(resource, Resource("r", "Other", 2.0)),
        time_horizon=3.0,
    )
    assert problem.validate().is_ok()
    assert problem.resource_by_key("r") is resource
    task_service = TaskApplicationService(
        solver=MockSolver(),
        task_context=TaskContext(),
        resource_context=ResourceContext(),
    )
    bunch_service = BunchApplicationService(
        solver=MockSolver(),
        task_context=TaskContext(),
        resource_context=ResourceContext(),
        bunch_context=BunchGenerationContext(),
    )
    task_column = TaskColumn("duplicate", (("a", "r", 0.0), ("a", "r", 1.0)), 1.0)
    bunch_column = BunchColumn("duplicate", (("a", 0.0), ("a", 1.0)), "r", 1.0)
    assert task_service.register(problem).is_ok()
    assert bunch_service.register(problem).is_ok()
    # 两条服务路径都拒绝同一任务的不同开始时间，避免同一列出现歧义。
    # Both services reject conflicting starts for duplicate task members.
    assert task_service.add_columns((task_column,)).is_failed()
    assert bunch_service.add_columns((bunch_column,)).is_failed()
