"""BPP1D 精确列池事务及主问题合同 / Exact BPP1D pool and master contracts."""

from __future__ import annotations

import gc
import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast

import pytest

from ospf_python import _native
from ospf_python._binding.bpp1d import (
    AuxiliaryVariable,
    BinSpec,
    ExtensionConstraint,
    ItemSpec,
    PackingContext,
    PatternExtension,
    PatternExtensionSpec,
    PatternExtraction,
    PatternPool,
    PatternRegistration,
)
from ospf_python._binding.control import SolveHandle, SolveProgress
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Result

MIXED = ("bin", {"a": 1, "b": 1})
SINGLE_A = ("bin", {"a": 1})
SINGLE_B = ("bin", {"b": 1})


def _context() -> PackingContext:
    zero = Rational.from_value(0).unwrap()
    one = Rational.from_value(1).unwrap()
    two = Rational.from_value(2).unwrap()
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    return PackingContext.create(
        items=[
            ItemSpec(id="a", length=one, weight=zero, amount=1),
            ItemSpec(id="b", length=one, weight=zero, amount=1),
        ],
        bins=[BinSpec(id="bin", length=two, max_weight=zero, cost=one)],
        spacing=zero,
        length_unit=length,
        weight_unit=mass,
    ).unwrap()


def test_pool_rebuilds_atomically_and_returns_detached_snapshots() -> None:
    stages: list[str] = []

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        stages.append(snapshot.stage)
        return PatternExtensionSpec()

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    first = pool.snapshot().unwrap()
    assert first.generation == 0 and first.patterns == [MIXED]
    assert len(first.compiled_columns) == 1
    assert first.compiled_columns[0].reference.model_identity == first.model_identity
    unchanged = pool.add_columns(patterns=[MIXED, MIXED]).unwrap()
    assert (
        unchanged.generation == 0 and unchanged.model_identity == first.model_identity
    )
    assert stages == ["lp"]
    second = pool.add_columns(patterns=[SINGLE_A]).unwrap()
    assert second.generation == 1 and second.model_identity != first.model_identity
    assert second.patterns == [SINGLE_A, MIXED]
    second.patterns[0][1].clear()
    assert pool.snapshot().unwrap().patterns == [SINGLE_A, MIXED]
    third = pool.remove_columns(patterns=[MIXED]).unwrap()
    assert third.generation == 2 and third.patterns == [SINGLE_A]
    assert stages == ["lp", "lp", "lp"]
    assert pool.close().is_ok() and pool.close().is_ok()
    assert pool.snapshot().is_failed()


def test_failed_strict_conversion_keeps_existing_pool() -> None:
    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        if len(snapshot.candidates) > 1:
            return PatternExtensionSpec(
                variables=[AuxiliaryVariable(name="extra", lower=(1, 3))]
            )
        return PatternExtensionSpec()

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    result = pool.add_columns(patterns=[SINGLE_A])
    assert isinstance(result, Failed)
    assert "precision" in result.error.message.lower()
    assert pool.snapshot().unwrap() == before


def test_invalid_batch_and_missing_native_extension_leave_pool_unchanged() -> None:
    calls: list[int] = []

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        calls.append(len(snapshot.candidates))
        return PatternExtensionSpec()

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    assert pool.add_columns(patterns=[SINGLE_A, ("bin", {"unknown": 1})]).is_failed()
    assert pool.add_columns(patterns=[("bin", {"a": True})]).is_failed()
    _, error = pool._handle.add_columns(patterns=[SINGLE_A])
    assert error is not None and error.category == "FAILED_PRECONDITION"
    assert pool.snapshot().unwrap() == before and calls == [1]


def test_native_pool_rejects_different_extension_callbacks() -> None:
    def register(
        _: object,
    ) -> tuple[list[object], list[object], list[object], tuple[int, int]]:
        return [], [], [], (0, 1)

    def other(
        _: object,
    ) -> tuple[list[object], list[object], list[object], tuple[int, int]]:
        return [], [], [], (0, 1)

    def extract(_: object) -> dict[str, str]:
        return {}

    def other_extract(_: object) -> dict[str, str]:
        return {}

    context = _context()
    pool, error = context._handle.column_pool(
        patterns=[MIXED],
        extension=(register, extract),  # type: ignore[arg-type]
    )
    assert error is None and pool is not None
    before, error = pool.snapshot()
    assert error is None
    for callbacks in ((other, extract), (register, other_extract)):
        _, error = pool.add_columns(
            patterns=[SINGLE_A],
            extension=callbacks,  # type: ignore[arg-type]
        )
        assert error is not None and error.category == "FAILED_PRECONDITION"
        assert pool.snapshot() == (before, None)
    result, error = pool.add_columns(
        patterns=[SINGLE_A],
        extension=(register, extract),  # type: ignore[arg-type]
    )
    assert error is None and result is not None and result[0] == 1


def test_native_pool_does_not_keep_callbacks_alive() -> None:
    def create() -> tuple[
        _native.Bpp1dPool, weakref.ReferenceType[object], weakref.ReferenceType[object]
    ]:
        def register(_: object) -> _native._Bpp1dRegistration:
            return [], [], [], (0, 1)

        def extract(_: object) -> dict[str, str]:
            return {}

        pool, error = _context()._handle.column_pool(
            patterns=[MIXED], extension=(register, extract)
        )
        assert error is None and pool is not None
        return pool, weakref.ref(register), weakref.ref(extract)

    pool, register, extract = create()
    gc.collect()
    assert register() is None and extract() is None
    assert pool.snapshot()[1] is None
    _, error = pool.add_columns(patterns=[SINGLE_A])
    assert error is not None and error.category == "FAILED_PRECONDITION"


def test_native_pool_rejects_nonweakrefable_callbacks() -> None:
    class NonWeakCallback:
        __slots__ = ()

        def __call__(self, _: object) -> _native._Bpp1dRegistration:
            return [], [], [], (0, 1)

    def extract(_: object) -> dict[str, str]:
        return {}

    pool, error = _context()._handle.column_pool(
        patterns=[MIXED], extension=(NonWeakCallback(), extract)
    )
    assert pool is None and error is not None and error.category == "ILLEGAL_ARGUMENT"


def test_concurrent_callback_failures_keep_their_own_results() -> None:
    barrier = threading.Barrier(2)
    first: Result[PatternExtensionSpec, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="first")
    )
    second: Result[PatternExtensionSpec, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="second")
    )

    def register(
        snapshot: PatternRegistration,
    ) -> PatternExtensionSpec | Result[PatternExtensionSpec, Any, Any]:
        candidates = [pattern for _, pattern in snapshot.candidates]
        if len(candidates) == 1:
            return PatternExtensionSpec()
        barrier.wait(timeout=10)
        return first if SINGLE_A in candidates else second

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    with ThreadPoolExecutor(max_workers=2) as executor:
        one = executor.submit(pool.add_columns, patterns=[SINGLE_A])
        two = executor.submit(pool.add_columns, patterns=[SINGLE_B])
        first_result, second_result = one.result(timeout=15), two.result(timeout=15)
    assert isinstance(first_result, Failed) and isinstance(second_result, Failed)
    assert first_result.error.value.callback_result is first
    assert second_result.error.value.callback_result is second
    assert pool.snapshot().unwrap() == before


def test_reentrant_callback_failures_keep_their_own_results() -> None:
    inner: Result[PatternExtensionSpec, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="inner")
    )
    outer: Result[PatternExtensionSpec, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="outer")
    )
    holder: dict[str, PatternPool] = {}

    def register(
        snapshot: PatternRegistration,
    ) -> PatternExtensionSpec | Result[PatternExtensionSpec, Any, Any]:
        candidates = [pattern for _, pattern in snapshot.candidates]
        if len(candidates) == 1:
            return PatternExtensionSpec()
        if SINGLE_A in candidates:
            result = holder["pool"].add_columns(patterns=[SINGLE_B])
            assert isinstance(result, Failed)
            assert result.error.value.callback_result is inner
            return outer
        return inner

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    holder["pool"] = pool
    before = pool.snapshot().unwrap()
    result = pool.add_columns(patterns=[SINGLE_A])
    assert isinstance(result, Failed) and result.error.value.callback_result is outer
    assert pool.snapshot().unwrap() == before


def test_callback_failure_identity_interrupt_and_recovery() -> None:
    original: Result[PatternExtensionSpec, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="denied")
    )
    exception = ValueError("register")
    state = {"mode": "ok"}

    def register(
        snapshot: PatternRegistration,
    ) -> PatternExtensionSpec | Result[PatternExtensionSpec, Any, Any]:
        if len(snapshot.candidates) == 1 or state["mode"] == "ok":
            return PatternExtensionSpec()
        if state["mode"] == "failed":
            return original
        if state["mode"] == "exception":
            raise exception
        raise KeyboardInterrupt()

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    state["mode"] = "failed"
    result = pool.add_columns(patterns=[SINGLE_A])
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is original
    state["mode"] = "exception"
    result = pool.add_columns(patterns=[SINGLE_A])
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is exception
    state["mode"] = "interrupt"
    with pytest.raises(KeyboardInterrupt):
        pool.add_columns(patterns=[SINGLE_A])
    assert pool.snapshot().unwrap() == before
    state["mode"] = "ok"
    assert pool.add_columns(patterns=[SINGLE_A]).unwrap().generation == 1


def test_reentrant_update_commits_inner_and_rejects_outer() -> None:
    holder: dict[str, PatternPool] = {}

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        candidates = [pattern for _, pattern in snapshot.candidates]
        if SINGLE_A in candidates and SINGLE_B not in candidates:
            assert (
                holder["pool"].add_columns(patterns=[SINGLE_B]).unwrap().generation == 1
            )
        return PatternExtensionSpec()

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    holder["pool"] = pool
    result = pool.add_columns(patterns=[SINGLE_A])
    assert isinstance(result, Failed) and result.error.value.category == "ABORTED"
    assert pool.snapshot().unwrap().patterns == [MIXED, SINGLE_B]


def test_concurrent_rebuild_rejects_conflict_without_losing_winner() -> None:
    entered = threading.Event()
    release = threading.Event()

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        candidates = [pattern for _, pattern in snapshot.candidates]
        if SINGLE_A in candidates and SINGLE_B not in candidates:
            entered.set()
            assert release.wait(10)
        return PatternExtensionSpec()

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    with ThreadPoolExecutor(max_workers=1) as executor:
        slow = executor.submit(pool.add_columns, patterns=[SINGLE_A])
        try:
            assert entered.wait(10)
            winner = pool.add_columns(patterns=[SINGLE_B]).unwrap()
        finally:
            release.set()
        rejected = slow.result(timeout=10)
    assert isinstance(rejected, Failed)
    assert rejected.error.value.category == "ABORTED"
    assert winner.generation == 1
    assert pool.snapshot().unwrap() == winner


def test_close_rejects_inflight_rebuild() -> None:
    entered = threading.Event()
    release = threading.Event()

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        if len(snapshot.candidates) > 1:
            entered.set()
            assert release.wait(10)
        return PatternExtensionSpec()

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    reference = weakref.ref(pool)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(pool.add_columns, patterns=[SINGLE_A])
        try:
            assert entered.wait(10)
            assert pool.close().is_ok()
        finally:
            release.set()
        rejected = pending.result(timeout=10)
    assert isinstance(rejected, Failed)
    assert rejected.error.value.category == "NOT_INITIALIZED"
    del rejected, pending, pool, register
    gc.collect()
    assert reference() is None


def test_pool_callback_reference_cycle_is_collectable() -> None:
    def create_cycle() -> weakref.ReferenceType[object]:
        holder: dict[str, object] = {}

        def register(_: PatternRegistration) -> PatternExtensionSpec:
            assert holder is not None
            return PatternExtensionSpec()

        pool = (
            _context()
            .column_pool(
                patterns=[MIXED], extension=PatternExtension(register=register)
            )
            .unwrap()
        )
        holder["pool"] = pool
        return weakref.ref(pool)

    reference = create_cycle()
    gc.collect()
    assert reference() is None


def test_unavailable_lp_does_not_consume_cancellation() -> None:
    pool = _context().column_pool(patterns=[MIXED]).unwrap()
    handle = SolveHandle()
    assert pool.solve_lp(solver="unknown", cancellation=handle).is_failed()
    assert handle.phase == "READY"


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def test_lp_solves_published_snapshot_and_retains_exact_values(solver: str) -> None:
    pool = _context().column_pool(patterns=[MIXED]).unwrap()
    solved = pool.solve_lp(solver=solver).unwrap()
    assert solved.report.model_generation == 0
    assert solved.report.model_identity == pool.snapshot().unwrap().model_identity
    assert solved.report.values == (1.0,)
    solution = solved.solution.unwrap()
    assert solution.model_objective == (1, 1)
    assert list(solution.values.values()) == [(1, 1)]
    pool.add_columns(patterns=[SINGLE_A]).unwrap()
    assert solved.report.model_generation == 0
    assert pool.snapshot().unwrap().generation == 1


def test_lp_relaxes_and_validates_extension_variables(solver: str) -> None:
    extractions: list[object] = []

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        assert snapshot.stage == "lp"
        flag = snapshot.auxiliary("flag")
        return PatternExtensionSpec(
            variables=[AuxiliaryVariable(name="flag", kind="binary")],
            constraints=[
                ExtensionConstraint(
                    name="half", terms=[(flag, (2, 1))], relation="==", rhs=(1, 1)
                )
            ],
            objective=[(flag, (1, 1))],
        )

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        extractions.append(snapshot)
        return {}

    pool = (
        _context()
        .column_pool(
            patterns=[MIXED],
            extension=PatternExtension(register=register, extract_solution=extract),
        )
        .unwrap()
    )
    solved = pool.solve_lp(solver=solver).unwrap()
    solution = solved.solution.unwrap()
    assert solution.model_objective == (3, 2)
    assert {value for value in solution.values.values()} == {(1, 1), (1, 2)}
    assert extractions == []


def test_empty_pool_report_and_recovery(solver: str) -> None:
    pool = _context().column_pool(patterns=[]).unwrap()
    initial = pool.snapshot().unwrap()
    assert initial.generation == 0 and initial.patterns == []
    empty = pool.solve_lp(solver=solver).unwrap()
    assert empty.report.problem_status == "INFEASIBLE"
    assert empty.solution.is_failed()
    assert pool.add_columns(patterns=[MIXED]).unwrap().generation == 1
    assert pool.solve_lp(solver=solver).unwrap().solution.is_ok()
    assert pool.remove_columns(patterns=[MIXED]).unwrap().generation == 2
    assert pool.snapshot().unwrap().patterns == []


def test_lp_progress_failure_is_preserved_and_pool_recovers(solver: str) -> None:
    original: Result[None, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="stop")
    )
    pool = _context().column_pool(patterns=[MIXED]).unwrap()
    before = pool.snapshot().unwrap()
    result = pool.solve_lp(solver=solver, on_progress=lambda _: original)
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is original
    assert pool.snapshot().unwrap() == before
    assert pool.solve_lp(solver=solver).unwrap().solution.is_ok()


def test_inflight_lp_uses_old_snapshot_after_rebuild_and_close(solver: str) -> None:
    entered, release = threading.Event(), threading.Event()
    pool = _context().column_pool(patterns=[MIXED]).unwrap()
    before = pool.snapshot().unwrap()

    def progress(_: SolveProgress) -> None:
        if not entered.is_set():
            entered.set()
            assert release.wait(timeout=10)

    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(pool.solve_lp, solver=solver, on_progress=progress)
        try:
            assert entered.wait(timeout=10)
            assert pool.add_columns(patterns=[SINGLE_A]).unwrap().generation == 1
            assert pool.close().is_ok()
        finally:
            release.set()
        solved = pending.result(timeout=15).unwrap()
    assert solved.report.model_generation == before.generation
    assert solved.report.model_identity == before.model_identity
    assert solved.compiled_columns == before.compiled_columns
    assert solved.solution.unwrap().model_objective == (1, 1)
    assert pool.snapshot().is_failed()


def test_inexact_lp_solution_keeps_report_but_fails_exact_validation(
    solver: str,
) -> None:
    zero = Rational.from_value(0).unwrap()
    one = Rational.from_value(1).unwrap()
    three = Rational.from_value(3).unwrap()
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    ids = "abcd"
    context = PackingContext.create(
        items=[ItemSpec(id=id_, length=one, weight=zero, amount=1) for id_ in ids],
        bins=[BinSpec(id="bin", length=three, max_weight=zero, cost=one)],
        spacing=zero,
        length_unit=length,
        weight_unit=mass,
    ).unwrap()
    pool = context.column_pool(
        patterns=[
            ("bin", {item: 1 for item in ids if item != omitted}) for omitted in ids
        ]
    ).unwrap()
    solved = pool.solve_lp(solver=solver).unwrap()
    assert len(solved.report.values) == 4
    assert solved.solution.is_failed()


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt(), SystemExit(2)])
def test_final_registration_failure_interrupt_and_unchanged_pool(
    interrupt: BaseException,
) -> None:
    original: Result[PatternExtensionSpec, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="final registration")
    )
    exception = ValueError("final registration")
    state = {"mode": "failed"}

    def register(
        snapshot: PatternRegistration,
    ) -> PatternExtensionSpec | Result[PatternExtensionSpec, Any, Any]:
        if snapshot.stage == "lp":
            return PatternExtensionSpec()
        assert snapshot.stage == "final_milp"
        if state["mode"] == "failed":
            return original
        if state["mode"] == "exception":
            raise exception
        if state["mode"] == "interrupt":
            raise interrupt
        return PatternExtensionSpec()

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    handle = SolveHandle()
    result = pool.solve_final_milp(
        solver="unknown", expansion_limit=2, cancellation=handle
    )
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is original and handle.phase == "READY"
    state["mode"] = "exception"
    result = pool.solve_final_milp(solver="unknown", expansion_limit=2)
    assert (
        isinstance(result, Failed)
        and result.error.value.callback_exception is exception
    )
    state["mode"] = "interrupt"
    with pytest.raises(type(interrupt)) as caught:
        pool.solve_final_milp(solver="unknown", expansion_limit=2)
    assert caught.value is interrupt and pool.snapshot().unwrap() == before
    state["mode"] = "ok"
    assert pool.solve_final_milp(solver="unknown", expansion_limit=2).is_failed()
    assert handle.phase == "READY" and pool.snapshot().unwrap() == before


def test_native_final_rejects_different_or_missing_extension() -> None:
    def register(_: object) -> _native._Bpp1dRegistration:
        return [], [], [], (0, 1)

    def other(_: object) -> _native._Bpp1dRegistration:
        return [], [], [], (0, 1)

    def extract(_: object) -> dict[str, str]:
        return {}

    def other_extract(_: object) -> dict[str, str]:
        return {}

    pool, error = _context()._handle.column_pool(
        patterns=[MIXED], extension=(register, extract)
    )
    assert error is None and pool is not None
    before = pool.snapshot()
    for callbacks in (None, (other, extract), (register, other_extract)):
        _, error = pool.solve_final_milp(
            solver="unknown", expansion_limit=2, extension=callbacks
        )
        assert error is not None and error.category == "FAILED_PRECONDITION"
        assert pool.snapshot() == before
    _, error = pool.solve_final_milp(
        solver="unknown", expansion_limit=2, extension=(register, extract)
    )
    assert error is not None and error.category == "NOT_SUPPORTED"
    assert pool.snapshot() == before
    plain, error = _context()._handle.column_pool(patterns=[MIXED])
    assert error is None and plain is not None
    _, error = plain.solve_final_milp(
        solver="unknown", expansion_limit=2, extension=(register, extract)
    )
    assert error is not None and error.category == "FAILED_PRECONDITION"


def test_final_reentrant_registration_failures_keep_contexts() -> None:
    inner: Result[PatternExtensionSpec, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="inner final")
    )
    outer: Result[PatternExtensionSpec, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="outer final")
    )
    holder: dict[str, PatternPool] = {}
    nested = False

    def register(
        snapshot: PatternRegistration,
    ) -> PatternExtensionSpec | Result[PatternExtensionSpec, Any, Any]:
        nonlocal nested
        if snapshot.stage == "lp":
            return PatternExtensionSpec()
        if nested:
            return inner
        nested = True
        result = holder["pool"].solve_final_milp(solver="unknown", expansion_limit=2)
        assert (
            isinstance(result, Failed) and result.error.value.callback_result is inner
        )
        return outer

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    holder["pool"] = pool
    result = pool.solve_final_milp(solver="unknown", expansion_limit=2)
    assert isinstance(result, Failed) and result.error.value.callback_result is outer
    assert pool.snapshot().unwrap().generation == 0


def test_concurrent_final_registration_failures_are_isolated() -> None:
    originals: list[Result[PatternExtensionSpec, Any, Any]] = [
        Failed(Err(_code=ErrorCode.PERMISSION_DENIED, _message=message))
        for message in ("first final", "second final")
    ]
    barrier = threading.Barrier(2)
    current = threading.local()

    def register(
        snapshot: PatternRegistration,
    ) -> PatternExtensionSpec | Result[PatternExtensionSpec, Any, Any]:
        if snapshot.stage == "lp":
            return PatternExtensionSpec()
        barrier.wait(timeout=10)
        return originals[cast("int", current.index)]

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )

    def run(index: int) -> None:
        current.index = index
        result = pool.solve_final_milp(solver="unknown", expansion_limit=2)
        assert isinstance(result, Failed)
        assert result.error.value.callback_result is originals[index]

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run, index) for index in range(2)]
        for future in futures:
            future.result(timeout=15)
    assert pool.snapshot().unwrap().generation == 0


def test_final_rejects_stale_references_and_inexact_registration() -> None:
    registrations: list[PatternRegistration] = []
    mode = {"value": "stale"}

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        registrations.append(snapshot)
        if snapshot.stage == "lp":
            return PatternExtensionSpec()
        if mode["value"] == "stale":
            return PatternExtensionSpec(
                objective=[(registrations[0].candidates[0][0], (1, 1))]
            )
        return PatternExtensionSpec(
            variables=[AuxiliaryVariable(name="extra", lower=(1, 3))]
        )

    pool = (
        _context()
        .column_pool(patterns=[MIXED], extension=PatternExtension(register=register))
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    handle = SolveHandle()
    stale = pool.solve_final_milp(
        solver="unknown", expansion_limit=2, cancellation=handle
    )
    assert isinstance(stale, Failed) and stale.error.value.category != "NOT_SUPPORTED"
    assert registrations[0].model_identity != registrations[1].model_identity
    mode["value"] = "inexact"
    result = pool.solve_final_milp(
        solver="unknown", expansion_limit=2, cancellation=handle
    )
    assert isinstance(result, Failed) and "precision" in result.error.message.lower()
    assert handle.phase == "READY" and pool.snapshot().unwrap() == before


def test_final_rejects_invalid_limits_and_closed_pool() -> None:
    pool = _context().column_pool(patterns=[MIXED]).unwrap()
    before = pool.snapshot().unwrap()
    for limit in (True, -1, 2**64, 1.0):
        result = pool.solve_final_milp(
            solver="unknown",
            expansion_limit=limit,  # type: ignore[arg-type]
        )
        assert (
            isinstance(result, Failed)
            and result.error.value.category == "ILLEGAL_ARGUMENT"
        )
    assert pool.snapshot().unwrap() == before
    assert pool.close().is_ok()
    result = pool.solve_final_milp(solver="unknown", expansion_limit=2)
    assert (
        isinstance(result, Failed) and result.error.value.category == "NOT_INITIALIZED"
    )


def test_final_integer_stage_extracts_full_verified_solution(solver: str) -> None:
    registrations: list[PatternRegistration] = []
    extractions: list[PatternExtraction] = []

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        registrations.append(snapshot)
        flag = snapshot.auxiliary("flag")
        return PatternExtensionSpec(
            variables=[AuxiliaryVariable(name="flag", kind="binary")],
            constraints=[
                ExtensionConstraint(
                    name="half", terms=[(flag, (2, 1))], relation=">=", rhs=(1, 1)
                )
            ],
            objective=[(flag, (1, 1))],
        )

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        extractions.append(snapshot)
        flag = next(key for key in snapshot.values if key.auxiliary == "flag")
        return {"flag": str(snapshot.values[flag][0])}

    pool = (
        _context()
        .column_pool(
            patterns=[MIXED],
            extension=PatternExtension(register=register, extract_solution=extract),
        )
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    lp = pool.solve_lp(solver=solver).unwrap()
    assert lp.solution.unwrap().model_objective == (3, 2)
    final = pool.solve_final_milp(solver=solver, expansion_limit=2).unwrap()
    solution = final.solution.unwrap()
    assert [snapshot.stage for snapshot in registrations] == ["lp", "final_milp"]
    assert final.report.model_generation == before.generation
    assert final.report.model_identity != before.model_identity
    assert final.report.model_identity == registrations[-1].model_identity
    assert len(final.compiled_columns) == len(final.report.values) == 2
    assert all(
        column.reference.model_identity == final.report.model_identity
        for column in final.compiled_columns
    )
    assert solution.usages == [("bin", {"a": 1, "b": 1}, 1)]
    assert solution.packed[-1] == (1, 1) and solution.model_objective == (2, 1)
    assert solution.indicators == {"flag": "1"}
    assert len(extractions) == 1 and set(extractions[0].values.values()) == {(1, 1)}
    assert pool.snapshot().unwrap() == before
    again = pool.solve_final_milp(solver=solver, expansion_limit=2).unwrap()
    assert again.report.model_identity != final.report.model_identity
    assert again.report.model_generation == before.generation
    assert again.solution.unwrap().indicators == {"flag": "1"}


def test_final_empty_pool_and_expansion_failure_keep_report(solver: str) -> None:
    pool = _context().column_pool(patterns=[]).unwrap()
    empty = pool.solve_final_milp(solver=solver, expansion_limit=2).unwrap()
    assert empty.report.problem_status == "INFEASIBLE"
    assert empty.report.model_generation == 0 and empty.solution.is_failed()
    pool.add_columns(patterns=[MIXED]).unwrap()
    before = pool.snapshot().unwrap()
    limited = pool.solve_final_milp(solver=solver, expansion_limit=1).unwrap()
    assert limited.report.values and limited.solution.is_failed()
    assert pool.snapshot().unwrap() == before
    assert (
        pool.solve_final_milp(solver=solver, expansion_limit=2)
        .unwrap()
        .solution.is_ok()
    )


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt(), SystemExit(2)])
def test_final_extraction_failure_interrupt_and_recovery(
    solver: str, interrupt: BaseException
) -> None:
    original: Result[dict[str, str], Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="final extraction")
    )
    exception = ValueError("final extraction")
    state = {"mode": "failed"}

    def extract(
        _: PatternExtraction,
    ) -> dict[str, str] | Result[dict[str, str], Any, Any]:
        if state["mode"] == "failed":
            return original
        if state["mode"] == "exception":
            raise exception
        if state["mode"] == "interrupt":
            raise interrupt
        return {"ok": "yes"}

    pool = (
        _context()
        .column_pool(
            patterns=[MIXED],
            extension=PatternExtension(
                register=lambda _: PatternExtensionSpec(), extract_solution=extract
            ),
        )
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    result = pool.solve_final_milp(solver=solver, expansion_limit=2).unwrap()
    assert result.report.values and isinstance(result.solution, Failed)
    assert result.solution.error.value.callback_result is original
    state["mode"] = "exception"
    result = pool.solve_final_milp(solver=solver, expansion_limit=2).unwrap()
    assert isinstance(result.solution, Failed)
    assert result.solution.error.value.callback_exception is exception
    state["mode"] = "interrupt"
    with pytest.raises(type(interrupt)) as caught:
        pool.solve_final_milp(solver=solver, expansion_limit=2)
    assert caught.value is interrupt and pool.snapshot().unwrap() == before
    state["mode"] = "ok"
    result = pool.solve_final_milp(solver=solver, expansion_limit=2).unwrap()
    assert result.solution.unwrap().indicators == {"ok": "yes"}
    assert pool.snapshot().unwrap() == before


def test_concurrent_final_extraction_failures_are_isolated(solver: str) -> None:
    originals: list[Result[dict[str, str], Any, Any]] = [
        Failed(Err(_code=ErrorCode.PERMISSION_DENIED, _message=message))
        for message in ("first final", "second final")
    ]
    barrier = threading.Barrier(2)
    current = threading.local()

    def extract(_: PatternExtraction) -> Result[dict[str, str], Any, Any]:
        barrier.wait(timeout=10)
        return originals[cast("int", current.index)]

    pool = (
        _context()
        .column_pool(
            patterns=[MIXED],
            extension=PatternExtension(
                register=lambda _: PatternExtensionSpec(), extract_solution=extract
            ),
        )
        .unwrap()
    )

    def run(index: int) -> None:
        current.index = index
        result = pool.solve_final_milp(solver=solver, expansion_limit=2).unwrap()
        assert isinstance(result.solution, Failed)
        assert result.solution.error.value.callback_result is originals[index]

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run, index) for index in range(2)]
        for future in futures:
            future.result(timeout=20)
    assert pool.snapshot().unwrap().generation == 0


def test_reentrant_final_extraction_failures_are_isolated(solver: str) -> None:
    inner: Result[dict[str, str], Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="inner extraction")
    )
    outer: Result[dict[str, str], Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="outer extraction")
    )
    holder: dict[str, PatternPool] = {}
    nested = False

    def extract(_: PatternExtraction) -> Result[dict[str, str], Any, Any]:
        nonlocal nested
        if nested:
            return inner
        nested = True
        result = (
            holder["pool"].solve_final_milp(solver=solver, expansion_limit=2).unwrap()
        )
        assert isinstance(result.solution, Failed)
        assert result.solution.error.value.callback_result is inner
        return outer

    pool = (
        _context()
        .column_pool(
            patterns=[MIXED],
            extension=PatternExtension(
                register=lambda _: PatternExtensionSpec(), extract_solution=extract
            ),
        )
        .unwrap()
    )
    holder["pool"] = pool
    result = pool.solve_final_milp(solver=solver, expansion_limit=2).unwrap()
    assert isinstance(result.solution, Failed)
    assert result.solution.error.value.callback_result is outer
    assert pool.snapshot().unwrap().generation == 0


def test_final_progress_failure_and_cancel_keep_pool(solver: str) -> None:
    original: Result[None, Any, Any] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="stop")
    )
    pool = _context().column_pool(patterns=[MIXED]).unwrap()
    before = pool.snapshot().unwrap()
    failed = pool.solve_final_milp(
        solver=solver, expansion_limit=2, on_progress=lambda _: original
    )
    assert isinstance(failed, Failed) and failed.error.value.callback_result is original
    handle = SolveHandle()
    assert handle.cancel(reason="before final solve").unwrap()
    cancelled = pool.solve_final_milp(
        solver=solver, expansion_limit=2, cancellation=handle
    ).unwrap()
    assert cancelled.report.termination_reason == "CANCELLED"
    assert cancelled.solution.is_failed() and handle.cancellation_preceded_completion
    assert pool.snapshot().unwrap() == before


def test_inflight_final_retains_old_generation_and_extension_after_close(
    solver: str,
) -> None:
    entered, release = threading.Event(), threading.Event()
    extraction_patterns: list[list[tuple[str, dict[str, int]]]] = []

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        if snapshot.stage == "final_milp":
            entered.set()
            assert release.wait(timeout=10)
        return PatternExtensionSpec()

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        extraction_patterns.append([pattern for _, pattern in snapshot.candidates])
        return {"captured": "yes"}

    pool = (
        _context()
        .column_pool(
            patterns=[MIXED],
            extension=PatternExtension(register=register, extract_solution=extract),
        )
        .unwrap()
    )
    before = pool.snapshot().unwrap()
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(
            pool.solve_final_milp, solver=solver, expansion_limit=2
        )
        try:
            assert entered.wait(timeout=10)
            assert pool.add_columns(patterns=[SINGLE_A]).unwrap().generation == 1
            assert pool.close().is_ok()
        finally:
            release.set()
        result = pending.result(timeout=15).unwrap()
    assert result.report.model_generation == before.generation
    assert result.report.model_identity != before.model_identity
    assert [column.pattern for column in result.compiled_columns] == [MIXED]
    assert extraction_patterns == [[MIXED]]
    assert result.solution.unwrap().indicators == {"captured": "yes"}
    assert pool.snapshot().is_failed()
