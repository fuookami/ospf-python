"""私有列池与主问题生命周期合同 / Private column-pool and master lifecycle contracts."""

from __future__ import annotations

import gc

import pytest

from ospf_python import _native
from ospf_python._binding.model import (
    ColumnDecisionSpec,
    ColumnProjectionFloat64,
    ColumnSpec,
    ConstraintSpec,
    MetaModelFloat64,
    VariableSpec,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


def setup() -> tuple[MetaModelFloat64, ColumnProjectionFloat64]:
    model = MetaModelFloat64.create("projection").unwrap()
    x, y = model.add_variables(
        [VariableSpec(name="x", kind="binary"), VariableSpec(name="y", kind="binary")]
    ).unwrap()
    model.add_constraints(
        [ConstraintSpec(name="capacity", terms=[(x, 1), (y, 1)], relation="<=", rhs=1)]
    ).unwrap()
    model.set_objective(terms=[(x, 3), (y, 2)], sense="maximize").unwrap()
    projection = model.create_projection(
        decisions=[
            ColumnDecisionSpec(id="x", block="a", variable=x),
            ColumnDecisionSpec(id="y", block="b", variable=y),
        ],
        blocks=["a", "b"],
    ).unwrap()
    return model, projection


def seed() -> list[ColumnSpec]:
    return [
        ColumnSpec(id="a0", block="a", values={"x": 0}),
        ColumnSpec(id="b0", block="b", values={"y": 0}),
    ]


def test_creation_checks_provenance_and_mapping_without_mutating_source() -> None:
    model = MetaModelFloat64.create("source").unwrap()
    foreign = MetaModelFloat64.create("source").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
        y = foreign.add_variables([VariableSpec(name="x")]).unwrap()[0]
        generation = model.generation().unwrap()
        for decisions, blocks in (
            ([ColumnDecisionSpec(id="x", block="a", variable=y)], ["a"]),
            ([ColumnDecisionSpec(id="x", block="a", variable=x)], ["a", "a"]),
            ([ColumnDecisionSpec(id="x", block="missing", variable=x)], ["a"]),
            (
                [
                    ColumnDecisionSpec(id="x", block="a", variable=x),
                    ColumnDecisionSpec(id="x", block="a", variable=x),
                ],
                ["a"],
            ),
        ):
            assert model.create_projection(
                decisions=decisions, blocks=blocks
            ).is_failed()
        assert model.generation().unwrap() == generation
        assert model.snapshot().unwrap()[2:] == (1, 0)
        with pytest.raises(TypeError):
            _native.ColumnProjection()
    finally:
        model.close().unwrap()
        foreign.close().unwrap()


def test_seed_batch_rollback_detached_snapshots_and_master_rebuild() -> None:
    model, projection = setup()
    try:
        generation = model.generation().unwrap()
        columns = seed()
        projection.add_columns(columns).unwrap()
        columns[0].values["x"] = 1  # type: ignore[index]
        snapshot = projection.columns().unwrap()
        assert snapshot == seed()
        snapshot[0].values["x"] = 1  # type: ignore[index]
        assert projection.columns().unwrap() == seed()

        lp = projection.build_master().unwrap()
        assert (
            lp.source_generation,
            lp.integer,
            lp.columns,
            lp.variables,
            lp.rows,
        ) == (
            generation,
            False,
            2,
            2,
            3,
        )
        assert projection.master_info().unwrap() == lp
        for invalid in (
            [ColumnSpec(id="duplicate", block="a", values={"x": 1}), seed()[1]],
            [ColumnSpec(id="missing", block="a", values={})],
            [ColumnSpec(id="fractional", block="a", values={"x": 0.5})],
            [ColumnSpec(id="outside", block="a", values={"x": 2})],
            [ColumnSpec(id="nan", block="a", values={"x": float("nan")})],
            [ColumnSpec(id="precision", block="a", values={"x": 2**53})],
        ):
            assert projection.add_columns(invalid).is_failed()
            assert projection.columns().unwrap() == seed()
            assert projection.master_info().unwrap() == lp
        assert projection.remove_columns(["a0", "missing"]).is_failed()
        assert projection.columns().unwrap() == seed()
        assert projection.master_info().unwrap() == lp
        projection.add_columns([]).unwrap()
        projection.remove_columns([]).unwrap()
        assert projection.master_info().unwrap() == lp

        projection.add_columns(
            [ColumnSpec(id="a1", block="a", values={"x": 1})]
        ).unwrap()
        assert projection.master_info().is_failed()
        mip = projection.build_master(integer=True).unwrap()
        assert mip.integer and mip.columns == 3 and mip.variables == 3
        assert mip.rows == 3
        assert not lp.integer and lp.columns == 2
        projection.remove_columns(["a1"]).unwrap()
        assert projection.master_info().is_failed()
        assert projection.build_master().unwrap().columns == 2
        assert model.generation().unwrap() == generation
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_source_mutation_and_restore_do_not_revive_old_master() -> None:
    model, projection = setup()
    try:
        projection.add_columns(seed()).unwrap()
        first = projection.build_master().unwrap()
        x = model.add_variables(
            [VariableSpec(name="extra", lower=0, upper=0)]
        ).unwrap()[0]
        stale = projection.master_info()
        assert isinstance(stale, Failed)
        assert stale.error.code is ErrorCode.FAILED_PRECONDITION
        second = projection.build_master().unwrap()
        assert second.source_generation == first.source_generation + 1
        model.set_bounds(handle=x, lower=0, upper=1).unwrap()
        model.set_bounds(handle=x, lower=0, upper=0).unwrap()
        assert projection.master_info().is_failed()
        assert projection.build_master().unwrap().source_generation == (
            second.source_generation + 2
        )
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_rebuild_revalidates_existing_columns_after_source_bounds_change() -> None:
    model = MetaModelFloat64.create("bounds-change").unwrap()
    x = model.add_variables([VariableSpec(name="x", kind="binary")]).unwrap()[0]
    model.set_objective(terms=[(x, 1)], sense="maximize").unwrap()
    projection = model.create_projection(
        decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)], blocks=["a"]
    ).unwrap()
    try:
        projection.add_columns(
            [ColumnSpec(id="one", block="a", values={"x": 1})]
        ).unwrap()
        projection.build_master().unwrap()
        model.set_bounds(handle=x, lower=0, upper=0).unwrap()
        assert projection.build_master().is_failed()
        assert projection.master_info().is_failed()
        assert projection.columns().unwrap()[0].id == "one"
        projection.remove_columns(["one"]).unwrap()
        projection.add_columns(
            [ColumnSpec(id="zero", block="a", values={"x": 0})]
        ).unwrap()
        assert projection.build_master().unwrap().columns == 1
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_projection_lifetime_independence_and_model_close() -> None:
    model, first = setup()
    second = model.create_projection(decisions=[], blocks=["c"]).unwrap()
    try:
        first.add_columns(seed()).unwrap()
        second.add_columns([ColumnSpec(id="c0", block="c", values={})]).unwrap()
        first_master = first.build_master().unwrap()
        second_master = second.build_master().unwrap()
        first.remove_columns(["a0"]).unwrap()
        assert first.master_info().is_failed()
        assert second.master_info().unwrap() == second_master
        assert first_master.columns == 2
        first.close().unwrap()
        first.close().unwrap()
        assert first.columns().is_failed()
        assert second.columns().is_ok()
        model.close().unwrap()
        result = second.columns()
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.NOT_INITIALIZED
        second.close().unwrap()
        second.close().unwrap()
    finally:
        first.close().unwrap()
        second.close().unwrap()
        model.close().unwrap()


def test_projection_keeps_its_source_owner_alive_without_a_python_model_copy() -> None:
    model, projection = setup()
    projection.add_columns(seed()).unwrap()
    del model
    gc.collect()
    try:
        assert set(vars(projection)) == {"_handle"}
        assert projection.columns().unwrap() == seed()
        assert projection.build_master().unwrap().columns == 2
    finally:
        projection.close().unwrap()


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
def test_projection_reentry_and_finalizer_during_real_solve(solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    model, projection = setup()
    projection.add_columns(seed()).unwrap()
    projection.build_master().unwrap()
    temporary = [model.create_projection(decisions=[], blocks=["extra"]).unwrap()]
    errors: list[ErrorCode] = []

    def callback(event: object) -> None:
        if errors:
            return
        for result in (
            projection.columns(),
            projection.add_columns(seed()),
            projection.remove_columns(["a0"]),
            projection.build_master(),
            projection.master_info(),
            projection.close(),
            model.create_projection(decisions=[], blocks=["another"]),
        ):
            assert isinstance(result, Failed)
            errors.append(result.error.code)
        temporary.clear()
        gc.collect()

    try:
        assert model.solve(solver=solver, on_progress=callback).is_ok()
        assert errors == [ErrorCode.FAILED_PRECONDITION] * 7
        assert projection.columns().unwrap() == seed()
        assert projection.master_info().is_ok()
    finally:
        projection.close().unwrap()
        model.close().unwrap()
