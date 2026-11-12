"""私有 Phase I 列投影合同 / Private Phase I column-projection contracts."""

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


def setup(
    *, impossible: bool = False
) -> tuple[
    MetaModelFloat64,
    ColumnProjectionFloat64,
    _native.VariableHandle,
    _native.VariableHandle,
]:
    model = MetaModelFloat64.create("phase-one").unwrap()
    x, y = model.add_variables(
        [VariableSpec(name="x", kind="binary"), VariableSpec(name="y", kind="binary")]
    ).unwrap()
    constraints = [
        ConstraintSpec(
            name="capacity",
            terms=[(x, 1), (y, 1)],
            relation=">=" if impossible else "<=",
            rhs=3 if impossible else 1,
        )
    ]
    if not impossible:
        constraints.append(
            ConstraintSpec(name="local-y-zero", terms=[(y, 1)], relation="<=", rhs=0)
        )
    model.add_constraints(constraints).unwrap()
    model.set_objective(terms=[(x, 3), (y, 2)], sense="maximize").unwrap()
    projection = model.create_projection(
        decisions=[
            ColumnDecisionSpec(id="x", block="a", variable=x),
            ColumnDecisionSpec(id="y", block="b", variable=y),
        ],
        blocks=["a", "b"],
    ).unwrap()
    return model, projection, x, y


def test_master_phase_and_conflicting_options_preserve_current_state() -> None:
    model, projection, _, _ = setup()
    try:
        ordinary = projection.build_master().unwrap()
        assert not ordinary.integer and not ordinary.phase_one
        phase_one = projection.build_master(phase_one=True).unwrap()
        assert phase_one.phase_one and not phase_one.integer
        assert (
            phase_one.columns == 0 and phase_one.variables == 6 and phase_one.rows == 4
        )
        assert projection.master_info().unwrap() == phase_one
        assert projection.build_master(integer=True, phase_one=True).is_failed()
        assert projection.master_info().unwrap() == phase_one
        assert projection.columns().unwrap() == []
        assert model.generation().unwrap() == phase_one.source_generation
        integer = projection.build_master(integer=True).unwrap()
        assert integer.integer and not integer.phase_one
        assert phase_one.phase_one and not ordinary.phase_one
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_empty_pool_phase_one_to_integer_solution(solver: str) -> None:
    model, projection, x, y = setup()
    try:
        initial = projection.build_master(phase_one=True).unwrap()
        assert initial.phase_one and initial.columns == 0
        assert projection.pricing_request(block="a").is_failed()
        control = SolveHandle()
        assert projection.solve_master_integer(
            solver=solver, cancellation=control
        ).is_failed()
        assert control.phase == "READY"

        attempt = projection.solve_master_lp(solver=solver).unwrap()
        assert attempt.pricing.is_ok() and attempt.report.objective == pytest.approx(2)
        a = projection.pricing_request(block="a").unwrap()
        b = projection.pricing_request(block="b").unwrap()
        ca = (
            projection.solve_pricing(request=a, solver=solver)
            .unwrap()
            .candidate.unwrap()
        )
        cb = (
            projection.solve_pricing(request=b, solver=solver)
            .unwrap()
            .candidate.unwrap()
        )
        assert ca.values["x"] in (pytest.approx(0), pytest.approx(1))
        assert cb.values == {"y": pytest.approx(0)}
        assert ca.reduced_cost == pytest.approx(-1)
        assert cb.reduced_cost == pytest.approx(-1)

        assert projection.build_master(integer=True, phase_one=True).is_failed()
        assert projection.master_info().unwrap() == initial
        assert projection.pricing_info(request=a).is_ok()
        duplicate_ids = [
            (a, [ColumnSpec(id="same", block="a", values=ca.values)]),
            (b, [ColumnSpec(id="same", block="b", values=cb.values)]),
        ]
        assert projection.add_priced_batch(duplicate_ids).is_failed()
        assert projection.columns().unwrap() == []
        assert projection.master_info().unwrap() == initial
        assert projection.pricing_info(request=a).is_ok()
        projection.add_priced_batch(
            [
                (a, [ColumnSpec(id="a0", block="a", values=ca.values)]),
                (b, [ColumnSpec(id="b0", block="b", values=cb.values)]),
            ]
        ).unwrap()
        assert projection.pricing_info(request=a).is_failed()
        assert projection.master_info().is_failed()

        phase_one = projection.build_master(phase_one=True).unwrap()
        assert phase_one.phase_one and phase_one.columns == 2
        attempt = projection.solve_master_lp(solver=solver).unwrap()
        assert attempt.pricing.is_ok() and attempt.report.objective == pytest.approx(0)
        stale = projection.pricing_request(block="a").unwrap()
        ordinary = projection.build_master().unwrap()
        assert not ordinary.phase_one and not ordinary.integer
        assert projection.pricing_info(request=stale).is_failed()
        assert projection.add_priced_batch([(stale, [])]).is_failed()
        assert projection.pricing_request(block="a").is_failed()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        candidate = (
            projection.solve_pricing(request=request, solver=solver)
            .unwrap()
            .candidate.unwrap()
        )
        if candidate.reduced_cost < -1e-7:
            projection.add_priced_batch(
                [(request, [ColumnSpec(id="a1", block="a", values=candidate.values)])]
            ).unwrap()
        integer = projection.build_master(integer=True).unwrap()
        assert integer.integer and not integer.phase_one
        final = projection.solve_master_integer(solver=solver).unwrap()
        assert final.report.objective == pytest.approx(-3)
        solution = final.solution.unwrap()
        assert projection.solution_value(solution=solution, handle=x).unwrap() == (
            pytest.approx(1)
        )
        assert projection.solution_value(solution=solution, handle=y).unwrap() == (
            pytest.approx(0)
        )
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_positive_phase_one_and_repeated_vectors_are_not_completion(
    solver: str,
) -> None:
    model, projection, _, _ = setup(impossible=True)
    try:
        projection.build_master(phase_one=True).unwrap()
        first = projection.solve_master_lp(solver=solver).unwrap()
        assert first.pricing.is_ok() and first.report.objective == pytest.approx(5)
        a = projection.pricing_request(block="a").unwrap()
        b = projection.pricing_request(block="b").unwrap()
        ca = (
            projection.solve_pricing(request=a, solver=solver)
            .unwrap()
            .candidate.unwrap()
        )
        cb = (
            projection.solve_pricing(request=b, solver=solver)
            .unwrap()
            .candidate.unwrap()
        )
        assert ca.values == {"x": pytest.approx(1)}
        assert cb.values == {"y": pytest.approx(1)}
        assert ca.reduced_cost == pytest.approx(-2)
        assert cb.reduced_cost == pytest.approx(-2)
        projection.add_priced_batch(
            [
                (a, [ColumnSpec(id="a1", block="a", values=ca.values)]),
                (b, [ColumnSpec(id="b1", block="b", values=cb.values)]),
            ]
        ).unwrap()
        projection.build_master(phase_one=True).unwrap()
        current = projection.solve_master_lp(solver=solver).unwrap()
        assert current.pricing.is_ok() and current.report.objective == pytest.approx(1)
        a = projection.pricing_request(block="a").unwrap()
        b = projection.pricing_request(block="b").unwrap()
        ca = (
            projection.solve_pricing(request=a, solver=solver)
            .unwrap()
            .candidate.unwrap()
        )
        cb = (
            projection.solve_pricing(request=b, solver=solver)
            .unwrap()
            .candidate.unwrap()
        )
        assert ca.values == {"x": pytest.approx(1)}
        assert cb.values == {"y": pytest.approx(1)}
        assert projection.reduced_cost(request=a, values=ca.values).unwrap() == (
            pytest.approx(ca.reduced_cost)
        )
        assert projection.reduced_cost(request=b, values=cb.values).unwrap() == (
            pytest.approx(cb.reduced_cost)
        )
        projection.add_priced_batch(
            [
                (a, [ColumnSpec(id="duplicate-a", block="a", values=ca.values)]),
                (b, [ColumnSpec(id="duplicate-b", block="b", values=cb.values)]),
            ]
        ).unwrap()
        projection.build_master(phase_one=True).unwrap()
        repeated = projection.solve_master_lp(solver=solver).unwrap()
        assert repeated.pricing.is_ok() and repeated.report.objective == pytest.approx(
            1
        )
        projection.build_master().unwrap()
        phase_two = projection.solve_master_lp(solver=solver).unwrap()
        assert phase_two.report.problem_status == "INFEASIBLE"
        assert phase_two.pricing.is_failed()
        assert projection.pricing_request(block="a").is_failed()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_phase_one_cancellation_invalidates_prior_pricing(solver: str) -> None:
    model, projection, _, _ = setup()
    try:
        projection.build_master(phase_one=True).unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        control = SolveHandle()
        control.cancel(reason="phase-one").unwrap()
        attempt = projection.solve_master_lp(
            solver=solver, cancellation=control
        ).unwrap()
        assert attempt.report.termination_reason == "CANCELLED"
        assert control.cancellation_preceded_completion
        assert attempt.pricing.is_failed()
        assert projection.pricing_info(request=request).is_failed()
        assert projection.pricing_request(block="a").is_failed()
        assert projection.master_info().unwrap().phase_one
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_phase_roundtrip_and_source_mutation_invalidate_requests(solver: str) -> None:
    model, projection, x, y = setup()
    sibling = model.create_projection(
        decisions=[
            ColumnDecisionSpec(id="x", block="a", variable=x),
            ColumnDecisionSpec(id="y", block="b", variable=y),
        ],
        blocks=["a", "b"],
    ).unwrap()
    try:
        projection.add_columns(
            [
                ColumnSpec(id="a0", block="a", values={"x": 0}),
                ColumnSpec(id="b0", block="b", values={"y": 0}),
            ]
        ).unwrap()
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        ordinary = projection.pricing_request(block="a").unwrap()
        projection.build_master(phase_one=True).unwrap()
        assert projection.pricing_info(request=ordinary).is_failed()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        phase_one = projection.pricing_request(block="a").unwrap()
        sibling.build_master(phase_one=True).unwrap()
        sibling.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        foreign = sibling.pricing_request(block="a").unwrap()
        before = projection.master_info().unwrap()
        assert projection.pricing_info(request=foreign).is_failed()
        assert projection.add_priced_batch([(foreign, [])]).is_failed()
        assert projection.master_info().unwrap() == before
        assert projection.pricing_info(request=phase_one).is_ok()
        model.add_variables([VariableSpec(name="fixed", lower=0, upper=0)]).unwrap()
        assert projection.master_info().is_failed()
        assert projection.pricing_info(request=phase_one).is_failed()
        assert sibling.pricing_info(request=foreign).is_failed()
        rebuilt = projection.build_master(phase_one=True).unwrap()
        assert (
            rebuilt.phase_one
            and rebuilt.source_generation == before.source_generation + 1
        )
        assert projection.pricing_request(block="a").is_failed()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        assert projection.pricing_info(request=phase_one).is_failed()
    finally:
        sibling.close().unwrap()
        projection.close().unwrap()
        model.close().unwrap()


def test_phase_one_progress_cancellation_and_reentry(solver: str) -> None:
    model, projection, _, _ = setup()
    control = SolveHandle()
    events: list[SolveProgress] = []
    errors: list[ErrorCode] = []
    try:
        projection.build_master(phase_one=True).unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()

        def callback(event: SolveProgress) -> None:
            if not events:
                nested = projection.build_master(phase_one=True)
                assert isinstance(nested, Failed)
                errors.append(nested.error.code)
            events.append(event)
            if not event.terminal and not control.is_cancelled:
                control.cancel(reason="phase-one progress").unwrap()

        attempt = projection.solve_master_lp(
            solver=solver, cancellation=control, on_progress=callback
        ).unwrap()
        assert events and errors == [ErrorCode.FAILED_PRECONDITION]
        assert control.cancellation_preceded_completion
        assert attempt.pricing.is_failed()
        assert projection.pricing_info(request=request).is_failed()
        assert projection.master_info().unwrap().phase_one
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_phase_one_callback_failure_preserves_result_and_invalidates_prices(
    solver: str,
) -> None:
    model, projection, _, _ = setup()
    try:
        projection.build_master(phase_one=True).unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        failure: BindingResult[None] = invalid("回调失败 / Callback failure")
        seen: list[ErrorCode] = []

        def callback(event: SolveProgress) -> BindingResult[None]:
            result = projection.pricing_info(request=request)
            assert isinstance(result, Failed)
            seen.append(result.error.code)
            return failure

        result = projection.solve_master_lp(solver=solver, on_progress=callback)
        assert isinstance(result, Failed)
        assert result.error.value.callback_result is failure
        assert seen == [ErrorCode.FAILED_PRECONDITION]
        assert projection.pricing_info(request=request).is_failed()
        assert projection.pricing_request(block="a").is_failed()
    finally:
        projection.close().unwrap()
        model.close().unwrap()
