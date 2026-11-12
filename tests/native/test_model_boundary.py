"""真实扩展的模型身份、原子性和 Result 合同 / Real-extension identity, atomicity and Result contracts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from ospf_python import _native
from ospf_python._binding.model import (
    ConstraintSpec,
    MetaModelFloat64,
    VariableSpec,
)
from ospf_python._binding.result import invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result


def model(name: str = "test") -> MetaModelFloat64:
    return MetaModelFloat64.create(name).unwrap()


def test_model_identity_and_single_state() -> None:
    first, second = model("first"), model("second")
    assert first.model_identity != second.model_identity
    variables = first.add_variables([VariableSpec(name="x")]).unwrap()
    assert variables[0].model_identity == first.model_identity
    assert first.snapshot().unwrap() == (first.model_identity, "first", 1, 0)
    assert second.snapshot().unwrap() == (second.model_identity, "second", 0, 0)
    assert set(vars(first)) == {"_handle"}


def test_native_failure_uses_existing_result_and_semantic_codes() -> None:
    result = model().add_variables([VariableSpec(name="bad", lower=2, upper=1)])
    assert isinstance(result, Result)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert result.error.value.rust_code == 0x34
    assert result.error.code.value == 2
    assert result.error.value.source == "ospf-python-native"
    with pytest.raises(FrozenInstanceError):
        result.error.value.source = "changed"  # type: ignore[misc]


def test_duplicate_variable_failure_rolls_back_entire_batch() -> None:
    instance = model()
    result = instance.add_variables([VariableSpec(name="x"), VariableSpec(name="x")])
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ALREADY_EXIST
    assert result.error.value.source == "ospf-python-native"
    assert result.error.value.rust_code is None
    assert instance.snapshot().unwrap()[2:] == (0, 0)
    assert instance.add_variables([VariableSpec(name="x")]).is_ok()


@pytest.mark.parametrize(
    "spec",
    [
        VariableSpec(name="bad", kind="unknown"),
        VariableSpec(name="bad", lower=float("nan")),
        VariableSpec(name="bad", upper=float("inf")),
        VariableSpec(name="bad", lower=2**53 + 1),
        VariableSpec(name="bad", kind="integer", lower=0.5),
        VariableSpec(name="bad", kind="integer", upper=float(2**53)),
        VariableSpec(name="bad", kind="binary", upper=2),
        VariableSpec(name="bad", lower=True),
    ],
)
def test_invalid_bounds_and_precision_do_not_mutate(spec: VariableSpec) -> None:
    instance = model()
    assert instance.add_variables([VariableSpec(name="valid"), spec]).is_failed()
    assert instance.snapshot().unwrap()[2:] == (0, 0)


def test_constraint_batch_rolls_back_and_rejects_cross_model_handles() -> None:
    instance, other = model(), model()
    x = instance.add_variables([VariableSpec(name="x")]).unwrap()[0]
    y = other.add_variables([VariableSpec(name="y")]).unwrap()[0]
    result = instance.add_constraints(
        [
            ConstraintSpec(name="valid", terms=[(x, 1)], relation="<=", rhs=5),
            ConstraintSpec(name="foreign", terms=[(y, 1)], relation="<=", rhs=5),
        ]
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert instance.snapshot().unwrap()[2:] == (1, 0)
    assert instance.add_constraints(
        [ConstraintSpec(name="ok", terms=[(x, 1)], relation="<=", rhs=5)]
    ).is_ok()


@pytest.mark.parametrize("relation,rhs", [("bad", 1), ("<=", float("nan"))])
def test_constraint_validation_is_atomic(relation: str, rhs: float) -> None:
    instance = model()
    x = instance.add_variables([VariableSpec(name="x")]).unwrap()[0]
    assert instance.add_constraints(
        [
            ConstraintSpec(name="first", terms=[(x, 1)], relation="<=", rhs=5),
            ConstraintSpec(name="bad", terms=[(x, 1)], relation=relation, rhs=rhs),
        ]
    ).is_failed()
    assert instance.snapshot().unwrap()[3] == 0


def test_handles_are_immutable_and_cannot_be_forged() -> None:
    handle = model().add_variables([VariableSpec(name="x")]).unwrap()[0]
    with pytest.raises(AttributeError):
        handle.index = 99  # type: ignore[misc]
    with pytest.raises(TypeError):
        _native.VariableHandle()


def test_all_variable_consumers_reject_foreign_handles_atomically() -> None:
    first, other = model("same-name"), model("same-name")
    try:
        x = first.add_variables([VariableSpec(name="x", lower=0, upper=2)]).unwrap()[0]
        foreign = other.add_variables(
            [VariableSpec(name="x", lower=0, upper=2)]
        ).unwrap()[0]
        generation = first.generation().unwrap()
        for result in (
            first.add_constraints(
                [
                    ConstraintSpec(name="local", terms=[(x, 1)], relation="<=", rhs=1),
                    ConstraintSpec(
                        name="foreign", terms=[(foreign, 1)], relation="<=", rhs=1
                    ),
                ]
            ),
            first.set_bounds(handle=foreign, lower=0, upper=1),
            first.set_objective(terms=[(x, 1), (foreign, 1)], sense="maximize"),
        ):
            assert isinstance(result, Failed)
            assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert first.generation().unwrap() == generation
        assert first.snapshot().unwrap()[2:] == (1, 0)
        assert first.add_constraints(
            [ConstraintSpec(name="local", terms=[(x, 1)], relation="<=", rhs=1)]
        ).is_ok()
        assert first.set_bounds(handle=x, lower=0, upper=1).is_ok()
        assert first.set_objective(terms=[(x, 1)], sense="maximize").is_ok()
        assert not hasattr(x, "provenance")
    finally:
        first.close().unwrap()
        other.close().unwrap()


def test_close_is_idempotent_and_invalidates_operations() -> None:
    instance = model()
    x = instance.add_variables([VariableSpec(name="x")]).unwrap()[0]
    identity = instance.model_identity
    assert isinstance(instance.close(), Ok)
    assert isinstance(instance.close(), Ok)
    assert instance.model_identity == identity
    operations = [
        instance.snapshot(),
        instance.add_variables([VariableSpec(name="y")]),
        instance.set_objective(terms=[(x, 1)], sense="maximize"),
        instance.solve(solver="scip"),
    ]
    for result in operations:
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.NOT_INITIALIZED


def test_python_threads_use_the_same_rust_owner() -> None:
    instance = model()
    with ThreadPoolExecutor(max_workers=1) as pool:
        handle = (
            pool.submit(
                instance.add_variables, [VariableSpec(name="from_other_thread")]
            )
            .result(timeout=10)
            .unwrap()[0]
        )
    assert handle.model_identity == instance.model_identity
    assert instance.snapshot().unwrap()[2] == 1
    assert instance.close().is_ok()


def test_pyo3_conversion_errors_become_failed_at_adapter_boundary() -> None:
    result = invoke(lambda: _native._create_model(123))  # type: ignore[arg-type]
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_uncompiled_and_unsupported_backends_are_explicit_failures() -> None:
    instance = model()
    compiled = _native.build_info()["native_solvers"].split(",")
    for solver in ("scip", "gurobi10", "gurobi11", "gurobi12"):
        if solver not in compiled:
            result = instance.solve(solver=solver)
            assert isinstance(result, Failed)
            assert result.error.code is ErrorCode.SOLVER_NOT_AVAILABLE
    result = instance.solve(solver="gurobi13")
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.NOT_SUPPORTED


def test_nonzero_objective_constant_is_not_silently_lost() -> None:
    instance = model()
    x = instance.add_variables([VariableSpec(name="x", lower=0, upper=2)]).unwrap()[0]
    assert instance.set_objective(terms=[(x, 1)], sense="maximize").is_ok()
    result = instance.set_objective(terms=[(x, 10)], sense="maximize", constant=5)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.NOT_SUPPORTED


@pytest.mark.parametrize("seconds", [-1, float("inf"), float("nan"), 1e100])
def test_invalid_time_limits_return_result(seconds: float) -> None:
    result = model().solve(solver="scip", time_limit=seconds)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
