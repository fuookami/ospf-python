"""精确 BPP1D 建模扩展合同 / Exact BPP1D modeling-extension contracts."""

from __future__ import annotations

import gc
import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from typing import Any

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
    PatternRegistration,
    VariableRef,
)
from ospf_python._binding.control import SolveHandle
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Success, Warn


def _context() -> PackingContext:
    zero = Rational.from_value(0).unwrap()
    one = Rational.from_value(1).unwrap()
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    return PackingContext.create(
        items=[ItemSpec(id="a", length=one, weight=zero, amount=1)],
        bins=[BinSpec(id="bin", length=one, max_weight=zero, cost=one)],
        spacing=zero,
        length_unit=length,
        weight_unit=mass,
    ).unwrap()


def _spec(snapshot: PatternRegistration) -> PatternExtensionSpec:
    assert snapshot.stage == "milp"
    assert snapshot.items == [("a", (1, 1), (0, 1), 1, {})]
    assert snapshot.bins == [("bin", (1, 1), (0, 1), (1, 1), None)]
    assert snapshot.spacing == (0, 1)
    assert snapshot.length_unit.symbol == "m" and snapshot.weight_unit.symbol == "kg"
    assert snapshot.objective == "bin_count"
    assert len(snapshot.candidates) == 1
    candidate, pattern = snapshot.candidates[0]
    assert pattern == ("bin", {"a": 1})
    auxiliary = snapshot.auxiliary("extra")
    return PatternExtensionSpec(
        variables=[
            AuxiliaryVariable(name="extra", kind="integer", lower=(0, 1), upper=(1, 1))
        ],
        constraints=[
            ExtensionConstraint(
                name="required", terms=[(auxiliary, (1, 1))], relation="==", rhs=(1, 1)
            )
        ],
        objective=[(auxiliary, (1, 1)), (candidate, (2, 1))],
    )


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def test_extension_registers_exact_model_and_extracts_validated_values(
    solver: str,
) -> None:
    seen: list[dict[VariableRef, tuple[int, int]]] = []

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        assert snapshot.items == [("a", (1, 1), (0, 1), 1, {})]
        assert snapshot.bins == [("bin", (1, 1), (0, 1), (1, 1), None)]
        assert snapshot.candidates[0][1] == ("bin", {"a": 1})
        values = snapshot.values
        seen.append(values.copy())
        return {
            "extra": str(
                values[next(ref for ref in values if ref.auxiliary == "extra")][0]
            )
        }

    result = (
        _context()
        .solve(
            solver=solver,
            max_patterns=10,
            max_nodes=100,
            expansion_limit=1,
            extension=PatternExtension(register=_spec, extract_solution=extract),
        )
        .unwrap()
    )
    solution = result.solution.unwrap()
    assert solution.packed[-1] == (1, 1)
    assert solution.model_objective == (4, 1)
    assert solution.indicators == {"extra": "1"}
    assert len(seen) == 1 and set(seen[0].values()) == {(1, 1)}
    assert result.columns == [("bin", {"a": 1})]
    assert len(result.compiled_columns) == len(result.report.values) == 2
    assert {column.reference.auxiliary for column in result.compiled_columns} == {
        None,
        "extra",
    }
    assert all(
        column.reference.model_identity == result.report.model_identity
        for column in result.compiled_columns
    )
    assert len({column.variable_identity for column in result.compiled_columns}) == 2
    for column, value in zip(
        result.compiled_columns, result.report.values, strict=True
    ):
        assert Fraction(*seen[0][column.reference]) == Fraction.from_float(value)
    result.columns[0][1].clear()
    candidate = next(
        column.pattern for column in result.compiled_columns if column.pattern
    )
    assert candidate == ("bin", {"a": 1})
    assert solution.usages == [("bin", {"a": 1}, 1)]


def test_registration_failure_keeps_result_and_does_not_consume_handle() -> None:
    original: Failed[Any, str, Err[str]] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="denied")
    )
    handle = SolveHandle()
    result = _context().solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=handle,
        extension=PatternExtension(register=lambda _: original),
    )
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is original
    assert result.error.value.error_class == "CALLBACK"
    assert handle.phase == "READY"


def test_registration_rejects_stale_identity_before_solve() -> None:
    references: list[VariableRef] = []

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        current = snapshot.candidates[0][0]
        references.append(current)
        return PatternExtensionSpec(objective=[(references[0], (1, 1))])

    extension = PatternExtension(register=register)
    ctx = _context()
    first = ctx.solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=extension,
    )
    second = ctx.solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=extension,
    )
    assert isinstance(first, Failed) and first.error.value.category == "NOT_SUPPORTED"
    assert isinstance(second, Failed) and second.error.value.category != "NOT_SUPPORTED"
    assert references[0].model_identity != references[1].model_identity


def test_registration_rejects_stale_auxiliary_even_with_same_name() -> None:
    references: list[VariableRef] = []

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        references.append(snapshot.auxiliary("extra"))
        return PatternExtensionSpec(
            variables=[AuxiliaryVariable(name="extra")],
            objective=[(references[0], (1, 1))],
        )

    extension = PatternExtension(register=register)
    ctx = _context()
    first = ctx.solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=extension,
    )
    second = ctx.solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=extension,
    )
    assert isinstance(first, Failed) and first.error.value.category == "NOT_SUPPORTED"
    assert isinstance(second, Failed) and second.error.value.category != "NOT_SUPPORTED"


def test_callback_failure_and_interrupt_identity() -> None:
    error = ValueError("extension")

    def fail(_: PatternRegistration) -> PatternExtensionSpec:
        raise error

    result = _context().solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=PatternExtension(register=fail),
    )
    assert isinstance(result, Failed) and result.error.value.callback_exception is error
    for exception in (KeyboardInterrupt(), SystemExit(2)):

        def interrupt(
            _: PatternRegistration, *, cause: BaseException = exception
        ) -> PatternExtensionSpec:
            raise cause

        with pytest.raises(type(exception)) as captured:
            _context().solve(
                solver="unknown",
                max_patterns=10,
                max_nodes=100,
                expansion_limit=1,
                extension=PatternExtension(register=interrupt),
            )
        assert captured.value is exception


def test_extension_reentry_concurrency_and_release() -> None:
    ctx = _context()
    entered, release = threading.Event(), threading.Event()

    class Register:
        def __call__(self, snapshot: PatternRegistration) -> PatternExtensionSpec:
            assert (
                len(ctx.generate_patterns(max_patterns=10, max_nodes=100).unwrap()[0])
                == 1
            )
            entered.set()
            assert release.wait(timeout=10)
            return _spec(snapshot)

    register = Register()
    reference = weakref.ref(register)
    with ThreadPoolExecutor(max_workers=2) as pool:
        job = pool.submit(
            ctx.solve,
            solver="unknown",
            max_patterns=10,
            max_nodes=100,
            expansion_limit=1,
            extension=PatternExtension(register=register),
        )
        try:
            assert entered.wait(timeout=10)
            other = pool.submit(ctx.generate_patterns, max_patterns=10, max_nodes=100)
            assert len(other.result(timeout=10).unwrap()[0]) == 1
        finally:
            release.set()
        assert job.result(timeout=10).is_failed()
    del register
    gc.collect()
    assert reference() is None


def test_registration_exception_traceback_lifetime() -> None:
    class Register:
        def __call__(self, _: PatternRegistration) -> PatternExtensionSpec:
            raise ValueError("registration")

    register = Register()
    reference = weakref.ref(register)
    result = _context().solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=PatternExtension(register=register),
    )
    assert isinstance(result, Failed)
    del register
    gc.collect()
    assert reference() is not None
    del result
    gc.collect()
    assert reference() is None


def test_indicator_failure_keeps_report_and_result_identity(solver: str) -> None:
    original: Failed[Any, str, Err[str]] = Failed(
        Err(_code=ErrorCode.PERMISSION_DENIED, _message="indicator")
    )
    result = (
        _context()
        .solve(
            solver=solver,
            max_patterns=10,
            max_nodes=100,
            expansion_limit=1,
            extension=PatternExtension(
                register=lambda _: Ok(PatternExtensionSpec()),
                extract_solution=lambda _: original,
            ),
        )
        .unwrap()
    )
    assert result.report.values
    assert isinstance(result.solution, Failed)
    assert result.solution.error.value.callback_result is original
    assert result.solution.error.value.error_class == "CALLBACK"


@pytest.mark.parametrize("kind", ["fatal", "warn", "success", "bad_ok", "bad_dict"])
def test_indicator_rejects_other_results(solver: str, kind: str) -> None:
    error: Err[str] = Err(_code=ErrorCode.PERMISSION_DENIED, _message="indicator")
    returned: Any = {
        "fatal": Fatal((error,)),
        "warn": Warn({}, error),
        "success": Success(),
        "bad_ok": Ok({"x": 1}),
        "bad_dict": {"x": 1},
    }[kind]
    result = (
        _context()
        .solve(
            solver=solver,
            max_patterns=10,
            max_nodes=100,
            expansion_limit=1,
            extension=PatternExtension(
                register=lambda _: PatternExtensionSpec(),
                extract_solution=lambda _: returned,
            ),
        )
        .unwrap()
    )
    assert result.report.values and isinstance(result.solution, Failed)
    assert result.solution.error.value.error_class == "CALLBACK"
    assert result.solution.error.value.callback_result is (
        None if kind == "bad_dict" else returned
    )


@pytest.mark.parametrize(
    "kind", ["failed", "fatal", "warn", "success", "bad_ok", "bad"]
)
def test_registration_rejects_bad_result_without_losing_result_identity(
    kind: str,
) -> None:
    error: Err[str] = Err(_code=ErrorCode.PERMISSION_DENIED, _message="denied")
    returned: Any = {
        "failed": Failed(error),
        "fatal": Fatal((error,)),
        "warn": Warn(PatternExtensionSpec(), error),
        "success": Success(),
        "bad_ok": Ok(None),
        "bad": object(),
    }[kind]
    result = _context().solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=PatternExtension(register=lambda _: returned),
    )
    assert isinstance(result, Failed)
    assert result.error.value.error_class == "CALLBACK"
    assert result.error.value.callback_result is (None if kind == "bad" else returned)


@pytest.mark.parametrize(
    "spec",
    [
        PatternExtensionSpec(variables=[AuxiliaryVariable(name="", kind="integer")]),
        PatternExtensionSpec(variables=[AuxiliaryVariable(name="x", kind="unknown")]),
        PatternExtensionSpec(variables=[AuxiliaryVariable(name="pattern_0")]),
        PatternExtensionSpec(
            variables=[AuxiliaryVariable(name="x", kind="binary", upper=(2, 1))]
        ),
        PatternExtensionSpec(
            variables=[AuxiliaryVariable(name="x", lower=(2, 1), upper=(1, 1))]
        ),
        PatternExtensionSpec(
            variables=[AuxiliaryVariable(name="x"), AuxiliaryVariable(name="x")]
        ),
        PatternExtensionSpec(objective_constant=(0, 0)),
        PatternExtensionSpec(objective_constant=(0, -1)),
        PatternExtensionSpec(objective_constant=(False, 1)),
        PatternExtensionSpec(
            objective=[(VariableRef(model_identity=-1, auxiliary="x"), (1, 1))]
        ),
    ],
)
def test_invalid_declarations_fail_before_solver(spec: PatternExtensionSpec) -> None:
    control = SolveHandle()
    result = _context().solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
        extension=PatternExtension(register=lambda _: spec),
    )
    assert isinstance(result, Failed)
    assert result.error.value.category != "NOT_SUPPORTED"
    assert control.phase == "READY"


@pytest.mark.parametrize("name", ["demand_a", "duplicate"])
def test_extension_rejects_conflicting_row_names(name: str) -> None:
    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        row = ExtensionConstraint(
            name=name,
            terms=[(snapshot.candidates[0][0], (1, 1))],
            relation="<=",
            rhs=(1, 1),
        )
        return PatternExtensionSpec(
            constraints=[row, row] if name == "duplicate" else [row]
        )

    control = SolveHandle()
    result = _context().solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
        extension=PatternExtension(register=register),
    )
    assert isinstance(result, Failed) and result.error.value.category != "NOT_SUPPORTED"
    assert control.phase == "READY"


def test_nonzero_objective_constant_is_not_silently_discarded() -> None:
    control = SolveHandle()
    result = _context().solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
        extension=PatternExtension(
            register=lambda _: PatternExtensionSpec(objective_constant=(1, 1))
        ),
    )
    assert isinstance(result, Failed) and result.error.value.category == "NOT_SUPPORTED"
    assert "constant" in result.error.message.lower()
    assert control.phase == "READY"


@pytest.mark.parametrize("part", ["objective", "coefficient", "rhs", "bound"])
def test_nonbinary_rational_extension_fails_strict_conversion(part: str) -> None:
    control = SolveHandle()

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        candidate = snapshot.candidates[0][0]
        if part == "objective":
            return PatternExtensionSpec(objective=[(candidate, (1, 3))])
        if part == "bound":
            return PatternExtensionSpec(
                variables=[AuxiliaryVariable(name="x", lower=(1, 3))]
            )
        return PatternExtensionSpec(
            constraints=[
                ExtensionConstraint(
                    name="extra",
                    terms=[(candidate, (1, 3) if part == "coefficient" else (1, 1))],
                    relation="<=",
                    rhs=(1, 3) if part == "rhs" else (1, 1),
                )
            ]
        )

    result = _context().solve(
        solver="unknown",
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        cancellation=control,
        extension=PatternExtension(register=register),
    )
    assert isinstance(result, Failed) and "precision" in result.error.message.lower()
    assert control.phase == "READY"


def test_candidate_and_domain_snapshots_do_not_mutate_model(solver: str) -> None:
    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        spec = _spec(snapshot)
        snapshot.items[0][4]["invented"] = 100
        snapshot.candidates[0][1][1].clear()
        snapshot.items.clear()
        snapshot.bins.clear()
        return spec

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        assert snapshot.items == [("a", (1, 1), (0, 1), 1, {})]
        assert snapshot.candidates[0][1] == ("bin", {"a": 1})
        snapshot.candidates[0][1][1].clear()
        snapshot.values.clear()
        return {"fresh": "yes"}

    result = (
        _context()
        .solve(
            solver=solver,
            max_patterns=10,
            max_nodes=100,
            expansion_limit=1,
            extension=PatternExtension(register=register, extract_solution=extract),
        )
        .unwrap()
    )
    assert result.columns == [("bin", {"a": 1})]
    assert result.solution.unwrap().packed[2] == {}
    assert result.solution.unwrap().model_objective == (4, 1)
    assert result.solution.unwrap().indicators == {"fresh": "yes"}


def test_indicators_run_only_after_valid_solution_but_before_expansion(
    solver: str,
) -> None:
    calls: list[dict[VariableRef, tuple[int, int]]] = []

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        calls.append(snapshot.values)
        return {}

    ctx = _context()
    infeasible = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        policy=lambda _: False,
        extension=PatternExtension(
            register=lambda _: PatternExtensionSpec(), extract_solution=extract
        ),
    ).unwrap()
    assert infeasible.solution.is_failed() and not calls

    no_expansion = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=0,
        extension=PatternExtension(
            register=lambda _: PatternExtensionSpec(), extract_solution=extract
        ),
    ).unwrap()
    assert no_expansion.solution.is_failed() and len(calls) == 1


def test_empty_solution_still_provides_domain_snapshot(solver: str) -> None:
    zero = Rational.from_value(0).unwrap()
    one = Rational.from_value(1).unwrap()
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    ctx = PackingContext.create(
        items=[],
        bins=[BinSpec(id="bin", length=one, max_weight=zero, cost=one)],
        spacing=zero,
        length_unit=length,
        weight_unit=mass,
    ).unwrap()

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        assert (
            snapshot.items == [] and snapshot.candidates == [] and snapshot.values == {}
        )
        assert snapshot.bins[0][0] == "bin" and snapshot.length_unit.symbol == "m"
        return {"empty": "yes"}

    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=0,
        extension=PatternExtension(
            register=lambda _: PatternExtensionSpec(),
            extract_solution=extract,
        ),
    ).unwrap()
    assert result.compiled_columns == [] and result.solution.unwrap().indicators == {
        "empty": "yes"
    }


def test_extraction_exception_and_interrupt(solver: str) -> None:
    error = ValueError("extract")

    def fail(_: PatternExtraction) -> dict[str, str]:
        raise error

    ctx = _context()
    result = ctx.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=PatternExtension(
            register=lambda _: PatternExtensionSpec(), extract_solution=fail
        ),
    ).unwrap()
    assert isinstance(result.solution, Failed)
    assert result.solution.error.value.callback_exception is error
    for exception in (KeyboardInterrupt(), SystemExit(2)):

        def interrupt(
            _: PatternExtraction, *, cause: BaseException = exception
        ) -> dict[str, str]:
            raise cause

        with pytest.raises(type(exception)) as captured:
            ctx.solve(
                solver=solver,
                max_patterns=10,
                max_nodes=100,
                expansion_limit=1,
                extension=PatternExtension(
                    register=lambda _: PatternExtensionSpec(),
                    extract_solution=interrupt,
                ),
            )
        assert captured.value is exception


def test_concurrent_registrations_keep_model_identities_separate() -> None:
    ctx = _context()
    barrier = threading.Barrier(2)

    def run() -> int:
        identity = 0

        def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
            nonlocal identity
            identity = snapshot.model_identity
            barrier.wait(timeout=10)
            return _spec(snapshot)

        assert ctx.solve(
            solver="unknown",
            max_patterns=10,
            max_nodes=100,
            expansion_limit=1,
            extension=PatternExtension(register=register),
        ).is_failed()
        return identity

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(run), pool.submit(run)
        assert first.result(timeout=10) != second.result(timeout=10)


def test_downstream_example_uses_real_backend(solver: str) -> None:
    from examples.bpp1d_model_extension_example import solve

    solution = solve(solver=solver)
    assert solution.packed[-1] == (1, 1)
    assert solution.model_objective == (3, 1)
    assert solution.indicators == {"enabled": "1/1"}


def test_continuous_auxiliary_keeps_exact_binary_fraction(solver: str) -> None:
    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        auxiliary = snapshot.auxiliary("fraction")
        return PatternExtensionSpec(
            variables=[
                AuxiliaryVariable(name="fraction", kind="continuous", lower=(0, 1))
            ],
            constraints=[
                ExtensionConstraint(
                    name="half",
                    terms=[(auxiliary, (1, 1))],
                    relation="==",
                    rhs=(1, 2),
                )
            ],
            objective=[(auxiliary, (1, 1))],
        )

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        auxiliary = next(ref for ref in snapshot.values if ref.auxiliary == "fraction")
        assert snapshot.values[auxiliary] == (1, 2)
        return {"fraction": "1/2"}

    result = (
        _context()
        .solve(
            solver=solver,
            max_patterns=10,
            max_nodes=100,
            expansion_limit=1,
            extension=PatternExtension(register=register, extract_solution=extract),
        )
        .unwrap()
    )
    assert result.solution.unwrap().model_objective == (3, 2)
    assert result.solution.unwrap().indicators == {"fraction": "1/2"}
