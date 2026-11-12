"""候选策略跨语言合同 / Cross-language candidate-policy contracts."""

from __future__ import annotations

import gc
import threading
import weakref
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.bpp1d import BinSpec, ItemSpec, PackingContext, Pattern
from ospf_python._binding.control import SolveHandle
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Success, Warn


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


def test_policy_runs_inside_search_with_detached_candidate_snapshots() -> None:
    ctx = _context()
    seen: list[Pattern] = []

    def singles(candidate: Pattern) -> Ok[bool, Any, Any]:
        bin_id, amounts = candidate
        seen.append((bin_id, amounts.copy()))
        accepted = len(amounts) == 1
        amounts.clear()
        return Ok(accepted)

    patterns, complete, visited = ctx.generate_patterns(
        max_patterns=10, max_nodes=100, policy=singles
    ).unwrap()
    assert complete and visited > 0
    assert set((bin_id, tuple(counts)) for bin_id, counts in seen) == {
        ("bin", ("a",)),
        ("bin", ("b",)),
        ("bin", ("a", "b")),
    }
    assert patterns == [("bin", {"a": 1}), ("bin", {"b": 1})]
    assert len(ctx.generate_patterns(max_patterns=10, max_nodes=100).unwrap()[0]) == 3

    calls: list[Pattern] = []

    def only_a(candidate: Pattern) -> bool:
        calls.append(candidate)
        return candidate[1] == {"a": 1}

    limited, complete, _ = ctx.generate_patterns(
        max_patterns=1, max_nodes=100, policy=only_a
    ).unwrap()
    assert limited == [("bin", {"a": 1})]
    assert not complete and len(calls) > 1


@pytest.mark.parametrize("kind", ["failed", "fatal", "warn", "success", "bad_ok"])
def test_policy_result_failures_preserve_identity_and_stop(kind: str) -> None:
    ctx = _context()
    error: Err[str] = Err(_code=ErrorCode.PERMISSION_DENIED, _message="denied")
    returned: Any = {
        "failed": Failed(error),
        "fatal": Fatal((error,)),
        "warn": Warn(True, error),
        "success": Success(),
        "bad_ok": Ok(1),
    }[kind]
    calls: list[Pattern] = []

    def policy(candidate: Pattern) -> Any:
        calls.append(candidate)
        return False if len(calls) == 1 else returned

    result = ctx.generate_patterns(max_patterns=10, max_nodes=100, policy=policy)
    assert isinstance(result, Failed)
    assert result.error.value.error_class == "CALLBACK"
    assert result.error.value.callback_result is returned
    assert result.error.value.callback_exception is None
    assert result.error.value.callback_index == 1
    assert len(calls) == 2
    assert len(ctx.generate_patterns(max_patterns=10, max_nodes=100).unwrap()[0]) == 3


@pytest.mark.parametrize("bad", [None, 0, 1, "yes", object()])
def test_policy_rejects_non_boolean_results(bad: object) -> None:
    result = _context().generate_patterns(
        max_patterns=10,
        max_nodes=100,
        policy=lambda _: bad,  # type: ignore[arg-type,return-value]
    )
    assert isinstance(result, Failed)
    assert result.error.value.error_class == "CALLBACK"
    assert result.error.value.callback_index == 0


def test_rejection_budget_validation_and_empty_search_do_not_call_policy() -> None:
    ctx = _context()
    calls: list[Pattern] = []

    def reject(candidate: Pattern) -> Ok[bool, Any, Any]:
        calls.append(candidate)
        return Ok(False)

    candidates, complete, _ = ctx.generate_patterns(
        max_patterns=1, max_nodes=100, policy=reject
    ).unwrap()
    assert candidates == [] and complete and len(calls) == 3
    calls.clear()
    candidates, complete, visited = ctx.generate_patterns(
        max_patterns=10, max_nodes=1, policy=reject
    ).unwrap()
    assert candidates == [] and not complete and visited == 1 and not calls
    invalid_budget = ctx.generate_patterns(max_patterns=0, max_nodes=100, policy=reject)
    assert isinstance(invalid_budget, Failed)
    assert invalid_budget.error.value.category == "ILLEGAL_ARGUMENT" and not calls
    assert ctx.generate_patterns(
        max_patterns=10,
        max_nodes=100,
        policy=123,  # type: ignore[arg-type]
    ).is_failed()
    _, error = ctx._handle.generate_patterns(max_patterns=10, max_nodes=100, policy=123)  # type: ignore[arg-type]
    assert error is not None and error.category == "ILLEGAL_ARGUMENT"


def test_callback_exception_preserves_identity_but_interrupts_propagate() -> None:
    ctx = _context()
    error = ValueError("policy error")

    def fail(_: Pattern) -> bool:
        raise error

    result = ctx.generate_patterns(max_patterns=10, max_nodes=100, policy=fail)
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error
    assert result.error.value.callback_index == 0
    assert result.error.value.error_class == "CALLBACK"

    for exception in (KeyboardInterrupt(), SystemExit(2)):

        def interrupt(_: Pattern, *, cause: BaseException = exception) -> bool:
            raise cause

        with pytest.raises(type(exception)) as captured:
            ctx.generate_patterns(max_patterns=10, max_nodes=100, policy=interrupt)
        assert captured.value is exception


def test_policy_reentry_and_cross_thread_calls_have_no_shared_model_lock() -> None:
    ctx = _context()
    entered, release = threading.Event(), threading.Event()

    def policy(_: Pattern) -> bool:
        assert (
            len(ctx.generate_patterns(max_patterns=10, max_nodes=100).unwrap()[0]) == 3
        )
        entered.set()
        assert release.wait(timeout=10)
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        job = pool.submit(
            ctx.generate_patterns, max_patterns=10, max_nodes=100, policy=policy
        )
        try:
            assert entered.wait(timeout=10)
            other = pool.submit(ctx.generate_patterns, max_patterns=10, max_nodes=100)
            assert len(other.result(timeout=10).unwrap()[0]) == 3
        finally:
            release.set()
        assert len(job.result(timeout=10).unwrap()[0]) == 3


def test_policy_references_are_not_retained_by_context() -> None:
    ctx = _context()

    class Policy:
        def __call__(self, _: Pattern) -> bool:
            return True

    policy = Policy()
    reference = weakref.ref(policy)
    assert ctx.generate_patterns(max_patterns=10, max_nodes=100, policy=policy).is_ok()
    del policy
    gc.collect()
    assert reference() is None


def test_callback_exception_traceback_is_retained_only_by_failure() -> None:
    ctx = _context()

    class Policy:
        def __call__(self, _: Pattern) -> bool:
            raise ValueError("failed")

    policy = Policy()
    reference = weakref.ref(policy)
    result = ctx.generate_patterns(max_patterns=10, max_nodes=100, policy=policy)
    assert isinstance(result, Failed)
    del policy
    gc.collect()
    assert reference() is not None
    del result
    gc.collect()
    assert reference() is None


def test_concurrent_policies_do_not_share_callback_results() -> None:
    ctx = _context()
    barrier = threading.Barrier(2)

    def run(*, accepted: str) -> list[Pattern]:
        first = True

        def policy(candidate: Pattern) -> bool:
            nonlocal first
            if first:
                first = False
                barrier.wait(timeout=10)
            return candidate[1] == {accepted: 1}

        return ctx.generate_patterns(
            max_patterns=10, max_nodes=100, policy=policy
        ).unwrap()[0]

    with ThreadPoolExecutor(max_workers=2) as pool:
        left = pool.submit(run, accepted="a")
        right = pool.submit(run, accepted="b")
        assert left.result(timeout=10) == [("bin", {"a": 1})]
        assert right.result(timeout=10) == [("bin", {"b": 1})]


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def test_policy_changes_real_master_and_exact_solution(solver: str) -> None:
    ctx = _context()
    calls: list[Pattern] = []

    def singles(candidate: Pattern) -> bool:
        calls.append(candidate)
        return len(candidate[1]) == 1

    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=2,
        policy=singles,
    ).unwrap()
    assert result.candidate_complete and len(calls) == 3
    assert set((bin_id, tuple(amounts)) for bin_id, amounts in result.columns) == {
        ("bin", ("a",)),
        ("bin", ("b",)),
    }
    solution = result.solution.unwrap()
    assert solution.usages == [("bin", {"a": 1}, 1), ("bin", {"b": 1}, 1)]
    assert len(solution.packed[0]) == 2 and solution.packed[5] == (2, 1)
    placements = [placement for _, _, box in solution.packed[0] for placement in box]
    assert Counter(id_ for id_, _, _ in placements) == {"a": 1, "b": 1}
    assert all(
        Fraction(*start) == 0 and Fraction(*length) == 1
        for _, start, length in placements
    )

    unrestricted = ctx.solve(
        solver=solver, max_patterns=10, max_nodes=100, expansion_limit=2
    ).unwrap()
    assert unrestricted.solution.unwrap().packed[5] == (1, 1)

    denied = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=2,
        policy=lambda _: False,
    ).unwrap()
    assert denied.candidate_complete and denied.columns == []
    assert denied.report.problem_status == "INFEASIBLE" and denied.solution.is_failed()


def test_policy_failure_does_not_consume_solve_handle(solver: str) -> None:
    ctx = _context()
    control = SolveHandle()
    original: Failed[Any, str, Err[str]] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="denied")
    )
    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=2,
        cancellation=control,
        policy=lambda _: original,
    )
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is original
    assert control.phase == "READY"
    assert (
        ctx.solve(
            solver=solver,
            max_patterns=10,
            max_nodes=100,
            expansion_limit=2,
            cancellation=control,
        )
        .unwrap()
        .solution.is_ok()
    )


def test_backend_preflight_happens_after_policy_but_before_attempt() -> None:
    ctx = _context()
    control = SolveHandle()
    seen: list[Pattern] = []
    result = ctx.solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=2,
        cancellation=control,
        policy=lambda candidate: seen.append(candidate) or True,  # type: ignore[func-returns-value]
    )
    assert result.is_failed() and len(seen) == 3 and control.phase == "READY"

    interruption = KeyboardInterrupt()

    def interrupt(_: Pattern) -> bool:
        raise interruption

    with pytest.raises(KeyboardInterrupt) as captured:
        ctx.solve(
            solver="unknown",
            max_patterns=10,
            max_nodes=100,
            expansion_limit=2,
            cancellation=control,
            policy=interrupt,
        )
    assert captured.value is interruption and control.phase == "READY"
