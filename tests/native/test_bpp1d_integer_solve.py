"""真实后端的精确 BPP1D 主模型边界 / Exact BPP1D master boundary with real backends."""

from __future__ import annotations

import itertools
import json
import threading
from collections import Counter
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from functools import cache
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.bpp1d import BinSpec, ItemSpec, PackingContext
from ospf_python._binding.control import SolveHandle, SolveProgress
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def _r(value: int | float | Fraction) -> Rational:
    if isinstance(value, float):
        return Rational.from_float(value).unwrap()
    return Rational.from_value(value).unwrap()


def _context(
    *,
    lengths: Mapping[str, int | float | Fraction],
    capacity: int | float | Fraction,
    amounts: dict[str, int] | None = None,
    inventory: int | None = None,
    cost: int | float | Fraction = 1,
    objective: str = "bin_count",
) -> PackingContext:
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    return PackingContext.create(
        items=[
            ItemSpec(
                id=id_,
                length=_r(value),
                weight=_r(0),
                amount=(amounts or {}).get(id_, 1),
            )
            for id_, value in lengths.items()
        ],
        bins=[
            BinSpec(
                id="bin",
                length=_r(capacity),
                max_weight=_r(0),
                cost=_r(cost),
                inventory=inventory,
            )
        ],
        spacing=_r(0),
        length_unit=length,
        weight_unit=mass,
        objective=objective,
    ).unwrap()


def test_exact_candidate_to_real_solver_and_exact_placement(solver: str) -> None:
    lengths = {"a": 0.1, "c": 0.2, "b": 0.03}
    ctx = _context(lengths=lengths, capacity=0.33)
    events: list[SolveProgress] = []
    result = ctx.solve(
        solver=solver,
        max_patterns=100,
        max_nodes=1000,
        expansion_limit=3,
        on_progress=events.append,
    ).unwrap()
    assert result.candidate_complete and result.visited_nodes > 0
    assert len(result.columns) == 7
    assert result.report.termination_reason == "COMPLETED"
    assert len(result.report.values) == len(result.columns)
    assert result.report.model_generation == 0
    raw = json.loads(result.report.raw_json)
    assert raw["modelMapping"] is not None and raw["fingerprints"]["model"] is not None
    assert events and events[-1].terminal
    assert all(event.model_identity == result.report.model_identity for event in events)

    solution = result.solution.unwrap()
    assert solution.usages == [("bin", {"a": 1, "b": 1, "c": 1}, 1)]
    assert {
        (bin_id, tuple(sorted(counts.items()))): int(value)
        for (bin_id, counts), value in zip(
            result.columns, result.report.values, strict=True
        )
        if value
    } == {("bin", (("a", 1), ("b", 1), ("c", 1))): 1}
    plans, _, _, total, net, objective = solution.packed
    assert len(plans) == 1
    cursor = Fraction()
    counts: Counter[str] = Counter()
    for id_, start, piece_length in plans[0][2]:
        assert Fraction(*start) == cursor
        assert Fraction(*piece_length) == Fraction.from_float(lengths[id_])
        cursor += Fraction(*piece_length)
        counts[id_] += 1
    assert counts == Counter({"a": 1, "b": 1, "c": 1})
    assert cursor == Fraction(*net) == Fraction(*total) == Fraction.from_float(0.33)
    assert Fraction(*objective) == 1
    assert Fraction(*solution.model_objective) == 1
    assert solution.indicators == {}


def test_backend_objective_is_not_the_exact_recomputed_cost(solver: str) -> None:
    ctx = _context(
        lengths={"a": 1},
        capacity=1,
        amounts={"a": 3},
        cost=0.1,
        objective="cost",
    )
    result = ctx.solve(
        solver=solver, max_patterns=10, max_nodes=100, expansion_limit=3
    ).unwrap()
    exact = Fraction(*result.solution.unwrap().packed[5])
    assert exact == 3 * Fraction.from_float(0.1)
    assert Fraction(*result.solution.unwrap().model_objective) == exact
    assert result.report.objective is not None
    assert Fraction.from_float(result.report.objective) - exact == Fraction(1, 2**55)


@pytest.mark.parametrize(
    ("objective", "capacity", "cost"),
    [("cost", 1, Fraction(1, 10)), ("consumed_length", Fraction(1, 3), 1)],
)
def test_strict_model_conversion_fails_before_consuming_handle(
    solver: str, objective: str, capacity: int | Fraction, cost: int | Fraction
) -> None:
    ctx = _context(
        lengths={"a": capacity}, capacity=capacity, cost=cost, objective=objective
    )
    control = SolveHandle()
    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
    )
    assert isinstance(result, Failed)
    assert "precision" in result.error.message.lower()
    assert control.phase == "READY"


def test_truncated_pool_and_expansion_failure_keep_report(solver: str) -> None:
    ctx = _context(lengths={"a": 1}, capacity=2, amounts={"a": 2})
    result = ctx.solve(
        solver=solver, max_patterns=1, max_nodes=100, expansion_limit=2
    ).unwrap()
    assert not result.candidate_complete and len(result.columns) == 1
    assert result.solution.unwrap().usages == [("bin", {"a": 1}, 2)]
    assert len(result.solution.unwrap().packed[0]) == 2

    no_expansion = ctx.solve(
        solver=solver, max_patterns=10, max_nodes=100, expansion_limit=1
    ).unwrap()
    assert no_expansion.report.solution_presence == "OPTIMAL"
    assert no_expansion.solution.is_failed()
    assert json.loads(no_expansion.report.raw_json)["solution"] is not None


def test_infeasible_inventory_is_a_report_not_a_solution(solver: str) -> None:
    ctx = _context(lengths={"a": 1}, capacity=1, amounts={"a": 3}, inventory=2)
    result = ctx.solve(
        solver=solver, max_patterns=10, max_nodes=100, expansion_limit=3
    ).unwrap()
    assert result.candidate_complete
    assert result.report.problem_status == "INFEASIBLE"
    assert result.report.solution_presence == "NONE"
    assert result.solution.is_failed()
    assert json.loads(result.report.raw_json)["solution"] is None


def test_empty_and_truncated_pools_do_not_share_an_infeasibility_claim(
    solver: str,
) -> None:
    empty = (
        _context(lengths={}, capacity=1)
        .solve(solver=solver, max_patterns=10, max_nodes=100, expansion_limit=0)
        .unwrap()
    )
    assert empty.candidate_complete and empty.columns == []
    assert empty.solution.unwrap().packed == ([], [], {}, (0, 1), (0, 1), (0, 1))

    for length, nodes, complete in ((2, 100, True), (1, 1, False)):
        ctx = _context(lengths={"a": length}, capacity=1)
        result = ctx.solve(
            solver=solver, max_patterns=10, max_nodes=nodes, expansion_limit=1
        ).unwrap()
        assert result.candidate_complete is complete and result.columns == []
        assert result.report.problem_status == "INFEASIBLE"
        assert result.solution.is_failed()


@pytest.mark.parametrize("objective", ["bin_count", "consumed_length", "cost"])
def test_multiple_bins_match_small_independent_exact_enumeration(
    solver: str, objective: str
) -> None:
    lengths = (Fraction(1), Fraction(2), Fraction(3))
    weights = (1, 2, 0)
    demand = (2, 1, 1)
    bins = (("small", 3, 3, Fraction(3), 2), ("big", 5, 3, Fraction(5), 2))
    spacing = Fraction(1, 2)
    length_unit = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass_unit = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    items = [
        ItemSpec(
            id=chr(97 + i), length=_r(length), weight=_r(weights[i]), amount=demand[i]
        )
        for i, length in enumerate(lengths)
    ]
    bin_specs = [
        BinSpec(
            id=id_,
            length=_r(capacity),
            max_weight=_r(weight),
            cost=_r(cost),
            inventory=stock,
        )
        for id_, capacity, weight, cost, stock in bins
    ]
    ctx = PackingContext.create(
        items=items,
        bins=bin_specs,
        spacing=_r(spacing),
        length_unit=length_unit,
        weight_unit=mass_unit,
        objective=objective,
    ).unwrap()

    candidates: list[tuple[int, tuple[int, ...], Fraction]] = []
    for index, (_, capacity, max_weight, cost, _) in enumerate(bins):
        for counts in itertools.product(*(range(n + 1) for n in demand)):
            pieces = sum(counts)
            if (
                pieces
                and sum(n * length for n, length in zip(counts, lengths, strict=True))
                + spacing * (pieces - 1)
                <= capacity
                and sum(n * weight for n, weight in zip(counts, weights, strict=True))
                <= max_weight
            ):
                metric = {
                    "bin_count": Fraction(1),
                    "consumed_length": Fraction(capacity),
                    "cost": cost,
                }[objective]
                candidates.append((index, counts, metric))

    @cache
    def minimum(remaining: tuple[int, ...], stock: tuple[int, ...]) -> Fraction | None:
        if not any(remaining):
            return Fraction()
        choices = []
        for index, counts, metric in candidates:
            if not stock[index] or any(
                n > left for n, left in zip(counts, remaining, strict=True)
            ):
                continue
            next_stock = list(stock)
            next_stock[index] -= 1
            tail = minimum(
                tuple(left - n for n, left in zip(counts, remaining, strict=True)),
                tuple(next_stock),
            )
            if tail is not None:
                choices.append(metric + tail)
        return min(choices) if choices else None

    result = ctx.solve(
        solver=solver, max_patterns=1000, max_nodes=10000, expansion_limit=sum(demand)
    ).unwrap()
    assert result.candidate_complete
    expected_candidates = {
        (bins[index][0], tuple((chr(97 + i), n) for i, n in enumerate(counts) if n))
        for index, counts, _ in candidates
    }
    assert {
        (id_, tuple(sorted(counts.items()))) for id_, counts in result.columns
    } == expected_candidates
    solution = result.solution.unwrap()
    assert Fraction(*solution.packed[5]) == minimum(demand, (2, 2))
    actual: Counter[str] = Counter()
    stock_used: Counter[str] = Counter()
    for bin_id, amounts, count in solution.usages:
        stock_used[bin_id] += count
        for id_, n in amounts.items():
            actual[id_] += n * count
    assert actual == Counter(dict(zip(("a", "b", "c"), demand, strict=True)))
    assert stock_used["small"] <= 2 and stock_used["big"] <= 2
    for _, bin_id, placements in solution.packed[0]:
        _, capacity, max_weight, _, _ = next(bin_ for bin_ in bins if bin_[0] == bin_id)
        cursor = Fraction()
        total_weight = 0
        for index, (id_, start, length) in enumerate(placements):
            expected_start = cursor + (spacing if index else 0)
            assert Fraction(*start) == expected_start
            assert Fraction(*length) == lengths[ord(id_) - ord("a")]
            cursor = expected_start + Fraction(*length)
            total_weight += weights[ord(id_) - ord("a")]
        assert cursor <= capacity and total_weight <= max_weight


def test_large_count_is_not_silently_rounded(solver: str) -> None:
    ctx = _context(lengths={"a": 1}, capacity=1, amounts={"a": 2**53 + 1})
    control = SolveHandle()
    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=0,
        cancellation=control,
    )
    assert isinstance(result, Failed)
    assert "precision" in result.error.message.lower()
    assert control.phase == "READY"


def test_cancellation_requested_from_progress_is_preserved(solver: str) -> None:
    ctx = _context(lengths={"a": 1}, capacity=1)
    control = SolveHandle()
    events: list[SolveProgress] = []

    def callback(event: SolveProgress) -> None:
        events.append(event)
        if not event.terminal and not control.is_cancelled:
            assert control.cancel(reason="stop from progress").unwrap()

    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
        on_progress=callback,
    ).unwrap()
    assert result.report.termination_reason == "CANCELLED"
    assert control.phase == "FINISHED" and control.cancellation_preceded_completion
    assert events and events[-1].terminal


def test_cross_thread_cancellation_during_backend_callback(solver: str) -> None:
    ctx = _context(lengths={str(i): 1 for i in range(9)}, capacity=4)
    control = SolveHandle()
    in_backend, release = threading.Event(), threading.Event()

    def callback(event: SolveProgress) -> None:
        if event.source == "backend" and not in_backend.is_set():
            in_backend.set()
            assert release.wait(timeout=10)

    with ThreadPoolExecutor(max_workers=1) as pool:
        job = pool.submit(
            ctx.solve,
            solver=solver,
            max_patterns=1000,
            max_nodes=10000,
            expansion_limit=9,
            cancellation=control,
            on_progress=callback,
        )
        try:
            assert in_backend.wait(timeout=10)
            assert control.phase == "RUNNING"
            assert ctx.generate_patterns(max_patterns=1000, max_nodes=10000).is_ok()
            assert control.cancel(origin="external", reason="native active").unwrap()
        finally:
            release.set()
        result = job.result(timeout=10).unwrap()
    assert result.report.termination_reason == "CANCELLED"
    assert control.phase == "FINISHED" and control.cancellation_preceded_completion


def test_gurobi_compiled_limit_is_recorded(solver: str) -> None:
    if solver == "scip":
        pytest.skip("SCIP compiled-model limits are explicitly rejected")
    ctx = _context(lengths={"a": 1}, capacity=1)
    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        time_limit=10.25,
    ).unwrap()
    provenance = json.loads(result.report.raw_json)["provenance"]
    assert provenance["requestedConfiguration"]["time_limit"] == "Some(10.25)"
    assert provenance["effectiveConfiguration"]["time_limit"] == "Some(10.25)"
    assert result.solution.is_ok()


def test_cancel_and_reentry_preserve_attempt_semantics(solver: str) -> None:
    ctx = _context(lengths={"a": 1}, capacity=1)
    control = SolveHandle()
    assert control.cancel(reason="before solve").unwrap()
    events: list[SolveProgress] = []

    def callback(event: SolveProgress) -> None:
        events.append(event)
        assert ctx.generate_patterns(max_patterns=10, max_nodes=100).is_ok()

    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
        on_progress=callback,
    ).unwrap()
    assert result.report.termination_reason == "CANCELLED"
    assert result.solution.is_failed()
    assert control.phase == "FINISHED" and control.cancellation_preceded_completion
    assert events and events[-1].terminal
    assert ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
    ).is_failed()


def test_callback_failure_preserves_domain_error_and_context_recovers(
    solver: str,
) -> None:
    ctx = _context(lengths={"a": 1}, capacity=1)
    error: ExErr[str, dict[str, int]] = ExErr(
        _code=ErrorCode.PERMISSION_DENIED,
        _message="领域拒绝 / Domain denied",
        value={"item": 1},
    )
    returned: Failed[None, str, ExErr[str, dict[str, int]]] = Failed(error)
    control = SolveHandle()
    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
        on_progress=lambda _: returned,
    )
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is returned
    assert control.phase == "FINISHED"
    assert (
        ctx.solve(solver=solver, max_patterns=10, max_nodes=100, expansion_limit=1)
        .unwrap()
        .solution.is_ok()
    )


def test_invalid_arguments_and_compiled_scip_limit_do_not_consume_handle() -> None:
    ctx = _context(lengths={"a": 1}, capacity=1)
    control = SolveHandle()
    base: dict[str, Any] = dict(
        solver="scip",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
    )
    for changes in (
        {"solver": "unknown"},
        {"max_patterns": 0},
        {"max_nodes": 0},
        {"max_patterns": True},
        {"expansion_limit": -1},
        {"time_limit": 0},
        {"on_progress": 123},
    ):
        assert ctx.solve(**(base | changes)).is_failed()
        assert control.phase == "READY"
    if "scip" in _native.build_info()["native_solvers"].split(","):
        assert ctx.solve(**(base | {"time_limit": 10})).is_failed()
        assert control.phase == "READY"
        assert ctx.solve(**base).unwrap().solution.is_ok()
