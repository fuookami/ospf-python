"""真实后端的保守精确门禁 / Conservative exact gate with real backends."""

from __future__ import annotations

import json

import pytest

from ospf_python import _native
from ospf_python._binding.model import (
    ColumnDecisionSpec,
    ColumnSpec,
    ConstraintSpec,
    MetaModelFloat64,
    VariableSpec,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def test_unrepresentable_primal_keeps_both_reports_but_issues_no_prices(
    solver: str,
) -> None:
    model = MetaModelFloat64.create("unrepresentable third").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=1)]).unwrap()[0]
        model.add_constraints(
            [ConstraintSpec(name="third", terms=[(x, 3)], relation="==", rhs=1)]
        ).unwrap()
        model.set_objective(terms=[(x, 1)], sense="minimize").unwrap()
        attempt = model.solve_compiled(solver=solver).unwrap()
        assert attempt.report.termination_reason == "COMPLETED"
        assert json.loads(attempt.report.raw_json)["solution"]["values"]
        assert isinstance(attempt.certificate, Failed)
        assert attempt.certificate.error.code is ErrorCode.FAILED_PRECONDITION

        projection = model.create_projection(decisions=[], blocks=["a"]).unwrap()
        try:
            projection.add_columns(
                [ColumnSpec(id="empty", block="a", values={})]
            ).unwrap()
            projection.build_master().unwrap()
            master = projection.solve_master_lp(solver=solver).unwrap()
            assert master.report.termination_reason == "COMPLETED"
            assert json.loads(master.report.raw_json)["solution"]["values"]
            assert isinstance(master.pricing, Failed)
            assert master.pricing.error.code is ErrorCode.FAILED_PRECONDITION
            assert projection.pricing_request(block="a").is_failed()
        finally:
            projection.close().unwrap()
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("kind", ["row", "objective"])
def test_rounded_master_column_keeps_report_but_rejects_pricing(
    solver: str, kind: str
) -> None:
    model = MetaModelFloat64.create("rounded column").unwrap()
    variables = model.add_variables(
        [VariableSpec(name=name, kind="binary") for name in ("x", "y", "z")]
    ).unwrap()
    terms = list(zip(variables, [1e16, 1.0, -1e16], strict=True))
    if kind == "row":
        model.add_constraints(
            [ConstraintSpec(name="row", terms=terms, relation="<=", rhs=1)]
        ).unwrap()
        model.set_objective(terms=[], sense="minimize").unwrap()
    else:
        model.set_objective(terms=terms, sense="minimize").unwrap()
    projection = model.create_projection(
        decisions=[
            ColumnDecisionSpec(id=name, block="a", variable=variable)
            for name, variable in zip(("x", "y", "z"), variables, strict=True)
        ],
        blocks=["a"],
    ).unwrap()
    try:
        projection.add_columns(
            [ColumnSpec(id="one", block="a", values={"x": 1, "y": 1, "z": 1})]
        ).unwrap()
        projection.build_master().unwrap()
        attempt = projection.solve_master_lp(solver=solver).unwrap()
        assert attempt.report.termination_reason == "COMPLETED"
        assert json.loads(attempt.report.raw_json)["solution"]["values"]
        assert isinstance(attempt.pricing, Failed)
        assert attempt.pricing.error.code is ErrorCode.FAILED_PRECONDITION
        assert projection.pricing_request(block="a").is_failed()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_reduced_cost_retains_cancelled_sign(solver: str) -> None:
    model = MetaModelFloat64.create("reduced-cost cancellation").unwrap()
    variables = model.add_variables(
        [VariableSpec(name=name, kind="binary") for name in ("x", "y", "z")]
    ).unwrap()
    model.set_objective(
        terms=list(zip(variables, [1e16, -1.0, -1e16], strict=True)), sense="minimize"
    ).unwrap()
    projection = model.create_projection(
        decisions=[
            ColumnDecisionSpec(id=name, block="a", variable=variable)
            for name, variable in zip(("x", "y", "z"), variables, strict=True)
        ],
        blocks=["a"],
    ).unwrap()
    try:
        projection.add_columns(
            [ColumnSpec(id="zero", block="a", values={"x": 0, "y": 0, "z": 0})]
        ).unwrap()
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        assert (
            projection.reduced_cost(
                request=request, values={"x": 1, "y": 1, "z": 1}
            ).unwrap()
            == -1.0
        )
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_unrepresentable_cost_rejects_priced_batch_atomically(solver: str) -> None:
    model = MetaModelFloat64.create("reduced-cost underflow").unwrap()
    x = model.add_variables([VariableSpec(name="x", lower=0, upper=1)]).unwrap()[0]
    model.set_objective(
        terms=[(x, float.fromhex("0x0.0000000000001p-1022"))], sense="minimize"
    ).unwrap()
    projection = model.create_projection(
        decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)], blocks=["a"]
    ).unwrap()
    try:
        projection.add_columns(
            [ColumnSpec(id="zero", block="a", values={"x": 0})]
        ).unwrap()
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        before = projection.columns().unwrap()
        assert projection.reduced_cost(request=request, values={"x": 0.5}).is_failed()
        assert projection.add_priced_batch(
            [
                (
                    request,
                    [
                        ColumnSpec(id="one", block="a", values={"x": 1}),
                        ColumnSpec(id="half", block="a", values={"x": 0.5}),
                    ],
                )
            ]
        ).is_failed()
        assert projection.columns().unwrap() == before
        assert projection.pricing_info(request=request).is_ok()
    finally:
        projection.close().unwrap()
        model.close().unwrap()
