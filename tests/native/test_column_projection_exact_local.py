"""投影列的零容差局部校验 / Zero-tolerance local validation of projected columns."""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from ospf_python import _native
from ospf_python._binding.model import (
    ColumnDecisionSpec,
    ColumnSpec,
    ConstraintSpec,
    MetaModelFloat64,
    VariableSpec,
)


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


@pytest.mark.parametrize("relation,sign", [("<=", 1), (">=", -1), ("==", 1)])
def test_local_row_rejects_cancellation_hidden_by_float_sum(
    relation: str, sign: int
) -> None:
    coefficients = [sign * 1e16, sign * 1.0, -sign * 1e16]
    assert (coefficients[0] + coefficients[1]) + coefficients[2] == 0.0
    assert sum(map(Fraction.from_float, coefficients)) == sign

    model = MetaModelFloat64.create("local cancellation").unwrap()
    projection = None
    try:
        names = ("x", "y", "z")
        variables = model.add_variables(
            [VariableSpec(name=name, kind="binary") for name in names]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name="local",
                    terms=list(zip(variables, coefficients, strict=True)),
                    relation=relation,
                    rhs=0,
                )
            ]
        ).unwrap()
        model.set_objective(terms=[], sense="minimize").unwrap()
        projection = model.create_projection(
            decisions=[
                ColumnDecisionSpec(id=name, block="a", variable=variable)
                for name, variable in zip(names, variables, strict=True)
            ],
            blocks=["a"],
        ).unwrap()
        zero = ColumnSpec(id="zero", block="a", values=dict.fromkeys(names, 0))
        projection.add_columns([zero]).unwrap()
        master = projection.build_master().unwrap()
        candidate = ColumnSpec(id="one", block="a", values=dict.fromkeys(names, 1))
        assert projection.add_columns([candidate]).is_failed()
        assert projection.columns().unwrap() == [zero]
        assert projection.master_info().unwrap() == master
    finally:
        if projection is not None:
            projection.close().unwrap()
        model.close().unwrap()


@pytest.mark.parametrize(
    "kind,value",
    [
        ("binary", math.nextafter(1.0, 0.0)),
        ("binary", math.nextafter(0.0, 1.0)),
        ("continuous", math.nextafter(1.0, math.inf)),
        ("continuous", math.nextafter(0.0, -math.inf)),
    ],
)
def test_local_variable_domain_uses_zero_tolerance(kind: str, value: float) -> None:
    exact = Fraction.from_float(value)
    assert (exact.denominator != 1) if kind == "binary" else not 0 <= exact <= 1
    model = MetaModelFloat64.create("local bound").unwrap()
    projection = None
    try:
        x = model.add_variables(
            [VariableSpec(name="x", kind=kind, lower=0, upper=1)]
        ).unwrap()[0]
        model.set_objective(terms=[], sense="minimize").unwrap()
        projection = model.create_projection(
            decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)],
            blocks=["a"],
        ).unwrap()
        valid = ColumnSpec(id="valid", block="a", values={"x": 0})
        projection.add_columns([valid]).unwrap()
        master = projection.build_master().unwrap()
        assert projection.add_columns(
            [ColumnSpec(id="invalid", block="a", values={"x": value})]
        ).is_failed()
        assert projection.columns().unwrap() == [valid]
        assert projection.master_info().unwrap() == master
    finally:
        if projection is not None:
            projection.close().unwrap()
        model.close().unwrap()


def test_rebuild_rechecks_existing_column_against_new_local_row() -> None:
    model = MetaModelFloat64.create("new local row").unwrap()
    projection = None
    try:
        x = model.add_variables([VariableSpec(name="x", kind="binary")]).unwrap()[0]
        model.set_objective(terms=[], sense="minimize").unwrap()
        projection = model.create_projection(
            decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)],
            blocks=["a"],
        ).unwrap()
        column = ColumnSpec(id="one", block="a", values={"x": 1})
        projection.add_columns([column]).unwrap()
        projection.build_master().unwrap()
        model.add_constraints(
            [ConstraintSpec(name="local", terms=[(x, 1)], relation="<=", rhs=0)]
        ).unwrap()
        assert projection.master_info().is_failed()
        assert projection.build_master().is_failed()
        assert projection.columns().unwrap() == [column]
    finally:
        if projection is not None:
            projection.close().unwrap()
        model.close().unwrap()


def test_priced_batch_rejects_near_integer_without_invalidating_request(
    solver: str,
) -> None:
    model = MetaModelFloat64.create("priced local integrality").unwrap()
    projection = None
    try:
        x = model.add_variables([VariableSpec(name="x", kind="binary")]).unwrap()[0]
        model.set_objective(terms=[], sense="minimize").unwrap()
        projection = model.create_projection(
            decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)],
            blocks=["a"],
        ).unwrap()
        zero = ColumnSpec(id="zero", block="a", values={"x": 0})
        projection.add_columns([zero]).unwrap()
        master = projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        good = ColumnSpec(id="one", block="a", values={"x": 1})
        near = ColumnSpec(id="near", block="a", values={"x": math.nextafter(1.0, 0.0)})
        assert projection.add_priced_batch([(request, [good, near])]).is_failed()
        assert projection.columns().unwrap() == [zero]
        assert projection.master_info().unwrap() == master
        assert projection.pricing_info(request=request).is_ok()
        projection.add_priced_batch([(request, [good])]).unwrap()
        assert projection.pricing_info(request=request).is_failed()
    finally:
        if projection is not None:
            projection.close().unwrap()
        model.close().unwrap()


def test_cross_block_rows_are_master_constraints_not_local_rows(solver: str) -> None:
    model = MetaModelFloat64.create("cross block").unwrap()
    projection = None
    try:
        x, y = model.add_variables(
            [VariableSpec(name=name, kind="binary") for name in ("x", "y")]
        ).unwrap()
        model.add_constraints(
            [ConstraintSpec(name="cross", terms=[(x, 1), (y, 1)], relation="<=", rhs=0)]
        ).unwrap()
        model.set_objective(terms=[(x, 1), (y, 1)], sense="maximize").unwrap()
        projection = model.create_projection(
            decisions=[
                ColumnDecisionSpec(id="x", block="a", variable=x),
                ColumnDecisionSpec(id="y", block="b", variable=y),
            ],
            blocks=["a", "b"],
        ).unwrap()
        projection.add_columns(
            [
                ColumnSpec(id="a0", block="a", values={"x": 0}),
                ColumnSpec(id="a1", block="a", values={"x": 1}),
                ColumnSpec(id="b0", block="b", values={"y": 0}),
                ColumnSpec(id="b1", block="b", values={"y": 1}),
            ]
        ).unwrap()
        projection.build_master().unwrap()
        attempt = projection.solve_master_lp(solver=solver).unwrap()
        assert attempt.pricing.is_ok()
        assert attempt.report.objective == pytest.approx(0.0)
        assert projection.pricing_request(block="a").is_ok()
        assert projection.pricing_request(block="b").is_ok()
    finally:
        if projection is not None:
            projection.close().unwrap()
        model.close().unwrap()
