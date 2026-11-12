"""私有列生成闭环合同 / Private column-generation cycle contracts."""

from __future__ import annotations

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


def setup() -> tuple[
    MetaModelFloat64,
    ColumnProjectionFloat64,
    _native.VariableHandle,
    _native.VariableHandle,
]:
    model = MetaModelFloat64.create("two-block-cycle").unwrap()
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
    projection.add_columns(
        [
            ColumnSpec(id="a0", block="a", values={"x": 0}),
            ColumnSpec(id="b0", block="b", values={"y": 0}),
        ]
    ).unwrap()
    projection.build_master().unwrap()
    return model, projection, x, y


def test_final_solution_is_not_constructible() -> None:
    with pytest.raises(TypeError):
        _native.ColumnProjectionSolution()


def test_two_block_real_cycle_and_atomic_batch(solver: str) -> None:
    model, projection, x, y = setup()
    try:
        assert projection.solve_master_lp(solver=solver).unwrap().pricing.is_ok()
        a = projection.pricing_request(block="a").unwrap()
        b = projection.pricing_request(block="b").unwrap()
        priced_a = projection.solve_pricing(request=a, solver=solver).unwrap()
        priced_b = projection.solve_pricing(request=b, solver=solver).unwrap()
        ca, cb = priced_a.candidate.unwrap(), priced_b.candidate.unwrap()
        assert ca.values == {"x": pytest.approx(1)}
        assert cb.values == {"y": pytest.approx(1)}
        assert ca.reduced_cost == pytest.approx(-3)
        assert cb.reduced_cost == pytest.approx(-2)
        assert priced_a.report.solution_presence == "OPTIMAL"
        assert priced_b.report.solution_presence == "OPTIMAL"
        columns = projection.columns().unwrap()
        master = projection.master_info().unwrap()

        duplicate = [
            (a, [ColumnSpec(id="same", block="a", values=ca.values)]),
            (b, [ColumnSpec(id="same", block="b", values=cb.values)]),
        ]
        assert projection.add_priced_batch(duplicate).is_failed()
        assert projection.columns().unwrap() == columns
        assert projection.master_info().unwrap() == master
        assert projection.pricing_info(request=a).is_ok()
        assert projection.add_priced_batch(
            [(a, [ColumnSpec(id="wrong", block="b", values={"y": 1})])]
        ).is_failed()
        assert projection.add_priced_batch(
            [(a, [ColumnSpec(id="fractional", block="a", values={"x": 0.5})])]
        ).is_failed()
        assert projection.add_priced_batch([(a, [])]).is_ok()
        assert projection.master_info().unwrap() == master
        assert projection.pricing_info(request=a).is_ok()

        projection.add_priced_batch(
            [
                (a, [ColumnSpec(id="a1", block="a", values=ca.values)]),
                (b, [ColumnSpec(id="b1", block="b", values=cb.values)]),
            ]
        ).unwrap()
        assert projection.pricing_info(request=a).is_failed()
        assert projection.master_info().is_failed()
        projection.build_master().unwrap()
        lp = projection.solve_master_lp(solver=solver).unwrap()
        assert lp.pricing.is_ok() and lp.report.objective == pytest.approx(-3)

        projection.build_master(integer=True).unwrap()
        final = projection.solve_master_integer(solver=solver).unwrap()
        solution = final.solution.unwrap()
        assert final.report.solution_presence == "OPTIMAL"
        assert final.report.objective == pytest.approx(-3)
        assert projection.solution_value(solution=solution, handle=x).unwrap() == (
            pytest.approx(1)
        )
        assert projection.solution_value(solution=solution, handle=y).unwrap() == (
            pytest.approx(0)
        )
        assert projection.solution_value(solution=final.report, handle=x).is_failed()  # type: ignore[arg-type]
        projection.remove_columns(["a1"]).unwrap()
        assert projection.solution_value(solution=solution, handle=x).is_failed()
        projection.build_master().unwrap()
        assert projection.solve_master_lp(solver=solver).unwrap().report.objective == (
            pytest.approx(-2)
        )
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_real_pricing_counts_nonzero_convexity_constant(solver: str) -> None:
    model = MetaModelFloat64.create("pricing-constant").unwrap()
    x = model.add_variables([VariableSpec(name="x", kind="binary")]).unwrap()[0]
    model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
    projection = model.create_projection(
        decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)], blocks=["a"]
    ).unwrap()
    try:
        projection.add_columns(
            [
                ColumnSpec(id="first", block="a", values={"x": 1}),
                ColumnSpec(id="second", block="a", values={"x": 1}),
            ]
        ).unwrap()
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        assert projection.pricing_info(request=request).unwrap().convexity_price == (
            pytest.approx(-3)
        )
        priced = projection.solve_pricing(request=request, solver=solver).unwrap()
        candidate = priced.candidate.unwrap()
        assert priced.report.objective == pytest.approx(-3)
        assert candidate.values == {"x": pytest.approx(1)}
        assert candidate.reduced_cost == pytest.approx(0)
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_pricing_rechecks_local_rows_and_decision_identity(solver: str) -> None:
    model = MetaModelFloat64.create("local-pricing").unwrap()
    x, y = model.add_variables(
        [VariableSpec(name="x", kind="binary"), VariableSpec(name="y", kind="binary")]
    ).unwrap()
    model.add_constraints(
        [ConstraintSpec(name="local", terms=[(x, 1), (y, 1)], relation="<=", rhs=1)]
    ).unwrap()
    model.set_objective(terms=[(x, 3), (y, 2)], sense="maximize").unwrap()
    projection = model.create_projection(
        decisions=[
            ColumnDecisionSpec(id="z", block="a", variable=y),
            ColumnDecisionSpec(id="a", block="a", variable=x),
        ],
        blocks=["a"],
    ).unwrap()
    try:
        projection.add_columns(
            [ColumnSpec(id="zero", block="a", values={"a": 0, "z": 0})]
        ).unwrap()
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        priced = projection.solve_pricing(request=request, solver=solver).unwrap()
        candidate = priced.candidate.unwrap()
        assert candidate.values == {"a": pytest.approx(1), "z": pytest.approx(0)}
        assert candidate.reduced_cost == pytest.approx(-3)
        assert projection.add_priced_batch(
            [(request, [ColumnSpec(id="bad", block="a", values={"a": 1, "z": 1})])]
        ).is_failed()
        assert projection.pricing_info(request=request).is_ok()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_integer_solution_includes_unmapped_global_source_variables(
    solver: str,
) -> None:
    model = MetaModelFloat64.create("global-variable").unwrap()
    x, global_var = model.add_variables(
        [
            VariableSpec(name="x", kind="binary"),
            VariableSpec(name="global", kind="integer", lower=0, upper=2),
        ]
    ).unwrap()
    model.add_constraints(
        [
            ConstraintSpec(
                name="capacity", terms=[(x, 1), (global_var, 1)], relation="<=", rhs=2
            )
        ]
    ).unwrap()
    model.set_objective(terms=[(x, 3), (global_var, 2)], sense="maximize").unwrap()
    projection = model.create_projection(
        decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)], blocks=["a"]
    ).unwrap()
    try:
        projection.add_columns(
            [
                ColumnSpec(id="zero", block="a", values={"x": 0}),
                ColumnSpec(id="one", block="a", values={"x": 1}),
            ]
        ).unwrap()
        projection.build_master(integer=True).unwrap()
        final = projection.solve_master_integer(solver=solver).unwrap()
        solution = final.solution.unwrap()
        assert final.report.objective == pytest.approx(-5)
        assert projection.solution_value(solution=solution, handle=x).unwrap() == (
            pytest.approx(1)
        )
        assert projection.solution_value(
            solution=solution, handle=global_var
        ).unwrap() == (pytest.approx(1))
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_foreign_and_stale_capabilities_cannot_mutate_or_extract(solver: str) -> None:
    model, first, x, _ = setup()
    foreign_model, other, foreign_x, _ = setup()
    sibling = model.create_projection(decisions=[], blocks=["other"]).unwrap()
    sibling.add_columns([ColumnSpec(id="empty", block="other", values={})]).unwrap()
    sibling.build_master(integer=True).unwrap()
    try:
        first.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        other.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        a = first.pricing_request(block="a").unwrap()
        foreign = other.pricing_request(block="a").unwrap()
        before = first.columns().unwrap()
        assert first.solve_pricing(request=foreign, solver=solver).is_failed()
        assert first.add_priced_batch(
            [(a, [ColumnSpec(id="a1", block="a", values={"x": 1})]), (foreign, [])]
        ).is_failed()
        assert first.columns().unwrap() == before
        assert first.pricing_info(request=a).is_ok()
        first.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        control = SolveHandle()
        assert first.solve_pricing(
            request=a, solver=solver, cancellation=control
        ).is_failed()
        assert control.phase == "READY"
        assert first.add_priced_batch([(a, [])]).is_failed()

        first.build_master(integer=True).unwrap()
        solution = first.solve_master_integer(solver=solver).unwrap().solution.unwrap()
        assert first.solution_value(solution=solution, handle=foreign_x).is_failed()
        assert other.solution_value(solution=solution, handle=foreign_x).is_failed()
        assert sibling.solution_value(solution=solution, handle=x).is_failed()
        assert first.solution_value(
            solution=solution, handle=x
        ).unwrap() == pytest.approx(0)
        extra = model.add_variables(
            [VariableSpec(name="extra", lower=0, upper=0)]
        ).unwrap()[0]
        model.set_bounds(handle=extra, lower=0, upper=1).unwrap()
        model.set_bounds(handle=extra, lower=0, upper=0).unwrap()
        assert first.solution_value(solution=solution, handle=x).is_failed()
        first.build_master(integer=True).unwrap()
        assert first.solution_value(solution=solution, handle=x).is_failed()
    finally:
        first.close().unwrap()
        other.close().unwrap()
        sibling.close().unwrap()
        model.close().unwrap()
        foreign_model.close().unwrap()


def test_cancelled_pricing_retains_report_and_current_request(solver: str) -> None:
    model, projection, _, _ = setup()
    try:
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        control = SolveHandle()
        control.cancel().unwrap()
        attempt = projection.solve_pricing(
            request=request, solver=solver, cancellation=control
        ).unwrap()
        assert attempt.report.termination_reason == "CANCELLED"
        assert attempt.candidate.is_failed()
        assert projection.pricing_info(request=request).is_ok()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


@pytest.mark.parametrize("case", ["infeasible", "cancelled"])
def test_integer_master_preserves_terminal_report_without_source_solution(
    solver: str, case: str
) -> None:
    model, projection, x, y = setup()
    control = SolveHandle()
    try:
        if case == "infeasible":
            model.add_constraints(
                [
                    ConstraintSpec(
                        name="impossible", terms=[(x, 1), (y, 1)], relation="<=", rhs=-1
                    )
                ]
            ).unwrap()
        else:
            control.cancel().unwrap()
        projection.build_master(integer=True).unwrap()
        attempt = projection.solve_master_integer(
            solver=solver, cancellation=control
        ).unwrap()
        assert attempt.solution.is_failed()
        if case == "infeasible":
            assert attempt.report.problem_status == "INFEASIBLE"
        else:
            assert attempt.report.termination_reason == "CANCELLED"
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_invalid_tolerance_or_continuous_master_does_not_consume_handle(
    solver: str,
) -> None:
    model, projection, _, _ = setup()
    try:
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        for tolerance in (-1, 0.5, float("nan"), float("inf"), True):
            control = SolveHandle()
            assert projection.solve_pricing(
                request=request,
                solver=solver,
                tolerance=tolerance,
                cancellation=control,
            ).is_failed()
            assert control.phase == "READY"
            assert projection.pricing_info(request=request).is_ok()
        control = SolveHandle()
        assert projection.solve_master_integer(
            solver=solver, cancellation=control
        ).is_failed()
        assert control.phase == "READY"
        projection.build_master(integer=True).unwrap()
        for tolerance in (-1, 0.5, float("nan"), float("inf"), True):
            control = SolveHandle()
            assert projection.solve_master_integer(
                solver=solver, tolerance=tolerance, cancellation=control
            ).is_failed()
            assert control.phase == "READY"
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_pricing_callback_reentry_and_failure_preserve_context(solver: str) -> None:
    model, projection, _, _ = setup()
    try:
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        failure: BindingResult[None] = invalid("回调失败 / Callback failure")
        seen: list[ErrorCode] = []

        def callback(event: SolveProgress) -> BindingResult[None]:
            result = projection.pricing_info(request=request)
            assert isinstance(result, Failed)
            seen.append(result.error.code)
            return failure

        result = projection.solve_pricing(
            request=request, solver=solver, on_progress=callback
        )
        assert isinstance(result, Failed)
        assert seen == [ErrorCode.FAILED_PRECONDITION]
        assert result.error.value.callback_result is failure
        assert projection.pricing_info(request=request).is_ok()
    finally:
        projection.close().unwrap()
        model.close().unwrap()
