"""私有主 LP 与定价凭据合同 / Private master LP and pricing-capability contracts."""

from __future__ import annotations

import gc

import pytest

from ospf_python import _native
from ospf_python._binding.control import SolveHandle, SolveProgress
from ospf_python._binding.model import (
    ColumnDecisionSpec,
    ColumnProjectionFloat64,
    ColumnSpec,
    ConstraintSpec,
    MetaModelFloat64,
    VariableSpec,
)
from ospf_python._binding.result import BindingResult, invalid
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def setup(*, capacity: int = 1) -> tuple[MetaModelFloat64, ColumnProjectionFloat64]:
    model = MetaModelFloat64.create("pricing").unwrap()
    x, y = model.add_variables(
        [VariableSpec(name="x", kind="binary"), VariableSpec(name="y", kind="binary")]
    ).unwrap()
    model.add_constraints(
        [
            ConstraintSpec(
                name="capacity", terms=[(x, 1), (y, 1)], relation="<=", rhs=capacity
            )
        ]
    ).unwrap()
    model.set_objective(terms=[(x, 3), (y, 2)], sense="maximize").unwrap()
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
            ColumnSpec(id="b0", block="b", values={"y": 0}),
        ]
    ).unwrap()
    projection.build_master().unwrap()
    return model, projection


def test_pricing_request_is_not_constructible() -> None:
    with pytest.raises(TypeError):
        _native.ColumnPricingRequest()


def test_master_solve_issues_current_pricing_without_mutable_python_model(
    solver: str,
) -> None:
    model, projection = setup()
    try:
        assert projection.pricing_request(block="a").is_failed()
        attempt = projection.solve_master_lp(solver=solver).unwrap()
        assert attempt.pricing.is_ok()
        assert attempt.report.model_identity != model.model_identity
        assert attempt.report.model_generation == model.generation().unwrap()
        assert attempt.report.termination_reason == "COMPLETED"
        assert attempt.report.objective == pytest.approx(0)

        a = projection.pricing_request(block="a").unwrap()
        b = projection.pricing_request(block="b").unwrap()
        info = projection.pricing_info(request=a).unwrap()
        assert info.block == "a"
        assert info.coefficients == {"x": pytest.approx(-3)}
        assert projection.reduced_cost(request=a, values={"x": 1}).unwrap() == (
            pytest.approx(-3)
        )
        assert projection.reduced_cost(request=b, values={"y": 1}).unwrap() == (
            pytest.approx(-2)
        )
        info.coefficients["x"] = 999
        assert projection.reduced_cost(request=a, values={"x": 1}).unwrap() == (
            pytest.approx(-3)
        )
        for invalid in ({}, {"x": 1, "y": 0}, {"x": float("nan")}, {"x": 2**53}):
            assert projection.reduced_cost(request=a, values=invalid).is_failed()
        assert projection.pricing_request(block="missing").is_failed()
        assert set(vars(projection)) == {"_handle"}
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_reduced_cost_includes_nonzero_convexity_constant(solver: str) -> None:
    model = MetaModelFloat64.create("convexity-price").unwrap()
    x = model.add_variables([VariableSpec(name="x", kind="binary")]).unwrap()[0]
    model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
    projection = model.create_projection(
        decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)], blocks=["a"]
    ).unwrap()
    try:
        projection.add_columns(
            [
                ColumnSpec(id="one", block="a", values={"x": 1}),
                ColumnSpec(id="duplicate-value", block="a", values={"x": 1}),
            ]
        ).unwrap()
        projection.build_master().unwrap()
        attempt = projection.solve_master_lp(solver=solver).unwrap()
        assert attempt.pricing.is_ok()
        assert attempt.report.objective == pytest.approx(-3)
        request = projection.pricing_request(block="a").unwrap()
        info = projection.pricing_info(request=request).unwrap()
        assert info.coefficients == {"x": pytest.approx(-3)}
        assert info.convexity_price == pytest.approx(-3)
        assert projection.reduced_cost(request=request, values={"x": 0}).unwrap() == (
            pytest.approx(3)
        )
        assert projection.reduced_cost(request=request, values={"x": 1}).unwrap() == (
            pytest.approx(0)
        )
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_request_provenance_and_price_epochs(solver: str) -> None:
    model, first = setup()
    other_model, other = setup()
    second = model.create_projection(decisions=[], blocks=["c"]).unwrap()
    second.add_columns([ColumnSpec(id="c0", block="c", values={})]).unwrap()
    second.build_master().unwrap()
    try:
        first.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = first.pricing_request(block="a").unwrap()
        assert second.pricing_info(request=request).is_failed()
        assert other.pricing_info(request=request).is_failed()
        assert first.pricing_info(request=object()).is_failed()  # type: ignore[arg-type]

        first.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        assert first.pricing_info(request=request).is_failed()
        request = first.pricing_request(block="a").unwrap()
        failure = first.solve_master_lp(solver="not-a-solver")
        assert isinstance(failure, Failed)
        assert failure.error.code is ErrorCode.NOT_SUPPORTED
        assert first.pricing_info(request=request).is_failed()
        assert first.pricing_request(block="a").is_failed()

        first.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = first.pricing_request(block="a").unwrap()
        first.build_master().unwrap()
        assert first.pricing_info(request=request).is_failed()
        first.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = first.pricing_request(block="a").unwrap()
        extra = model.add_variables(
            [VariableSpec(name="extra", lower=0, upper=0)]
        ).unwrap()[0]
        model.set_bounds(handle=extra, lower=0, upper=1).unwrap()
        model.set_bounds(handle=extra, lower=0, upper=0).unwrap()
        assert first.pricing_info(request=request).is_failed()
        assert first.solve_master_lp(solver=solver).is_failed()
        first.build_master().unwrap()
        first.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        assert first.pricing_info(request=request).is_failed()
        request = first.pricing_request(block="a").unwrap()
        first.close().unwrap()
        assert first.pricing_info(request=request).is_failed()
        del first
        gc.collect()
        assert second.pricing_info(request=request).is_failed()
    finally:
        second.close().unwrap()
        other.close().unwrap()
        model.close().unwrap()
        other_model.close().unwrap()


@pytest.mark.parametrize("case", ["cancelled", "infeasible"])
def test_uncertified_report_is_preserved_and_does_not_issue_pricing(
    solver: str, case: str
) -> None:
    model, projection = setup(capacity=-1 if case == "infeasible" else 1)
    control = SolveHandle()
    if case == "cancelled":
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        old_request = projection.pricing_request(block="a").unwrap()
        control.cancel().unwrap()
    try:
        attempt = projection.solve_master_lp(
            solver=solver, cancellation=control
        ).unwrap()
        assert attempt.pricing.is_failed()
        if case == "cancelled":
            assert attempt.report.termination_reason == "CANCELLED"
            assert control.cancellation_preceded_completion
            assert projection.pricing_info(request=old_request).is_failed()
        else:
            assert attempt.report.problem_status == "INFEASIBLE"
        assert projection.pricing_request(block="a").is_failed()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_master_progress_can_cancel_without_issuing_pricing(solver: str) -> None:
    model, projection = setup()
    control = SolveHandle()
    nested_control = SolveHandle()
    events: list[SolveProgress] = []
    reentry_errors: list[ErrorCode] = []
    projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
    request = projection.pricing_request(block="a").unwrap()

    def cancel(event: SolveProgress) -> None:
        if not events:
            for result in (
                projection.pricing_info(request=request),
                projection.build_master(),
                projection.close(),
                model.close(),
                model.solve(solver=solver, cancellation=nested_control),
            ):
                assert isinstance(result, Failed)
                reentry_errors.append(result.error.code)
        events.append(event)
        if not event.terminal and not control.is_cancelled:
            control.cancel(reason="master progress").unwrap()

    try:
        attempt = projection.solve_master_lp(
            solver=solver, cancellation=control, on_progress=cancel
        ).unwrap()
        assert events
        assert all(
            event.model_identity == attempt.report.model_identity for event in events
        )
        assert reentry_errors == [ErrorCode.FAILED_PRECONDITION] * 5
        assert nested_control.phase == "READY"
        assert control.cancellation_preceded_completion
        assert attempt.pricing.is_failed()
        assert projection.pricing_info(request=request).is_failed()
        assert projection.pricing_request(block="a").is_failed()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_scip_unsupported_master_time_limit_invalidates_old_prices(solver: str) -> None:
    if solver != "scip":
        pytest.skip("SCIP compiled-model time-limit gate")
    model, projection = setup()
    try:
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        control = SolveHandle()
        result = projection.solve_master_lp(
            solver=solver, time_limit=1, cancellation=control
        )
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.NOT_SUPPORTED
        assert control.phase == "READY"
        assert projection.pricing_info(request=request).is_failed()
        assert projection.pricing_request(block="a").is_failed()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_master_callback_failure_preserves_result_and_invalidates_pricing(
    solver: str,
) -> None:
    model, projection = setup()
    projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
    request = projection.pricing_request(block="a").unwrap()
    seen: list[object] = []
    failed: BindingResult[None] = invalid("回调失败 / Callback failure")

    def callback(event: SolveProgress) -> BindingResult[None]:
        seen.append(event)
        assert projection.pricing_info(request=request).is_failed()
        return failed

    try:
        result = projection.solve_master_lp(solver=solver, on_progress=callback)
        assert seen
        assert isinstance(result, Failed)
        assert result.error.value.callback_result is failed
        assert projection.pricing_info(request=request).is_failed()
        assert projection.pricing_request(block="a").is_failed()
    finally:
        projection.close().unwrap()
        model.close().unwrap()
