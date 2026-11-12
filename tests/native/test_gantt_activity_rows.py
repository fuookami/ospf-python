"""活动扩展行和多任务列表达 / Activity extension rows and multi-task column encoding."""

from __future__ import annotations

import itertools
from dataclasses import replace
from fractions import Fraction
from typing import Any, cast

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
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


@pytest.fixture(params=("scip", "gurobi10", "gurobi11", "gurobi12"))
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def rat(value: int | Fraction) -> Rational:
    return Rational.from_value(value).unwrap()


def unit(name: str = "count") -> Unit:
    return Unit.create(name=name, symbol=name, powers=(0,) * 10).unwrap()


def test_rows_filter_candidates_using_both_bounds(solver: str) -> None:
    activity = Activity(
        id="a",
        modes=tuple(
            Mode(id=name, duration_ns=1, starts_ns=(0,), resources=(), cost=rat(cost))
            for name, cost in (("low", -2), ("middle", 1), ("high", -3))
        ),
    )
    row = Row(
        id="business-rule",
        unit=unit(),
        coefficients=tuple(
            ("a", name, 0, rat(value))
            for name, value in (("low", -1), ("middle", 1), ("high", 2))
        ),
        lower=rat(0),
        upper=rat(1),
    )
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(activity,),
        dependencies=(),
        rows=(row,),
        cost_unit=unit("cost"),
        max_work=1000,
        solver=solver,
    ).unwrap()
    solution = result.solution.unwrap()
    assert [(p.task, p.mode, p.start_ns) for p in solution.placements] == [
        ("a", "middle", 0)
    ]
    assert solution.cost == (1, 1)


@pytest.mark.parametrize("origin", (-(2**63), -(2**53) - 1, 2**53 + 1, 2**63 - 3))
def test_row_choice_identity_keeps_exact_nanoseconds(solver: str, origin: int) -> None:
    activity = Activity(
        id="a",
        modes=(
            Mode(
                id="m",
                duration_ns=1,
                starts_ns=(origin, origin + 1),
                resources=(),
                cost=rat(0),
            ),
        ),
    )
    row = Row(
        id="choose-second",
        unit=unit(),
        coefficients=(("a", "m", origin + 1, rat(1)),),
        lower=rat(1),
    )
    result = solve_activity(
        horizon_ns=(origin, origin + 2),
        resources=(),
        activities=(activity,),
        dependencies=(),
        rows=(row,),
        cost_unit=unit("cost"),
        max_work=100,
        solver=solver,
    ).unwrap()
    placement = result.solution.unwrap().placements[0]
    assert (placement.start_ns, placement.end_ns) == (origin + 1, origin + 2)


@pytest.mark.parametrize("case", range(12))
def test_multitask_columns_against_independent_subset_enumeration(
    solver: str, case: int
) -> None:
    columns = (
        ("ab-early", (("a", 0), ("b", 1))),
        ("ab-late", (("a", 0), ("b", 2))),
        ("bc", (("b", 1), ("c", 3))),
        ("ac", (("a", 0), ("c", 3))),
        ("a", (("a", 0),)),
        ("b", (("b", 1),)),
        ("c-late", (("c", 4),)),
        ("c-conflict", (("c", 0),)),
        ("ab-overlap", (("a", 0), ("b", 0))),
    )
    costs = {
        name: (case * (index + 1) + index * 3) % 9 - 3
        for index, (name, _) in enumerate(columns)
    }
    limited = {"ab-early", "ab-late", "bc", "ac", "ab-overlap"}
    limit = case % 3
    unavailable = ((4, 5),) if case % 2 else ()
    expected: dict[frozenset[str], int] = {}
    for flags in itertools.product((False, True), repeat=len(columns)):
        selected = [column for column, flag in zip(columns, flags, strict=True) if flag]
        names = frozenset(name for name, _ in selected)
        assignments = [assignment for _, group in selected for assignment in group]
        if any(sum(task == name for task, _ in assignments) != 1 for name in "abc"):
            continue
        times = dict(assignments)
        if times["b"] < times["a"] + 1:
            continue
        if any(sum(start == at for _, start in assignments) > 1 for at in range(5)):
            continue
        if any(
            start <= at < end for _, at in assignments for start, end in unavailable
        ):
            continue
        if len(names & limited) > limit:
            continue
        expected[names] = sum(costs[name] for name in names)

    activities = tuple(
        Activity(
            id=task,
            modes=tuple(
                Mode(
                    id=name,
                    duration_ns=1,
                    starts_ns=(start,),
                    resources=(("crew", rat(1)),),
                    cost=rat(costs[name] if group[0][0] == task else 0),
                )
                for name, group in columns
                for member, start in group
                if member == task
            ),
        )
        for task in "abc"
    )
    identity_unit = unit("identity")
    rows = tuple(
        Row(
            id=f"link-{name}-{member}",
            unit=identity_unit,
            coefficients=(
                (group[0][0], name, group[0][1], rat(1)),
                (member, name, start, rat(-1)),
            ),
            lower=rat(0),
            upper=rat(0),
        )
        for name, group in columns
        for member, start in group[1:]
    ) + (
        Row(
            id="limit",
            unit=identity_unit,
            coefficients=tuple(
                (group[0][0], name, group[0][1], rat(1))
                for name, group in columns
                if name in limited
            ),
            upper=rat(limit),
        ),
    )
    result = solve_activity(
        horizon_ns=(0, 5),
        resources=(
            Resource(
                id="crew", capacity=rat(1), unit=unit(), unavailable_ns=unavailable
            ),
        ),
        activities=activities,
        dependencies=(Precedence(predecessor="a", successor="b"),),
        rows=rows,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver=solver,
    ).unwrap()
    if not expected:
        assert result.report.problem_status == "INFEASIBLE"
        assert isinstance(result.solution, Failed)
        return
    solution = result.solution.unwrap()
    selected_names = frozenset(placement.mode for placement in solution.placements)
    assert selected_names in expected
    assert all(
        (placement.task, placement.start_ns) in dict(columns)[placement.mode]
        for placement in solution.placements
    )
    assert sorted((p.task, p.mode, p.start_ns) for p in solution.placements) == sorted(
        (task, name, start)
        for name, assignments in columns
        if name in selected_names
        for task, start in assignments
    )
    assert (
        Fraction(*solution.cost) == expected[selected_names] == min(expected.values())
    )
    assert result.report.solution_presence == "OPTIMAL"
    assert result.report.objective == pytest.approx(expected[selected_names])


@pytest.mark.parametrize("upper", (0, -1))
def test_empty_coefficient_row_has_its_constant_semantics(
    solver: str, upper: int
) -> None:
    activity = Activity(
        id="a",
        modes=(Mode(id="m", duration_ns=1, starts_ns=(0,), resources=(), cost=rat(0)),),
    )
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(activity,),
        dependencies=(),
        rows=(Row(id="constant", unit=unit(), coefficients=(), upper=rat(upper)),),
        cost_unit=unit("cost"),
        max_work=100,
        solver=solver,
    ).unwrap()
    if upper == 0:
        assert result.solution.unwrap().placements[0].task == "a"
    else:
        assert result.report.problem_status == "INFEASIBLE"
        assert isinstance(result.solution, Failed)


def test_row_work_is_included_in_budget(solver: str) -> None:
    activity = Activity(
        id="a",
        modes=(Mode(id="m", duration_ns=1, starts_ns=(0,), resources=(), cost=rat(0)),),
    )
    args: dict[str, Any] = dict(
        horizon_ns=(0, 2),
        resources=(),
        activities=(activity,),
        dependencies=(),
        cost_unit=unit("cost"),
        max_work=3,
        solver=solver,
    )
    assert solve_activity(**args).unwrap().solution.is_ok()
    handle = SolveHandle()
    result = solve_activity(
        **args,
        rows=(
            Row(
                id="r", unit=unit(), coefficients=(("a", "m", 0, rat(1)),), upper=rat(1)
            ),
        ),
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.RESOURCE_EXHAUSTED
    assert handle.phase == "READY"


def test_native_boundary_does_not_overwrite_duplicate_choice() -> None:
    one = rat(1)
    zero = rat(0)
    measure = unit()
    term = ("a", "m", 0, one._handle)
    value, error = _native._solve_activity(
        horizon=(0, 2),
        resources=[],
        activities=[("a", [("m", 1, [0], [], zero._handle)], None)],
        dependencies=[],
        rows=[("row", measure._handle, [term, term], [], None, one._handle)],
        cost_unit=measure._handle,
        max_work=100,
        solver="unknown",
        time_limit=None,
        cancellation=None,
        on_progress=None,
    )
    assert value is None
    assert error is not None and error.category == "ILLEGAL_ARGUMENT"


def test_sub_tolerance_row_violation_cannot_publish_schedule(solver: str) -> None:
    activity = Activity(
        id="a",
        modes=(Mode(id="m", duration_ns=1, starts_ns=(0,), resources=(), cost=rat(0)),),
    )
    row = Row(
        id="tiny",
        unit=unit(),
        coefficients=(("a", "m", 0, rat(Fraction(1) + Fraction(1, 2**42))),),
        upper=rat(1),
    )
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(activity,),
        dependencies=(),
        rows=(row,),
        cost_unit=unit("cost"),
        max_work=100,
        solver=solver,
    ).unwrap()
    assert isinstance(result.solution, Failed)


@pytest.mark.parametrize(
    "case",
    (
        "duplicate_row",
        "duplicate_choice",
        "unknown_choice",
        "missing_bounds",
        "inverted_bounds",
        "affine_unit",
        "inexact_coefficient",
        "inexact_bound",
        "invalid_term",
        "boolean_start",
        "overflow_start",
        "budget",
    ),
)
def test_invalid_row_never_starts_backend(case: str) -> None:
    activity = Activity(
        id="a",
        modes=(Mode(id="m", duration_ns=1, starts_ns=(0,), resources=(), cost=rat(0)),),
    )
    row = Row(
        id="row", unit=unit(), coefficients=(("a", "m", 0, rat(1)),), upper=rat(1)
    )
    rows: tuple[Any, ...] = (row,)
    max_work = 1000
    if case == "duplicate_row":
        rows += (row,)
    elif case == "duplicate_choice":
        rows = (replace(row, coefficients=row.coefficients * 2),)
    elif case == "unknown_choice":
        rows = (replace(row, coefficients=(("a", "m", 1, rat(1)),)),)
    elif case == "missing_bounds":
        rows = (replace(row, upper=None),)
    elif case == "inverted_bounds":
        rows = (replace(row, lower=rat(2)),)
    elif case == "affine_unit":
        rows = (
            replace(
                row,
                unit=Unit.create(
                    name="affine", symbol="a", powers=(0,) * 10, offset=0
                ).unwrap(),
            ),
        )
    elif case == "inexact_coefficient":
        rows = (replace(row, coefficients=(("a", "m", 0, rat(Fraction(1, 10))),)),)
    elif case == "inexact_bound":
        rows = (replace(row, upper=rat(Fraction(1, 10))),)
    elif case == "invalid_term":
        malformed = cast("tuple[tuple[str, str, int, Rational], ...]", (("a", "m", 0),))
        rows = (replace(row, coefficients=malformed),)
    elif case == "boolean_start":
        rows = (replace(row, coefficients=(("a", "m", False, rat(1)),)),)
    elif case == "overflow_start":
        rows = (replace(row, coefficients=(("a", "m", 2**63, rat(1)),)),)
    else:
        max_work = 1
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(activity,),
        dependencies=(),
        rows=rows,
        cost_unit=unit("cost"),
        max_work=max_work,
        solver="scip",
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is (
        ErrorCode.RESOURCE_EXHAUSTED
        if case == "budget"
        else ErrorCode.DATA_LOSS
        if case.startswith("inexact")
        else ErrorCode.ILLEGAL_ARGUMENT
    )
    assert handle.phase == "READY"
