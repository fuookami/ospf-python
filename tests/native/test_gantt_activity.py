"""有限候选活动的真实后端及独立领域复核 / Real backends and independent finite-activity checks."""

from __future__ import annotations

import itertools
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from fractions import Fraction

import pytest

from ospf_python import _native
from ospf_python._binding.control import SolveHandle, SolveProgress
from ospf_python._binding.gantt_activity import (
    Activity,
    Mode,
    Precedence,
    Resource,
    solve_activity,
)
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
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


def sample() -> tuple[
    tuple[Resource, ...], tuple[Activity, ...], tuple[Precedence, ...]
]:
    resources = (
        Resource(id="crew", capacity=rat(1), unit=unit(), unavailable_ns=((4, 5),)),
        Resource(id="machine", capacity=rat(2), unit=unit("machine")),
    )
    activities = (
        Activity(
            id="a",
            modes=(
                Mode(
                    id="slow",
                    duration_ns=3,
                    starts_ns=(0, 1, 2),
                    resources=(("crew", rat(1)), ("machine", rat(2))),
                    cost=rat(3),
                ),
                Mode(
                    id="fast",
                    duration_ns=2,
                    starts_ns=(0, 1, 2),
                    resources=(("crew", rat(1)), ("machine", rat(2))),
                    cost=rat(8),
                ),
            ),
        ),
        Activity(
            id="b",
            modes=(
                Mode(
                    id="normal",
                    duration_ns=2,
                    starts_ns=(0, 2, 3, 5, 6),
                    resources=(("crew", rat(1)), ("machine", rat(1))),
                    cost=rat(2),
                ),
            ),
        ),
    )
    return (
        resources,
        activities,
        (Precedence(predecessor="a", successor="b", min_gap_ns=1),),
    )


def _enumerate(
    *,
    resources: tuple[Resource, ...],
    activities: tuple[Activity, ...],
    dependencies: tuple[Precedence, ...],
) -> dict[tuple[tuple[str, str, int], ...], Fraction]:
    choices = [
        [
            (activity.id, mode, start)
            for mode in activity.modes
            for start in mode.starts_ns
        ]
        for activity in activities
    ]
    feasible: dict[tuple[tuple[str, str, int], ...], Fraction] = {}
    for selected in itertools.product(*choices):
        times = {
            task: (start, start + mode.duration_ns) for task, mode, start in selected
        }
        if any(
            times[dep.successor][0] < times[dep.predecessor][1] + dep.min_gap_ns
            for dep in dependencies
        ):
            continue
        valid = True
        for resource in resources:
            points = {
                point
                for _, mode, start in selected
                for point in (start, start + mode.duration_ns)
            }
            points.update(
                point for interval in resource.unavailable_ns for point in interval
            )
            for point in points:
                capacity = Fraction(*resource.capacity.as_integer_ratio())
                if any(start <= point < end for start, end in resource.unavailable_ns):
                    capacity = Fraction(0)
                used = sum(
                    (
                        Fraction(*amount.as_integer_ratio())
                        for _, mode, start in selected
                        for name, amount in mode.resources
                        if name == resource.id
                        and start <= point < start + mode.duration_ns
                    ),
                    Fraction(),
                )
                if used > capacity:
                    valid = False
        if valid:
            key = tuple((task, mode.id, start) for task, mode, start in selected)
            feasible[key] = sum(
                (Fraction(*mode.cost.as_integer_ratio()) for _, mode, _ in selected),
                Fraction(),
            )
    return feasible


def test_real_milp_preserves_timing_resources_and_exact_cost(solver: str) -> None:
    resources, activities, dependencies = sample()
    events: list[SolveProgress] = []
    result = solve_activity(
        horizon_ns=(0, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver=solver,
        on_progress=events.append,
    ).unwrap()
    feasible = _enumerate(
        resources=resources, activities=activities, dependencies=dependencies
    )
    solution = result.solution.unwrap()
    key = tuple(
        (entry.task, entry.mode, entry.start_ns) for entry in solution.placements
    )
    assert key in feasible
    assert Fraction(*solution.cost) == feasible[key] == min(feasible.values()) == 5
    assert [
        (entry.task, entry.end_ns - entry.start_ns) for entry in solution.placements
    ] == [("a", 3), ("b", 2)]
    assert result.report.objective == pytest.approx(5)
    assert result.report.solution_presence == "OPTIMAL"
    raw = json.loads(result.report.raw_json)
    assert raw["fingerprints"]["model"] is not None
    assert raw["modelMapping"] is not None
    assert events and events[-1].terminal
    assert all(event.model_identity == result.report.model_identity for event in events)


def test_infeasible_is_a_report_and_not_a_schedule(solver: str) -> None:
    resources, activities, dependencies = sample()
    activities = tuple(
        replace(activity, modes=(replace(activity.modes[0], starts_ns=(0,)),))
        for activity in activities
    )
    result = solve_activity(
        horizon_ns=(0, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver=solver,
    ).unwrap()
    assert result.report.problem_status == "INFEASIBLE"
    assert result.report.solution_presence == "NONE"
    assert isinstance(result.solution, Failed)
    assert result.solution.error.code is ErrorCode.NO_SOLUTION


def test_empty_start_domain_is_infeasible(solver: str) -> None:
    result = solve_activity(
        horizon_ns=(0, 8),
        resources=(),
        activities=(Activity(id="a", modes=()),),
        dependencies=(),
        cost_unit=unit("cost"),
        max_work=100,
        solver=solver,
    ).unwrap()
    assert result.report.problem_status == "INFEASIBLE"
    assert isinstance(result.solution, Failed)


def test_sub_tolerance_overload_never_produces_a_validated_schedule(
    solver: str,
) -> None:
    amount = Fraction(1, 2) + Fraction(1, 2**42)
    assert amount * 2 > 1
    resources = (Resource(id="r", capacity=rat(1), unit=unit()),)
    activities = tuple(
        Activity(
            id=name,
            modes=(
                Mode(
                    id="mode",
                    duration_ns=1,
                    starts_ns=(0,),
                    resources=(("r", rat(amount)),),
                    cost=rat(0),
                ),
            ),
        )
        for name in ("a", "b")
    )
    result = solve_activity(
        horizon_ns=(0, 2),
        resources=resources,
        activities=activities,
        dependencies=(),
        cost_unit=unit("cost"),
        max_work=1000,
        solver=solver,
    ).unwrap()
    assert isinstance(result.solution, Failed)


def test_pre_cancel_is_a_report_and_attempt_is_single_use(solver: str) -> None:
    resources, activities, dependencies = sample()
    handle = SolveHandle()
    handle.cancel(reason="preflight").unwrap()
    kwargs = dict(
        horizon_ns=(0, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver=solver,
        cancellation=handle,
    )
    result = solve_activity(**kwargs).unwrap()
    assert result.report.termination_reason == "CANCELLED"
    assert isinstance(result.solution, Failed)
    assert handle.phase == "FINISHED"
    again = solve_activity(**kwargs)
    assert isinstance(again, Failed)
    assert again.error.code is ErrorCode.FAILED_PRECONDITION


def test_compiled_time_limit_policy_is_not_silently_ignored(solver: str) -> None:
    resources, activities, dependencies = sample()
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver=solver,
        cancellation=handle,
        time_limit=10.25,
    )
    if solver == "scip":
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.NOT_SUPPORTED
        assert handle.phase == "READY"
    else:
        report = result.unwrap().report
        raw = json.loads(report.raw_json)
        assert (
            raw["provenance"]["requestedConfiguration"]["time_limit"] == "Some(10.25)"
        )
        assert (
            raw["provenance"]["effectiveConfiguration"]["time_limit"] == "Some(10.25)"
        )
        assert handle.phase == "FINISHED"


def test_callback_failure_is_preserved(solver: str) -> None:
    resources, activities, dependencies = sample()
    callback_failure = Failed(Err(_code=ErrorCode.APPLICATION_ERROR, _message="test"))
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver=solver,
        cancellation=handle,
        on_progress=lambda _: callback_failure,
    )
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is callback_failure
    assert handle.phase == "FINISHED"


def test_parallel_calls_use_distinct_models(solver: str) -> None:
    resources, activities, dependencies = sample()

    def run() -> tuple[int, Fraction]:
        result = solve_activity(
            horizon_ns=(0, 8),
            resources=resources,
            activities=activities,
            dependencies=dependencies,
            cost_unit=unit("cost"),
            max_work=100_000,
            solver=solver,
        ).unwrap()
        return result.report.model_identity, Fraction(*result.solution.unwrap().cost)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(lambda _: run(), range(2))
    assert first[0] != second[0]
    assert first[1] == second[1] == 5


@pytest.mark.parametrize("case", range(12))
def test_tiny_domains_against_independent_enumeration(solver: str, case: int) -> None:
    resources = (
        Resource(
            id="r",
            capacity=rat(Fraction(2 + case % 2, 2)),
            unit=unit(),
            unavailable_ns=((3, 4),) if case % 3 == 0 else (),
        ),
    )
    activities = tuple(
        Activity(
            id=name,
            modes=tuple(
                Mode(
                    id=f"m{mode}",
                    duration_ns=1 + mode,
                    starts_ns=(0, 2, 4, 6),
                    resources=(("r", rat(Fraction(1 + (case + task + mode) % 2, 2))),),
                    cost=rat((case + 2 * task + 3 * mode) % 7 - 2),
                )
                for mode in range(2)
            ),
        )
        for task, name in enumerate(("a", "b", "c"))
    )
    dependencies = (
        Precedence(predecessor="a", successor="b", min_gap_ns=case % 3 - 1),
        Precedence(predecessor="b", successor="c", min_gap_ns=(case // 3) % 3 - 1),
    )
    expected = _enumerate(
        resources=resources, activities=activities, dependencies=dependencies
    )
    result = solve_activity(
        horizon_ns=(0, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=200_000,
        solver=solver,
    ).unwrap()
    if not expected:
        assert result.report.problem_status == "INFEASIBLE"
        assert isinstance(result.solution, Failed)
    else:
        solution = result.solution.unwrap()
        key = tuple(
            (entry.task, entry.mode, entry.start_ns) for entry in solution.placements
        )
        assert key in expected
        assert Fraction(*solution.cost) == expected[key] == min(expected.values())


def test_negative_nanosecond_timestamps_preserve_exact_values(solver: str) -> None:
    activity = Activity(
        id="a",
        modes=(
            Mode(id="m", duration_ns=3, starts_ns=(-9,), resources=(), cost=rat(1)),
        ),
    )
    result = solve_activity(
        horizon_ns=(-10, 0),
        resources=(),
        activities=(activity,),
        dependencies=(),
        cost_unit=unit("cost"),
        max_work=100,
        solver=solver,
    ).unwrap()
    placement = result.solution.unwrap().placements[0]
    assert (placement.start_ns, placement.end_ns) == (-9, -6)


@pytest.mark.parametrize("origin", (-(2**63), -(2**53) - 1, 0, 2**53 + 1, 2**63 - 9))
def test_time_translation_preserves_exact_schedule(solver: str, origin: int) -> None:
    resources, activities, dependencies = sample()
    resources = tuple(
        replace(
            resource,
            unavailable_ns=tuple(
                (start + origin, end + origin) for start, end in resource.unavailable_ns
            ),
        )
        for resource in resources
    )
    activities = tuple(
        replace(
            activity,
            modes=tuple(
                replace(
                    mode, starts_ns=tuple(start + origin for start in mode.starts_ns)
                )
                for mode in activity.modes
            ),
        )
        for activity in activities
    )
    expected = _enumerate(
        resources=resources, activities=activities, dependencies=dependencies
    )
    result = solve_activity(
        horizon_ns=(origin, origin + 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver=solver,
    ).unwrap()
    solution = result.solution.unwrap()
    key = tuple((item.task, item.mode, item.start_ns) for item in solution.placements)
    assert key in expected
    assert Fraction(*solution.cost) == expected[key] == min(expected.values()) == 5
    durations = {
        (activity.id, mode.id): mode.duration_ns
        for activity in activities
        for mode in activity.modes
    }
    assert all(
        item.end_ns == item.start_ns + durations[item.task, item.mode]
        for item in solution.placements
    )


@pytest.mark.parametrize("source", ("cost", "grouped_resource"))
def test_inexact_compilation_is_rejected_before_backend_attempt(
    solver: str, source: str
) -> None:
    resources, activities, dependencies = sample()
    first = activities[0].modes[0]
    if source == "cost":
        first = replace(first, cost=rat(Fraction(1, 10)))
    else:
        first = replace(
            first, resources=(("crew", rat(1)), ("crew", rat(Fraction(1, 2**53))))
        )
    activities = (replace(activities[0], modes=(first,)), activities[1])
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver=solver,
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.DATA_LOSS
    assert handle.phase == "READY"


@pytest.mark.parametrize(
    "case",
    (
        "budget",
        "duplicate_resource",
        "duplicate_task",
        "unknown_resource",
        "unknown_task",
        "outside",
        "duplicate_start",
        "negative_duration",
        "overflow",
        "affine",
    ),
)
def test_invalid_input_does_not_start_backend(case: str) -> None:
    resources, activities, dependencies = sample()
    horizon = (0, 8)
    max_work = 100_000
    cost_unit = unit("cost")
    first = activities[0].modes[0]
    if case == "budget":
        max_work = 1
    elif case == "duplicate_resource":
        resources += (resources[0],)
    elif case == "duplicate_task":
        activities += (activities[0],)
    elif case == "unknown_resource":
        first = replace(first, resources=(("absent", rat(1)),))
    elif case == "unknown_task":
        dependencies = (Precedence(predecessor="a", successor="absent"),)
    elif case == "outside":
        first = replace(first, starts_ns=(7,))
    elif case == "duplicate_start":
        first = replace(first, starts_ns=(0, 0))
    elif case == "negative_duration":
        first = replace(first, duration_ns=-1)
    elif case == "overflow":
        first = replace(first, starts_ns=(2**63 - 1,))
    else:
        cost_unit = Unit.create(
            name="affine", symbol="point", powers=(0,) * 10, offset=0
        ).unwrap()
    activities = (replace(activities[0], modes=(first,)), *activities[1:])
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=horizon,
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=cost_unit,
        max_work=max_work,
        solver="scip",
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is (
        ErrorCode.RESOURCE_EXHAUSTED if case == "budget" else ErrorCode.ILLEGAL_ARGUMENT
    )
    assert handle.phase == "READY"


def test_unknown_backend_does_not_fallback_or_consume_handle() -> None:
    resources, activities, dependencies = sample()
    handle = SolveHandle()
    result = solve_activity(
        horizon_ns=(0, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver="unknown",
        cancellation=handle,
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.NOT_SUPPORTED
    assert handle.phase == "READY"


def test_python_boundary_rejects_bool_nanosecond() -> None:
    resources, activities, dependencies = sample()
    result = solve_activity(
        horizon_ns=(False, 8),
        resources=resources,
        activities=activities,
        dependencies=dependencies,
        cost_unit=unit("cost"),
        max_work=100_000,
        solver="scip",
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
