"""活动取消扩展行 / Activity extension rows for cancellation decisions."""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.control import SolveHandle
from ospf_python._binding.gantt_activity import Activity, Mode, Row, solve_activity
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


def unit() -> Unit:
    return Unit.create(name="count", symbol="count", powers=(0,) * 10).unwrap()


def activity(name: str, *, execute: int, cancel: int | None) -> Activity:
    return Activity(
        id=name,
        modes=(
            Mode(
                id="selected",
                duration_ns=1,
                starts_ns=(0,),
                resources=(),
                cost=rat(execute),
            ),
        ),
        cancellation_cost=None if cancel is None else rat(cancel),
    )


@pytest.mark.parametrize("costs", ((2, 4, -1, 0), (-2, 0, 5, 2), (1, 3, 1, 3)))
def test_cancellation_and_choice_terms_match_enumeration(
    solver: str, costs: tuple[int, int, int, int]
) -> None:
    execute_a, cancel_a, execute_b, cancel_b = costs
    activities = (
        activity("a", execute=execute_a, cancel=cancel_a),
        activity("b", execute=execute_b, cancel=cancel_b),
    )
    row = Row(
        id="mixed",
        unit=unit(),
        coefficients=(("a", "selected", 0, rat(-1)),),
        cancellation_coefficients=(("a", rat(1)), ("b", rat(2))),
        lower=rat(0),
        upper=rat(2),
    )
    expected = {}
    for a_cancelled, b_cancelled in itertools.product((False, True), repeat=2):
        lhs = (int(a_cancelled) if a_cancelled else -1) + 2 * int(b_cancelled)
        if 0 <= lhs <= 2:
            expected[(a_cancelled, b_cancelled)] = (
                cancel_a if a_cancelled else execute_a
            ) + (cancel_b if b_cancelled else execute_b)
    solved = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=activities,
        dependencies=(),
        rows=(row,),
        cost_unit=unit(),
        max_work=1000,
        solver=solver,
    ).unwrap()
    schedule = solved.solution.unwrap()
    chosen = ("a" in schedule.cancelled, "b" in schedule.cancelled)
    assert chosen in expected
    assert Fraction(*schedule.cost) == expected[chosen] == min(expected.values())
    assert {item.task for item in schedule.placements} == {
        name
        for name, cancelled in zip(("a", "b"), chosen, strict=True)
        if not cancelled
    }
    assert solved.report.solution_presence == "OPTIMAL"


@pytest.mark.parametrize(
    "case",
    ("duplicate", "unknown", "mandatory", "bad_id", "bad_value", "bad_container"),
)
def test_invalid_cancellation_references_do_not_start_solver(
    solver: str, case: str
) -> None:
    one = rat(1)
    terms: Any = {
        "duplicate": (("a", one), ("a", one)),
        "unknown": (("missing", one),),
        "mandatory": (("mandatory", one),),
        "bad_id": ((1, one),),
        "bad_value": (("a", 1),),
        "bad_container": [("a", one)],
    }[case]
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(
            activity("a", execute=0, cancel=0),
            activity("mandatory", execute=0, cancel=None),
        ),
        dependencies=(),
        rows=(
            Row(
                id="r",
                unit=unit(),
                coefficients=(),
                cancellation_coefficients=terms,
                upper=one,
            ),
        ),
        cost_unit=unit(),
        max_work=1000,
        solver=solver,
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert handle.phase == "READY"


def test_inexact_cancellation_coefficient_is_rejected_before_solve(solver: str) -> None:
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(activity("a", execute=0, cancel=0),),
        dependencies=(),
        rows=(
            Row(
                id="r",
                unit=unit(),
                coefficients=(),
                cancellation_coefficients=(("a", rat(2**53 + 1)),),
                upper=rat(2),
            ),
        ),
        cost_unit=unit(),
        max_work=1000,
        solver=solver,
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.DATA_LOSS
    assert handle.phase == "READY"


def test_cancellation_terms_count_towards_work_budget(solver: str) -> None:
    args: dict[str, Any] = dict(
        horizon_ns=(0, 2),
        resources=(),
        activities=(activity("a", execute=0, cancel=0),),
        dependencies=(),
        cost_unit=unit(),
        max_work=11,
        solver=solver,
    )
    assert (
        solve_activity(
            **args, rows=(Row(id="r", unit=unit(), coefficients=(), upper=rat(1)),)
        )
        .unwrap()
        .solution.is_ok()
    )
    handle = SolveHandle()
    result = solve_activity(
        **args,
        rows=(
            Row(
                id="r",
                unit=unit(),
                coefficients=(),
                cancellation_coefficients=(("a", rat(1)),),
                upper=rat(1),
            ),
        ),
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.RESOURCE_EXHAUSTED
    assert handle.phase == "READY"


def test_sub_tolerance_cancellation_row_cannot_publish_schedule(solver: str) -> None:
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=(),
        activities=(Activity(id="a", modes=(), cancellation_cost=rat(0)),),
        dependencies=(),
        rows=(
            Row(
                id="tiny",
                unit=unit(),
                coefficients=(),
                cancellation_coefficients=(
                    ("a", rat(Fraction(1) + Fraction(1, 2**42))),
                ),
                upper=rat(1),
            ),
        ),
        cost_unit=unit(),
        max_work=1000,
        solver=solver,
    ).unwrap()
    assert result.report.solution_presence in ("FEASIBLE", "OPTIMAL")
    assert isinstance(result.solution, Failed)


def test_native_boundary_does_not_overwrite_duplicate_cancellation() -> None:
    one = rat(1)
    measure = unit()
    term = ("a", one._handle)
    value, error = _native._solve_activity(
        horizon=(0, 2),
        resources=[],
        activities=[("a", [], one._handle)],
        dependencies=[],
        rows=[("r", measure._handle, [], [term, term], None, one._handle)],
        cost_unit=measure._handle,
        max_work=100,
        solver="unknown",
        time_limit=None,
        cancellation=None,
        on_progress=None,
    )
    assert value is None
    assert error is not None and error.category == "ILLEGAL_ARGUMENT"
