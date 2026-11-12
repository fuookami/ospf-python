"""显式取消及受限任务束覆盖 / Explicit cancellation and restricted bunch coverage."""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import cast

import pytest

from ospf_python import _native
from ospf_python._binding.control import SolveHandle
from ospf_python._binding.gantt_activity import (
    Activity,
    Mode,
    Precedence,
    Resource,
    Row,
    solve_activity,
)
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
    BunchColumn,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


@pytest.fixture(params=("scip", "gurobi10", "gurobi11", "gurobi12"))
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def _rat(value: int | Fraction) -> Rational:
    return Rational.from_value(value).unwrap()


def _unit() -> Unit:
    return Unit.create(name="count", symbol="count", powers=(0,) * 10).unwrap()


def _mode(*, cost: int, start: int = 0, duration: int = 1) -> Mode:
    return Mode(
        id="selected",
        duration_ns=duration,
        starts_ns=(start,),
        resources=(),
        cost=_rat(cost),
    )


def test_optional_activities_return_explicit_cancellations_and_cost(
    solver: str,
) -> None:
    activities = (
        Activity(id="mandatory", modes=(_mode(cost=2),)),
        Activity(id="execute", modes=(_mode(cost=-1),), cancellation_cost=_rat(0)),
        Activity(id="cancel", modes=(_mode(cost=5),), cancellation_cost=_rat(3)),
        Activity(id="no-candidates", modes=(), cancellation_cost=_rat(2)),
    )
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=activities,
        dependencies=(),
        cost_unit=_unit(),
        max_work=1000,
        solver=solver,
    ).unwrap()
    solution = result.solution.unwrap()
    assert {placement.task for placement in solution.placements} == {
        "mandatory",
        "execute",
    }
    assert set(solution.cancelled) == {"cancel", "no-candidates"}
    assert Fraction(*solution.cost) == 6
    assert result.report.objective == pytest.approx(6)
    assert result.report.solution_presence == "OPTIMAL"


@pytest.mark.parametrize("costs", ((-1, -1, -1), (2, 3, -1), (-1, 3, 1), (4, -2, -3)))
def test_optional_choices_encode_restricted_bunch_coverage_and_empty_column(
    solver: str, costs: tuple[int, int, int]
) -> None:
    columns = (
        BunchColumn("first", (("task", 0.0),), "r", float(costs[0])),
        BunchColumn("second", (("task", 1.0),), "r", float(costs[1])),
        BunchColumn("empty", (), "r", float(costs[2])),
    )
    activities = tuple(
        Activity(
            id=column.bunch_key,
            modes=(
                _mode(cost=cost, start=index, duration=0 if column.is_empty else 1),
            ),
            cancellation_cost=_rat(0),
        )
        for index, (column, cost) in enumerate(zip(columns, costs, strict=True))
    )
    coverage = Row(
        id="task-coverage",
        unit=_unit(),
        coefficients=tuple(
            (column.bunch_key, "selected", index, _rat(1))
            for index, column in enumerate(columns)
            if not column.is_empty
        ),
        lower=_rat(1),
    )
    feasible = {
        frozenset(
            column.bunch_key
            for column, flag in zip(columns, flags, strict=True)
            if flag
        ): sum(cost for cost, flag in zip(costs, flags, strict=True) if flag)
        for flags in itertools.product((False, True), repeat=3)
        if flags[0] or flags[1]
    }
    result = solve_activity(
        horizon_ns=(0, 3),
        resources=(),
        activities=activities,
        dependencies=(),
        rows=(coverage,),
        cost_unit=_unit(),
        max_work=1000,
        solver=solver,
    ).unwrap()
    solution = result.solution.unwrap()
    chosen = frozenset(placement.task for placement in solution.placements)
    assert chosen in feasible
    assert set(solution.cancelled) == {column.bunch_key for column in columns} - chosen
    assert Fraction(*solution.cost) == feasible[chosen] == min(feasible.values())
    assert result.report.solution_presence == "OPTIMAL"
    if costs == (-1, -1, -1):
        assert chosen == {"first", "second", "empty"}


@pytest.mark.parametrize("case", range(4))
def test_optional_multitask_bunches_against_exact_subset_enumeration(
    solver: str, case: int
) -> None:
    definitions = (
        ("ab", (("a", 0.0), ("b", 1.0))),
        ("ab-copy", (("a", 0.0), ("b", 1.0))),
        ("a", (("a", 0.0),)),
        ("b", (("b", 1.0),)),
        ("bad-order", (("a", 1.0), ("b", 0.0))),
        ("empty", ()),
        ("late", (("b", 2.0),)),
    )
    columns = tuple(
        BunchColumn(name, assignments, "r", float((case * (i + 1) + i * 3) % 7 - 3))
        for i, (name, assignments) in enumerate(definitions)
    )
    expected: dict[frozenset[str], Fraction] = {}
    for flags in itertools.product((False, True), repeat=len(columns)):
        selected = [column for column, flag in zip(columns, flags, strict=True) if flag]
        selected_assignments = [
            member for column in selected for member in column.task_assignments
        ]
        if any(
            not any(key == task for key, _ in selected_assignments)
            for task in ("a", "b")
        ):
            continue
        if any(
            Fraction.from_float(left) + 1 > Fraction.from_float(right)
            for key_left, left in selected_assignments
            if key_left == "a"
            for key_right, right in selected_assignments
            if key_right == "b"
        ):
            continue
        if any(
            sum(start <= at < start + 1.0 for _, start in selected_assignments) > 2
            for at in (0.0, 1.0, 2.0)
        ):
            continue
        expected[frozenset(column.bunch_key for column in selected)] = sum(
            (Fraction.from_float(column.cost) for column in selected), Fraction()
        )

    activities = []
    members_by_column: dict[str, list[tuple[str, str, int]]] = {}
    rows = []
    for column in columns:
        column_assignments = column.task_assignments or (("empty", 0.0),)
        members_by_column[column.bunch_key] = []
        for index, (task, start) in enumerate(column_assignments):
            identity = f"{column.bunch_key}/{task}"
            start_ns = int(start) * 1_000_000_000
            members_by_column[column.bunch_key].append((identity, task, start_ns))
            activities.append(
                Activity(
                    id=identity,
                    modes=(
                        Mode(
                            id="selected",
                            duration_ns=0 if column.is_empty else 1_000_000_000,
                            starts_ns=(start_ns,),
                            resources=() if column.is_empty else (("r", _rat(1)),),
                            cost=Rational.from_float(column.cost).unwrap()
                            if index == 0
                            else _rat(0),
                        ),
                    ),
                    cancellation_cost=_rat(0),
                )
            )
        anchor = members_by_column[column.bunch_key][0]
        for member in members_by_column[column.bunch_key][1:]:
            rows.append(
                Row(
                    id=f"link/{column.bunch_key}",
                    unit=_unit(),
                    coefficients=(
                        (anchor[0], "selected", anchor[2], _rat(1)),
                        (member[0], "selected", member[2], _rat(-1)),
                    ),
                    lower=_rat(0),
                    upper=_rat(0),
                )
            )
    encoded_members = [
        member for values in members_by_column.values() for member in values
    ]
    for task in ("a", "b"):
        rows.append(
            Row(
                id=f"coverage/{task}",
                unit=_unit(),
                coefficients=tuple(
                    (identity, "selected", start, _rat(1))
                    for identity, key, start in encoded_members
                    if key == task
                ),
                lower=_rat(1),
            )
        )
    for left, left_task, left_start in encoded_members:
        for right, right_task, right_start in encoded_members:
            if (
                left_task == "a"
                and right_task == "b"
                and left_start + 1_000_000_000 > right_start
            ):
                rows.append(
                    Row(
                        id=f"precedence/{left}/{right}",
                        unit=_unit(),
                        coefficients=(
                            (left, "selected", left_start, _rat(1)),
                            (right, "selected", right_start, _rat(1)),
                        ),
                        upper=_rat(1),
                    )
                )
    result = solve_activity(
        horizon_ns=(0, 4_000_000_000),
        resources=(Resource(id="r", capacity=_rat(2), unit=_unit()),),
        activities=tuple(activities),
        dependencies=(),
        rows=tuple(rows),
        cost_unit=_unit(),
        max_work=100_000,
        solver=solver,
    ).unwrap()
    solution = result.solution.unwrap()
    selected_members = {placement.task for placement in solution.placements}
    chosen = frozenset(
        name
        for name, group in members_by_column.items()
        if group[0][0] in selected_members
    )
    assert selected_members == {
        member[0] for name in chosen for member in members_by_column[name]
    }
    assert (
        set(solution.cancelled)
        == {member[0] for member in encoded_members} - selected_members
    )
    assert chosen in expected
    assert Fraction(*solution.cost) == expected[chosen] == min(expected.values())


def test_require_both_presence_is_retained_for_optional_activities(solver: str) -> None:
    activities = (
        Activity(id="a", modes=(_mode(cost=1),), cancellation_cost=_rat(0)),
        Activity(id="b", modes=(_mode(cost=-5, start=1),), cancellation_cost=_rat(0)),
    )
    dependency = Precedence(predecessor="a", successor="b")
    result = solve_activity(
        horizon_ns=(0, 3),
        resources=(),
        activities=activities,
        dependencies=(dependency,),
        cost_unit=_unit(),
        max_work=1000,
        solver=solver,
    ).unwrap()
    solution = result.solution.unwrap()
    assert {item.task for item in solution.placements} == {"a", "b"}
    assert solution.cancelled == ()
    assert Fraction(*solution.cost) == -4
    rows = (
        Row(
            id="cancel-a",
            unit=_unit(),
            coefficients=(("a", "selected", 0, _rat(1)),),
            upper=_rat(0),
        ),
        Row(
            id="execute-b",
            unit=_unit(),
            coefficients=(("b", "selected", 1, _rat(1)),),
            lower=_rat(1),
        ),
    )
    infeasible = solve_activity(
        horizon_ns=(0, 3),
        resources=(),
        activities=activities,
        dependencies=(dependency,),
        rows=rows,
        cost_unit=_unit(),
        max_work=1000,
        solver=solver,
    ).unwrap()
    assert infeasible.report.problem_status == "INFEASIBLE"
    assert infeasible.solution.is_failed()


@pytest.mark.parametrize("case", ("negative", "inexact", "wrong_type"))
def test_invalid_cancellation_cost_never_starts_backend(case: str) -> None:
    cost = _rat(-1) if case == "negative" else _rat(Fraction(1, 10))
    if case == "wrong_type":
        cost = cast("Rational", 1.0)
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(Activity(id="a", modes=(_mode(cost=0),), cancellation_cost=cost),),
        dependencies=(),
        cost_unit=_unit(),
        max_work=100,
        solver="scip",
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is (
        ErrorCode.DATA_LOSS if case == "inexact" else ErrorCode.ILLEGAL_ARGUMENT
    )
    assert handle.phase == "READY"


def test_cancellation_variables_are_included_in_work_budget() -> None:
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(Activity(id="a", modes=(), cancellation_cost=_rat(0)),),
        dependencies=(),
        cost_unit=_unit(),
        max_work=1,
        solver="scip",
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.RESOURCE_EXHAUSTED
    assert handle.phase == "READY"


def test_cancellation_does_not_bypass_native_domain_row_validation(solver: str) -> None:
    activity = Activity(id="a", modes=(_mode(cost=-1),), cancellation_cost=_rat(1))
    row = Row(
        id="sub-tolerance",
        unit=_unit(),
        coefficients=(("a", "selected", 0, _rat(Fraction(1) + Fraction(1, 2**42))),),
        upper=_rat(1),
    )
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(activity,),
        dependencies=(),
        rows=(row,),
        cost_unit=_unit(),
        max_work=1000,
        solver=solver,
    ).unwrap()
    assert result.solution.is_failed()
