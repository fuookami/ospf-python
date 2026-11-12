"""单次定价的后端界快照合同 / Per-pricing backend-bound observation contracts."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.control import SolveHandle, SolveProgress
from ospf_python._binding.model import (
    ColumnDecisionSpec,
    ColumnProjectionFloat64,
    ColumnSpec,
    MetaModelFloat64,
    VariableSpec,
)


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def setup(
    *, seed: int
) -> tuple[MetaModelFloat64, ColumnProjectionFloat64, _native.VariableHandle]:
    model = MetaModelFloat64.create("pricing-bound").unwrap()
    x = model.add_variables([VariableSpec(name="x", kind="binary")]).unwrap()[0]
    model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
    projection = model.create_projection(
        decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)], blocks=["a"]
    ).unwrap()
    projection.add_columns(
        [
            ColumnSpec(id="seed", block="a", values={"x": seed}),
            ColumnSpec(id="copy", block="a", values={"x": seed}),
        ]
    ).unwrap()
    return model, projection, x


def test_bound_observation_is_not_constructible() -> None:
    with pytest.raises(TypeError):
        _native.ColumnPricingBound()


@pytest.mark.parametrize("seed", [0, 1])
def test_real_backend_bound_is_scoped_and_separate_from_candidate(
    solver: str, seed: int
) -> None:
    model, projection, _ = setup(seed=seed)
    try:
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        attempt = projection.solve_pricing(request=request, solver=solver).unwrap()
        assert attempt.candidate.unwrap().reduced_cost == pytest.approx(-3 * (1 - seed))
        bound = attempt.bound.unwrap()
        info = projection.pricing_bound_info(bound=bound).unwrap()
        assert info.block == "a"
        assert info.reported_cx_lower == pytest.approx(-3)
        assert info.convexity_price == pytest.approx(-3 * seed)
        assert info.reported_nonnegative is (seed == 1)
        assert projection.pricing_bound_info(bound=attempt.report).is_failed()  # type: ignore[arg-type]
        assert projection.pricing_info(request=request).is_ok()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


@pytest.mark.parametrize(
    "change", ["resolve", "rebuild", "add", "remove", "source", "close"]
)
def test_bound_observation_expires_with_its_pricing_request(
    solver: str, change: str
) -> None:
    model, projection, x = setup(seed=1)
    try:
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        bound = (
            projection.solve_pricing(request=request, solver=solver)
            .unwrap()
            .bound.unwrap()
        )
        snapshot = projection.pricing_bound_info(bound=bound).unwrap()
        if change == "resolve":
            projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        elif change == "rebuild":
            projection.build_master().unwrap()
        elif change == "add":
            projection.add_columns(
                [ColumnSpec(id="another", block="a", values={"x": 1})]
            ).unwrap()
        elif change == "remove":
            projection.remove_columns(["seed"]).unwrap()
        elif change == "source":
            model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
        else:
            projection.close().unwrap()
        assert projection.pricing_bound_info(bound=bound).is_failed()
        assert (
            snapshot.reported_nonnegative
            and snapshot.convexity_price == pytest.approx(-3)
        )
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_bound_rejects_another_projection_and_cancelled_attempt(solver: str) -> None:
    model, first, x = setup(seed=1)
    other = model.create_projection(
        decisions=[ColumnDecisionSpec(id="x", block="a", variable=x)], blocks=["a"]
    ).unwrap()
    try:
        other.add_columns([ColumnSpec(id="seed", block="a", values={"x": 1})]).unwrap()
        for projection in (first, other):
            projection.build_master().unwrap()
            projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = first.pricing_request(block="a").unwrap()
        bound = (
            first.solve_pricing(request=request, solver=solver).unwrap().bound.unwrap()
        )
        assert other.pricing_bound_info(bound=bound).is_failed()
        control = SolveHandle()
        control.cancel().unwrap()
        cancelled = first.solve_pricing(
            request=request, solver=solver, cancellation=control
        ).unwrap()
        assert cancelled.report.termination_reason == "CANCELLED"
        assert cancelled.bound.is_failed() and cancelled.candidate.is_failed()
        assert first.pricing_bound_info(bound=bound).is_ok()
    finally:
        first.close().unwrap()
        other.close().unwrap()
        model.close().unwrap()


def test_noop_and_failed_batch_leave_bound_current(solver: str) -> None:
    model, projection, _ = setup(seed=1)
    try:
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        bound = (
            projection.solve_pricing(request=request, solver=solver)
            .unwrap()
            .bound.unwrap()
        )
        before = projection.columns().unwrap()
        assert projection.add_priced_batch(
            [(request, [ColumnSpec(id="seed", block="a", values={"x": 1})])]
        ).is_failed()
        assert projection.columns().unwrap() == before
        projection.add_priced_batch([(request, [])]).unwrap()
        assert projection.pricing_bound_info(bound=bound).is_ok()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


@pytest.mark.parametrize("late", [False, True])
def test_cancellation_order_controls_bound_observation(solver: str, late: bool) -> None:
    model, projection, _ = setup(seed=1)
    control = SolveHandle()

    def cancel(event: SolveProgress) -> None:
        if event.terminal is late and not control.is_cancelled:
            control.cancel(reason="pricing progress").unwrap()

    try:
        projection.build_master().unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        attempt = projection.solve_pricing(
            request=request, solver=solver, cancellation=control, on_progress=cancel
        ).unwrap()
        assert control.is_cancelled
        assert control.cancellation_preceded_completion is not late
        if late:
            assert projection.pricing_bound_info(bound=attempt.bound.unwrap()).is_ok()
        else:
            assert attempt.bound.is_failed()
    finally:
        projection.close().unwrap()
        model.close().unwrap()


def test_phase_one_bound_does_not_imply_source_feasibility(solver: str) -> None:
    model, projection, _ = setup(seed=0)
    try:
        projection.build_master(phase_one=True).unwrap()
        projection.solve_master_lp(solver=solver).unwrap().pricing.unwrap()
        request = projection.pricing_request(block="a").unwrap()
        bound = (
            projection.solve_pricing(request=request, solver=solver)
            .unwrap()
            .bound.unwrap()
        )
        info = projection.pricing_bound_info(bound=bound).unwrap()
        assert info.reported_cx_lower == pytest.approx(0)
        assert info.convexity_price == pytest.approx(0)
        assert info.reported_nonnegative
    finally:
        projection.close().unwrap()
        model.close().unwrap()
