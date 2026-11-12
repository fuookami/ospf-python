"""私有原约束身份合同 / Private source-constraint identity contracts."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


def test_source_handles_are_distinct_from_names_and_solver_rows() -> None:
    model = MetaModelFloat64.create("source-identities").unwrap()
    try:
        assert model.constraint_handles().unwrap() == []
        x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
        result = model.add_constraints(
            [
                ConstraintSpec(name="row", terms=[(x, 1)], relation="==", rhs=2),
                ConstraintSpec(name="row_eq_le", terms=[(x, 1)], relation="<=", rhs=3),
                ConstraintSpec(name="lower", terms=[(x, 1)], relation=">=", rhs=1),
            ]
        )
        assert result.is_ok()
        handles = model.constraint_handles().unwrap()
        assert [(h.name, h.relation) for h in handles] == [
            ("row", "=="),
            ("row_eq_le", "<="),
            ("lower", ">="),
        ]
        assert len({h.source_identity for h in handles}) == 3
        assert all(h.model_identity == model.model_identity for h in handles)
        assert [model.constraint_index(handle=h).unwrap() for h in handles] == [0, 1, 2]
        assert [h.source_identity for h in model.constraint_handles().unwrap()] == [
            h.source_identity for h in handles
        ]
        invalid = model.constraint_index(handle=None)  # type: ignore[arg-type]
        assert isinstance(invalid, Failed)
        assert invalid.error.code is ErrorCode.ILLEGAL_ARGUMENT
        with pytest.raises(AttributeError):
            handles[0].source_identity = "forged"  # type: ignore[misc]
        with pytest.raises(TypeError):
            _native.ConstraintHandle()
    finally:
        model.close().unwrap()


def test_duplicate_names_and_failed_batch_leave_published_handles_unchanged() -> None:
    model = MetaModelFloat64.create("constraint-rollback").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
        model.add_constraints(
            [ConstraintSpec(name="existing", terms=[(x, 1)], relation="<=", rhs=2)]
        ).unwrap()
        handle = model.constraint_handles().unwrap()[0]
        result = model.add_constraints(
            [
                ConstraintSpec(name="transient", terms=[(x, 1)], relation="<=", rhs=3),
                ConstraintSpec(name="existing", terms=[(x, 1)], relation=">=", rhs=1),
            ]
        )
        assert isinstance(result, Failed)
        assert model.snapshot().unwrap()[3] == 1
        assert model.constraint_index(handle=handle).unwrap() == 0
        assert [h.source_identity for h in model.constraint_handles().unwrap()] == [
            handle.source_identity
        ]
        model.add_constraints(
            [ConstraintSpec(name="transient", terms=[(x, 1)], relation="<=", rhs=3)]
        ).unwrap()
        assert model.constraint_index(handle=handle).unwrap() == 0
        assert len(model.constraint_handles().unwrap()) == 2
    finally:
        model.close().unwrap()


def test_foreign_and_closed_models_reject_constraint_handles() -> None:
    first = MetaModelFloat64.create("same-name").unwrap()
    second = MetaModelFloat64.create("same-name").unwrap()
    try:
        for model in (first, second):
            x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
            model.add_constraints(
                [ConstraintSpec(name="row", terms=[(x, 1)], relation="<=", rhs=2)]
            ).unwrap()
        handle = first.constraint_handles().unwrap()[0]
        other = second.constraint_handles().unwrap()[0]
        assert handle.source_identity != other.source_identity
        foreign = second.constraint_index(handle=handle)
        assert isinstance(foreign, Failed)
        assert foreign.error.code is ErrorCode.ILLEGAL_ARGUMENT
        first.close().unwrap()
        for result in (
            first.constraint_handles(),
            first.constraint_index(handle=handle),
        ):
            assert isinstance(result, Failed)
            assert result.error.code is ErrorCode.NOT_INITIALIZED
    finally:
        first.close().unwrap()
        second.close().unwrap()


def test_nonfinite_combined_row_is_rejected_before_publication() -> None:
    model = MetaModelFloat64.create("nonfinite-snapshot").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
        generation = model.generation().unwrap()
        result = model.add_constraints(
            [
                ConstraintSpec(
                    name="overflow",
                    terms=[(x, 1e308), (x, 1e308)],
                    relation="<=",
                    rhs=1,
                )
            ]
        )
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.OVERFLOW
        assert model.constraint_handles().unwrap() == []
        assert model.snapshot().unwrap()[2:] == (1, 0)
        assert model.generation().unwrap() == generation
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
def test_source_identity_survives_bounds_and_real_solves(solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    model = MetaModelFloat64.create("identity-solve").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0)]).unwrap()[0]
        model.add_constraints(
            [ConstraintSpec(name="limit", terms=[(x, 1)], relation="<=", rhs=2)]
        ).unwrap()
        model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
        handle = model.constraint_handles().unwrap()[0]
        errors: list[ErrorCode] = []

        def callback(event: object) -> None:
            if not errors:
                result = model.constraint_index(handle=handle)
                assert isinstance(result, Failed)
                errors.append(result.error.code)

        assert model.solve(solver=solver, on_progress=callback).unwrap().objective == 6
        assert errors == [ErrorCode.FAILED_PRECONDITION]
        model.set_bounds(handle=x, lower=0, upper=1).unwrap()
        assert model.solve(solver=solver).unwrap().objective == 3
        assert model.constraint_index(handle=handle).unwrap() == 0
        assert (
            model.constraint_handles().unwrap()[0].source_identity
            == handle.source_identity
        )
    finally:
        model.close().unwrap()
