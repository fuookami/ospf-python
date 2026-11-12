"""真实 Rust 取消、回调和重入合同 / Real Rust cancellation, callback and reentry contracts."""

from __future__ import annotations

import gc
import random
import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.control import CancellationScope, SolveHandle, SolveProgress
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Warn


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def graph_model() -> MetaModelFloat64:
    """固定 seed 的小型真实 MILP，不超过受限 Gurobi 许可规模 / Seeded real MILP within restricted-license size."""
    model = MetaModelFloat64.create("callback-independent-set").unwrap()
    variables = model.add_variables(
        [VariableSpec(name=f"x{i}", kind="binary") for i in range(40)]
    ).unwrap()
    randomizer = random.Random(42)
    assert model.add_constraints(
        [
            ConstraintSpec(
                name=f"edge-{i}-{j}",
                terms=[(variables[i], 1), (variables[j], 1)],
                relation="<=",
                rhs=1,
            )
            for i in range(40)
            for j in range(i)
            if randomizer.random() < 0.3
        ]
    ).is_ok()
    assert model.set_objective(
        terms=[(variable, 1) for variable in variables], sense="maximize"
    ).is_ok()
    return model


def test_control_first_fact_is_immutable_and_idempotent() -> None:
    control = SolveHandle()
    assert control.phase == "READY"
    assert not control.is_cancelled
    assert control.completed_at_epoch_ms is None
    assert control.cancellation() is None
    assert control.cancel(origin="future-origin", reason="first").unwrap() is True
    assert control.cancel(origin="user", reason="second").unwrap() is False
    record = control.cancellation()
    assert record is not None
    assert record.origin == "future-origin"
    assert record.reason == "first"
    assert record.requested_at_epoch_ms > 0
    assert control.cancellation_preceded_completion
    with pytest.raises(AttributeError):
        record.reason = "changed"  # type: ignore[misc]


def test_cancellation_scope_covers_current_and_future_handles() -> None:
    scope = CancellationScope()
    current = scope.new_handle().unwrap()

    assert scope.cancel(origin="user", reason="scope").unwrap()
    assert current.is_cancelled
    future = scope.new_handle().unwrap()
    assert future.is_cancelled
    assert not scope.cancel(reason="duplicate").unwrap()


@pytest.mark.parametrize("origin", ["", " ", 42])
def test_cancellation_scope_rejects_invalid_origin(origin: Any) -> None:
    scope = CancellationScope()
    result = scope.cancel(origin=origin)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert not scope.is_cancelled


def test_concurrent_cancel_has_exactly_one_winner() -> None:
    control = SolveHandle()
    start = threading.Barrier(8)

    def request(index: int) -> bool:
        start.wait(timeout=5)
        return control.cancel(origin="external", reason=str(index)).unwrap()

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(request, range(8)))
    assert sum(results) == 1
    assert control.cancellation() is not None


@pytest.mark.parametrize("origin", ["", " ", 42])
def test_invalid_cancellation_origin_is_a_result(origin: Any) -> None:
    control = SolveHandle()
    result = control.cancel(origin=origin)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert not control.is_cancelled


def test_invalid_request_does_not_consume_control() -> None:
    model = MetaModelFloat64.create("invalid control").unwrap()
    control = SolveHandle()
    assert model.solve(solver="gurobi13", cancellation=control).is_failed()
    assert control.phase == "READY"
    for seconds in (0, -1, float("nan")):
        assert model.solve(
            solver="scip", cancellation=control, time_limit=seconds
        ).is_failed()
        assert control.phase == "READY"
    assert model.solve(
        solver="scip",
        cancellation=control,
        on_progress=123,  # type: ignore[arg-type]
    ).is_failed()
    assert control.phase == "READY"
    assert model.close().is_ok()
    assert model.solve(solver="scip", cancellation=control).is_failed()
    assert control.phase == "READY"


def test_pre_cancelled_attempt_is_a_normal_report_and_single_use(solver: str) -> None:
    model = graph_model()
    control = SolveHandle()
    assert control.cancel(origin="user", reason="preflight").unwrap()
    events: list[SolveProgress] = []
    report = model.solve(
        solver=solver, cancellation=control, on_progress=events.append
    ).unwrap()
    assert report.termination_reason == "CANCELLED"
    assert report.solution_presence == "NONE"
    assert control.phase == "FINISHED"
    assert control.completed_at_epoch_ms is not None
    assert control.cancellation_preceded_completion
    assert all(event.source == "reporter" for event in events)
    result = model.solve(solver=solver, cancellation=control)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.FAILED_PRECONDITION
    assert model.solve(solver=solver, cancellation=SolveHandle()).is_ok()


def test_progress_snapshots_are_detached_and_attempts_are_distinct(solver: str) -> None:
    model = graph_model()
    events: list[SolveProgress] = []
    caller = threading.get_ident()
    threads: list[int] = []

    def callback(event: SolveProgress) -> Any:
        events.append(event)
        threads.append(threading.get_ident())
        return Ok(None)

    report = model.solve(solver=solver, on_progress=callback).unwrap()
    assert report.solution_presence == "OPTIMAL"
    assert events[0].source == "reporter"
    assert events[-1].terminal
    assert events[-1].overall_progress == 100
    assert any(event.source == "backend" for event in events)
    assert all(event.model_identity == model.model_identity for event in events)
    assert len({event.attempt_identity for event in events}) == 1
    assert all(thread != caller for thread in threads)
    assert all(event.elapsed_nanoseconds >= 0 for event in events)
    with pytest.raises(AttributeError):
        events[0].stage = "changed"  # type: ignore[misc]
    events[0].stage_path.append("not-shared")
    assert "not-shared" not in events[0].stage_path
    first_attempt = events[0].attempt_identity
    events.clear()
    assert model.solve(solver=solver, on_progress=callback).is_ok()
    assert events[0].attempt_identity != first_attempt


def test_same_model_reentry_is_a_busy_result_in_native_callbacks(solver: str) -> None:
    model = graph_model()
    nested_control = SolveHandle()
    checked: list[bool] = []

    def callback(event: SolveProgress) -> None:
        if event.source != "backend" or checked:
            return
        for result in (
            model.snapshot(),
            model.close(),
            model.add_variables([VariableSpec(name="cannot-publish")]),
            model.solve(solver=solver, cancellation=nested_control),
        ):
            assert isinstance(result, Failed)
            assert result.error.code is ErrorCode.FAILED_PRECONDITION
        assert nested_control.phase == "READY"
        checked.append(True)

    assert model.solve(solver=solver, on_progress=callback).is_ok()
    assert checked == [True]
    assert model.snapshot().unwrap()[2] == 40
    assert model.close().is_ok()


@pytest.mark.timeout(20)
def test_cross_thread_cancel_during_actual_backend_callback(solver: str) -> None:
    model = graph_model()
    control = SolveHandle()
    in_backend, release = threading.Event(), threading.Event()

    def callback(event: SolveProgress) -> None:
        if event.source == "backend" and not in_backend.is_set():
            in_backend.set()
            assert release.wait(timeout=5)

    with ThreadPoolExecutor(max_workers=1) as pool:
        job = pool.submit(
            model.solve, solver=solver, cancellation=control, on_progress=callback
        )
        try:
            assert in_backend.wait(timeout=8), (
                "Expected an actual native telemetry callback"
            )
            assert control.phase == "RUNNING"
            assert control.cancel(
                origin="external", reason="while-native-active"
            ).unwrap()
        finally:
            release.set()
        report = job.result(timeout=8).unwrap()
    assert report.termination_reason == "CANCELLED"
    assert control.phase == "FINISHED"
    assert control.cancellation_preceded_completion
    record = control.cancellation()
    assert record is not None
    assert record.reason == "while-native-active"
    assert model.snapshot().is_ok()


@pytest.mark.timeout(20)
def test_same_model_concurrent_solve_is_busy_and_owner_recovers(solver: str) -> None:
    model = graph_model()
    in_backend, release = threading.Event(), threading.Event()

    def callback(event: SolveProgress) -> None:
        if event.source == "backend" and not in_backend.is_set():
            in_backend.set()
            assert release.wait(timeout=5)

    with ThreadPoolExecutor(max_workers=1) as pool:
        active = pool.submit(model.solve, solver=solver, on_progress=callback)
        try:
            assert in_backend.wait(timeout=8), (
                "Expected an actual native telemetry callback"
            )
            concurrent = model.solve(solver=solver)
            assert isinstance(concurrent, Failed)
            assert concurrent.error.code is ErrorCode.FAILED_PRECONDITION
        finally:
            release.set()
        assert active.result(timeout=8).unwrap().solution_presence == "OPTIMAL"

    assert model.solve(solver=solver).unwrap().solution_presence == "OPTIMAL"
    assert model.close().is_ok()


@pytest.mark.timeout(30)
def test_same_model_sustained_contention_preserves_owner_atomicity(
    solver: str,
) -> None:
    model = graph_model()
    workers = 8
    attempts_per_worker = 16
    rounds = 4

    with (
        ThreadPoolExecutor(max_workers=1) as solver_pool,
        ThreadPoolExecutor(max_workers=workers) as contender_pool,
    ):
        for _ in range(rounds):
            in_backend, release = threading.Event(), threading.Event()
            callback_blocked = False

            def callback(
                event: SolveProgress,
                *,
                entered: threading.Event = in_backend,
                finished: threading.Event = release,
            ) -> None:
                nonlocal callback_blocked
                if event.source == "backend" and not callback_blocked:
                    callback_blocked = True
                    entered.set()
                    assert finished.wait(timeout=5)

            active = solver_pool.submit(
                model.solve, solver=solver, on_progress=callback
            )
            try:
                assert in_backend.wait(timeout=8), (
                    "Expected an actual native telemetry callback"
                )

                def contend(_: int) -> list[ErrorCode | None]:
                    return [
                        (
                            result.error.code
                            if isinstance(result := model.solve(solver=solver), Failed)
                            else None
                        )
                        for _ in range(attempts_per_worker)
                    ]

                outcomes = list(contender_pool.map(contend, range(workers)))
                assert len(outcomes) == workers
                assert all(
                    code is ErrorCode.FAILED_PRECONDITION
                    for batch in outcomes
                    for code in batch
                )
            finally:
                release.set()

            assert active.result(timeout=8).unwrap().solution_presence == "OPTIMAL"

    assert model.solve(solver=solver).unwrap().solution_presence == "OPTIMAL"
    assert model.close().is_ok()


def test_callback_can_cancel_without_a_model_lock(solver: str) -> None:
    model = graph_model()
    control = SolveHandle()
    requests: list[bool] = []

    def callback(event: SolveProgress) -> None:
        if event.source == "backend" and not requests:
            requests.append(control.cancel(origin="callback", reason="stop").unwrap())

    report = model.solve(
        solver=solver, cancellation=control, on_progress=callback
    ).unwrap()
    assert requests == [True]
    assert report.termination_reason == "CANCELLED"


def test_late_callback_cancellation_does_not_rewrite_completion(solver: str) -> None:
    model = graph_model()
    control = SolveHandle()

    def callback(event: SolveProgress) -> None:
        if event.terminal:
            assert control.completed_at_epoch_ms is not None
            assert control.cancel(origin="callback", reason="too-late").unwrap()

    report = model.solve(
        solver=solver, cancellation=control, on_progress=callback
    ).unwrap()
    assert report.termination_reason == "COMPLETED"
    assert report.solution_presence == "OPTIMAL"
    assert control.is_cancelled
    assert not control.cancellation_preceded_completion


@pytest.mark.parametrize("source", ["reporter", "backend", "terminal"])
def test_callback_exception_is_a_failed_result_and_owner_recovers(
    solver: str, source: str
) -> None:
    model = graph_model()
    control = SolveHandle()

    def callback(event: SolveProgress) -> None:
        if (source == "terminal" and event.terminal) or (
            source != "terminal" and event.source == source
        ):
            raise ValueError("intentional callback failure")

    result = model.solve(solver=solver, cancellation=control, on_progress=callback)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.SOLVE_FAILED
    assert result.error.value.error_class == "CALLBACK"
    assert "intentional callback failure" in result.error.message
    assert "ValueError" in result.error.message
    assert control.phase == "FINISHED"
    assert model.snapshot().is_ok()
    assert model.solve(solver=solver, cancellation=SolveHandle()).is_ok()


@pytest.mark.parametrize("kind", ["failed", "fatal", "warn", "wrong_value"])
def test_callback_result_preserves_domain_error_payload(solver: str, kind: str) -> None:
    model = graph_model()
    error: ExErr[str, dict[str, int]] = ExErr(
        _code=ErrorCode.PERMISSION_DENIED,
        _message="领域拒绝 / Domain denied",
        value={"domain-id": 37},
    )
    returned: Any = {
        "failed": Failed(error),
        "fatal": Fatal((error,)),
        "warn": Warn(None, error),
        "wrong_value": Ok(123),
    }[kind]

    result = model.solve(solver=solver, on_progress=lambda _: returned)
    assert isinstance(result, Failed)
    assert result.error.value.error_class == "CALLBACK"
    assert result.error.value.callback_result is returned
    assert error.value["domain-id"] == 37


@pytest.mark.parametrize("exit_path", ["success", "pre_cancel", "cancel", "failure"])
def test_callback_reference_is_not_retained_after_solve(
    solver: str, exit_path: str
) -> None:
    model = graph_model()
    control = SolveHandle()
    if exit_path == "pre_cancel":
        assert control.cancel().unwrap()

    class Callback:
        def __call__(self, event: SolveProgress) -> None:
            if exit_path == "cancel" and event.source == "backend":
                control.cancel().unwrap()
            if exit_path == "failure":
                raise ValueError("callback release failure path")

    callback = Callback()
    reference = weakref.ref(callback)
    result = model.solve(solver=solver, cancellation=control, on_progress=callback)
    if exit_path == "failure":
        assert isinstance(result, Failed)
        assert result.error.value.error_class == "CALLBACK"
    else:
        assert result.is_ok()
        if exit_path in ("pre_cancel", "cancel"):
            assert result.unwrap().termination_reason == "CANCELLED"
    del callback
    gc.collect()
    assert reference() is None
    assert model.close().is_ok()


def test_plain_invalid_callback_return_does_not_succeed(solver: str) -> None:
    result = graph_model().solve(solver=solver, on_progress=lambda _: 123)  # type: ignore[arg-type,return-value]
    assert isinstance(result, Failed)
    assert result.error.value.error_class == "CALLBACK"
