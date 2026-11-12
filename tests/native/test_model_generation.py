"""私有模型修改代次合同 / Private model mutation-generation contracts."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


def test_successful_mutations_advance_generation_and_reads_do_not() -> None:
    model = MetaModelFloat64.create("generation").unwrap()
    try:
        assert model.generation().unwrap() == 0
        assert model.snapshot().is_ok()
        assert model.constraint_handles().is_ok()
        assert model.generation().unwrap() == 0
        assert model.add_variables([]).unwrap() == []
        assert model.generation().unwrap() == 1
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=3)]).unwrap()[0]
        assert model.generation().unwrap() == 2
        model.add_constraints(
            [ConstraintSpec(name="row", terms=[(x, 1)], relation="<=", rhs=2)]
        ).unwrap()
        assert model.generation().unwrap() == 3
        model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
        assert model.generation().unwrap() == 4
        model.set_bounds(handle=x, lower=0, upper=1).unwrap()
        assert model.generation().unwrap() == 5
        model.set_bounds(handle=x, lower=0, upper=3).unwrap()
        assert model.generation().unwrap() == 6
        model.set_bounds(handle=x, lower=0, upper=3).unwrap()
        model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
        model.add_constraints([]).unwrap()
        assert model.generation().unwrap() == 9
    finally:
        model.close().unwrap()


def test_failed_mutations_leave_generation_and_model_unchanged() -> None:
    model = MetaModelFloat64.create("failed-generation").unwrap()
    other = MetaModelFloat64.create("other").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=2)]).unwrap()[0]
        foreign = other.add_variables([VariableSpec(name="foreign")]).unwrap()[0]
        model.add_constraints(
            [ConstraintSpec(name="existing", terms=[(x, 1)], relation="<=", rhs=2)]
        ).unwrap()
        generation = model.generation().unwrap()
        failed = [
            model.add_variables(
                [VariableSpec(name="temporary"), VariableSpec(name="x")]
            ),
            model.add_constraints(
                [
                    ConstraintSpec(
                        name="temporary", terms=[(x, 1)], relation="<=", rhs=1
                    ),
                    ConstraintSpec(
                        name="existing", terms=[(x, 1)], relation="<=", rhs=1
                    ),
                ]
            ),
            model.set_bounds(handle=x, lower=2, upper=1),
            model.set_bounds(handle=foreign, lower=0, upper=1),
            model.set_objective(terms=[(x, 1)], sense="invalid"),
            model.set_objective(terms=[(x, 1)], sense="maximize", constant=1),
        ]
        assert all(isinstance(result, Failed) for result in failed)
        assert model.generation().unwrap() == generation
        assert model.snapshot().unwrap()[2:] == (1, 1)
        assert [handle.name for handle in model.constraint_handles().unwrap()] == [
            "existing"
        ]
        model.add_variables([VariableSpec(name="temporary")]).unwrap()
        assert model.generation().unwrap() == generation + 1
    finally:
        model.close().unwrap()
        other.close().unwrap()


def test_closed_model_does_not_return_a_generation() -> None:
    model = MetaModelFloat64.create("closed-generation").unwrap()
    model.close().unwrap()
    result = model.generation()
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.NOT_INITIALIZED


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
def test_reports_capture_the_generation_of_each_real_solve(solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    model = MetaModelFloat64.create("generation-solve").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=3)]).unwrap()[0]
        model.add_constraints(
            [ConstraintSpec(name="capacity", terms=[(x, 1)], relation="<=", rhs=2)]
        ).unwrap()
        model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
        generation = model.generation().unwrap()
        busy: list[ErrorCode] = []

        def callback(event: object) -> None:
            if not busy:
                result = model.generation()
                assert isinstance(result, Failed)
                busy.append(result.error.code)

        first = model.solve(solver=solver, on_progress=callback).unwrap()
        second = model.solve(solver=solver).unwrap()
        assert busy == [ErrorCode.FAILED_PRECONDITION]
        assert first.model_identity == second.model_identity == model.model_identity
        assert first.model_generation == second.model_generation == generation
        assert first.objective == second.objective == pytest.approx(6)
        assert model.set_bounds(handle=x, lower=2, upper=1).is_failed()
        assert model.generation().unwrap() == generation
        model.set_bounds(handle=x, lower=0, upper=1).unwrap()
        changed = model.solve(solver=solver).unwrap()
        model.set_bounds(handle=x, lower=0, upper=3).unwrap()
        restored = model.solve(solver=solver).unwrap()
        assert changed.model_generation == generation + 1
        assert changed.objective == pytest.approx(3)
        assert restored.model_generation == generation + 2
        assert restored.objective == first.objective
        model.close().unwrap()
        assert first.model_generation == generation
        assert first.objective == pytest.approx(6)
    finally:
        model.close().unwrap()
