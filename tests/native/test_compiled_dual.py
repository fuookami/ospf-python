"""私有同次编译与对偶证书合同 / Private same-compilation and dual-certificate contracts."""

from __future__ import annotations

import json
import random

import pytest

from ospf_python import _native
from ospf_python._binding.control import SolveHandle, SolveProgress
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def create_model(*, sense: str = "maximize", relation: str = "<=") -> MetaModelFloat64:
    model = MetaModelFloat64.create("certified").unwrap()
    x = model.add_variables([VariableSpec(name="x", lower=0)]).unwrap()[0]
    model.add_constraints(
        [ConstraintSpec(name="row", terms=[(x, 1)], relation=relation, rhs=2)]
    ).unwrap()
    model.set_objective(terms=[(x, 3)], sense=sense).unwrap()
    return model


def test_certificate_has_no_python_constructor() -> None:
    with pytest.raises(TypeError):
        _native.DualCertificate()


@pytest.mark.parametrize(
    ("sense", "relation", "coefficient"),
    [
        ("maximize", "<=", 3),
        ("minimize", ">=", 3),
        ("maximize", "==", 3),
        ("minimize", "==", 3),
        ("maximize", ">=", -3),
        ("minimize", "<=", -3),
    ],
)
def test_source_price_uses_same_compilation_and_original_direction(
    solver: str, sense: str, relation: str, coefficient: int
) -> None:
    model = MetaModelFloat64.create("source-price").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0)]).unwrap()[0]
        model.add_constraints(
            [
                ConstraintSpec(name="row", terms=[(x, 1)], relation=relation, rhs=2),
                ConstraintSpec(name="row_eq_le", terms=[(x, 1)], relation="<=", rhs=6),
            ]
        ).unwrap()
        model.set_objective(terms=[(x, coefficient)], sense=sense).unwrap()
        handles = model.constraint_handles().unwrap()
        attempt = model.solve_compiled(solver=solver).unwrap()
        certificate = attempt.certificate.unwrap()
        assert attempt.report.termination_reason == "COMPLETED"
        assert attempt.report.objective == pytest.approx(
            coefficient * 2 * (-1 if sense == "maximize" else 1)
        )
        assert json.loads(attempt.report.raw_json)["modelMapping"] is not None
        assert model.source_price(
            certificate=certificate, handle=handles[0]
        ).unwrap() == pytest.approx(coefficient)
        assert model.source_price(
            certificate=certificate, handle=handles[1]
        ).unwrap() == pytest.approx(0)
        shifted = MetaModelFloat64.create("shifted-price").unwrap()
        try:
            y = shifted.add_variables([VariableSpec(name="x", lower=0)]).unwrap()[0]
            shifted.add_constraints(
                [
                    ConstraintSpec(
                        name="row", terms=[(y, 1)], relation=relation, rhs=2.1
                    ),
                    ConstraintSpec(
                        name="row_eq_le", terms=[(y, 1)], relation="<=", rhs=6
                    ),
                ]
            ).unwrap()
            shifted.set_objective(terms=[(y, coefficient)], sense=sense).unwrap()
            changed = shifted.solve_compiled(solver=solver).unwrap()
            assert changed.certificate.is_ok()
            assert changed.report.objective is not None
            assert attempt.report.objective is not None
            delta = (changed.report.objective - attempt.report.objective) * (
                -1 if sense == "maximize" else 1
            )
            assert delta == pytest.approx(coefficient * 0.1)
        finally:
            shifted.close().unwrap()
    finally:
        model.close().unwrap()


def test_certificate_provenance_and_mutation_lifetime(solver: str) -> None:
    model = create_model()
    foreign = create_model()
    try:
        handle = model.constraint_handles().unwrap()[0]
        other = foreign.constraint_handles().unwrap()[0]
        first = model.solve_compiled(solver=solver).unwrap()
        second = model.solve_compiled(solver=solver).unwrap()
        one, two = first.certificate.unwrap(), second.certificate.unwrap()
        assert one is not two
        assert model.source_price(
            certificate=one, handle=handle
        ).unwrap() == pytest.approx(3)
        assert model.source_price(
            certificate=two, handle=handle
        ).unwrap() == pytest.approx(3)
        assert foreign.source_price(certificate=one, handle=other).is_failed()
        assert model.source_price(certificate=one, handle=other).is_failed()
        assert model.source_price(certificate=first.report, handle=handle).is_failed()  # type: ignore[arg-type]
        assert model.source_price(
            certificate=json.loads(first.report.raw_json), handle=handle
        ).is_failed()
        assert model.add_constraints(
            [
                ConstraintSpec(name="temporary", terms=[], relation="<=", rhs=1),
                ConstraintSpec(name="row", terms=[], relation="<=", rhs=1),
            ]
        ).is_failed()
        assert model.source_price(
            certificate=one, handle=handle
        ).unwrap() == pytest.approx(3)
        x = model.add_variables(
            [VariableSpec(name="extra", lower=0, upper=0)]
        ).unwrap()[0]
        stale = model.source_price(certificate=one, handle=handle)
        assert (
            isinstance(stale, Failed)
            and stale.error.code is ErrorCode.FAILED_PRECONDITION
        )
        updated = model.solve_compiled(solver=solver).unwrap().certificate.unwrap()
        assert model.set_bounds(handle=x, lower=0, upper=1).is_ok()
        assert model.set_bounds(handle=x, lower=0, upper=0).is_ok()
        assert model.source_price(certificate=one, handle=handle).is_failed()
        assert model.source_price(certificate=updated, handle=handle).is_failed()
        assert first.report.objective == pytest.approx(-6)
        assert model.close().is_ok()
        assert model.source_price(certificate=two, handle=handle).is_failed()
    finally:
        model.close().unwrap()
        foreign.close().unwrap()


@pytest.mark.parametrize("kind", ["binary", "integer"])
def test_relaxed_compiled_uses_continuous_lp_and_keeps_certificate_lifetime(
    solver: str,
    kind: str,
) -> None:
    model = MetaModelFloat64.create("relaxed-certificate").unwrap()
    try:
        x = model.add_variables(
            [VariableSpec(name="x", kind=kind, lower=0, upper=1)]
        ).unwrap()[0]
        model.add_constraints(
            [ConstraintSpec(name="lower", terms=[(x, 1)], relation=">=", rhs=0.5)]
        ).unwrap()
        model.set_objective(terms=[(x, 1)], sense="minimize").unwrap()

        mip = model.solve_compiled(solver=solver).unwrap()
        relaxed = model.solve_relaxed_compiled(solver=solver).unwrap()

        assert mip.report.values == pytest.approx((1.0,))
        assert relaxed.report.values == pytest.approx((0.5,))
        certificate = relaxed.certificate.unwrap()
        handle = model.constraint_handles().unwrap()[0]
        assert model.source_price(
            certificate=certificate, handle=handle
        ).unwrap() == pytest.approx(1.0)

        model.add_variables([VariableSpec(name="extra", lower=0, upper=0)]).unwrap()
        assert model.source_price(certificate=certificate, handle=handle).is_failed()
        assert model.close().is_ok()
        assert model.source_price(certificate=certificate, handle=handle).is_failed()
    finally:
        model.close().unwrap()


def test_multirow_prices_match_independent_rhs_perturbations(solver: str) -> None:
    def run(*, capacity: float, upper: float) -> tuple[float, list[float]]:
        model = MetaModelFloat64.create("multirow").unwrap()
        try:
            x, y = model.add_variables(
                [
                    VariableSpec(name="x", lower=0, upper=3),
                    VariableSpec(name="y", lower=0, upper=3),
                ]
            ).unwrap()
            model.add_constraints(
                [
                    ConstraintSpec(
                        name="capacity",
                        terms=[(x, 1), (y, 1)],
                        relation="<=",
                        rhs=capacity,
                    ),
                    ConstraintSpec(
                        name="upper", terms=[(x, 1)], relation="<=", rhs=upper
                    ),
                ]
            ).unwrap()
            model.set_objective(terms=[(x, 3), (y, 2)], sense="maximize").unwrap()
            handles = model.constraint_handles().unwrap()
            attempt = model.solve_compiled(solver=solver).unwrap()
            certificate = attempt.certificate.unwrap()
            assert attempt.report.objective is not None
            prices = [
                model.source_price(certificate=certificate, handle=h).unwrap()
                for h in handles
            ]
            return -attempt.report.objective, prices
        finally:
            model.close().unwrap()

    objective, prices = run(capacity=4, upper=2)
    assert objective == pytest.approx(10)
    assert prices == pytest.approx([2, 1])
    assert run(capacity=4.1, upper=2)[0] - objective == pytest.approx(0.2)
    assert run(capacity=4, upper=2.1)[0] - objective == pytest.approx(0.1)


def test_degenerate_duals_are_not_unique_finite_differences(solver: str) -> None:
    def run(*, first: float, second: float) -> tuple[float, list[float]]:
        model = MetaModelFloat64.create("degenerate").unwrap()
        try:
            x = model.add_variables([VariableSpec(name="x", lower=0)]).unwrap()[0]
            model.add_constraints(
                [
                    ConstraintSpec(
                        name="first", terms=[(x, 1)], relation="<=", rhs=first
                    ),
                    ConstraintSpec(
                        name="second", terms=[(x, 1)], relation="<=", rhs=second
                    ),
                ]
            ).unwrap()
            model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
            attempt = model.solve_compiled(solver=solver).unwrap()
            certificate = attempt.certificate.unwrap()
            prices = [
                model.source_price(certificate=certificate, handle=handle).unwrap()
                for handle in model.constraint_handles().unwrap()
            ]
            assert attempt.report.objective is not None
            return -attempt.report.objective, prices
        finally:
            model.close().unwrap()

    objective, prices = run(first=2, second=2)
    assert objective == pytest.approx(6)
    assert sum(prices) == pytest.approx(3)
    assert run(first=3, second=2)[0] == pytest.approx(objective)
    assert run(first=2, second=3)[0] == pytest.approx(objective)


@pytest.mark.parametrize(
    "case", ["infeasible", "unbounded", "integer", "empty", "cancelled"]
)
def test_unavailable_certificate_keeps_original_report(solver: str, case: str) -> None:
    model = MetaModelFloat64.create(case).unwrap()
    try:
        x = model.add_variables(
            [
                VariableSpec(
                    name="x",
                    kind="binary" if case == "integer" else "continuous",
                    lower=0,
                )
            ]
        ).unwrap()[0]
        if case != "empty":
            model.add_constraints(
                [ConstraintSpec(name="lower", terms=[(x, 1)], relation=">=", rhs=1)]
            ).unwrap()
        if case == "infeasible":
            model.add_constraints(
                [ConstraintSpec(name="upper", terms=[(x, 1)], relation="<=", rhs=0)]
            ).unwrap()
        if case == "empty":
            model.set_bounds(handle=x, lower=0, upper=1).unwrap()
        model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
        control = SolveHandle()
        if case == "cancelled":
            control.cancel().unwrap()
        attempt = model.solve_compiled(solver=solver, cancellation=control).unwrap()
        assert attempt.certificate.is_failed()
        assert (
            attempt.report.termination_reason
            == json.loads(attempt.report.raw_json)["terminationReason"]
        )
        if case == "infeasible":
            assert attempt.report.problem_status == "INFEASIBLE"
        if case == "unbounded":
            assert attempt.report.problem_status in {
                "UNBOUNDED",
                "INFEASIBLE_OR_UNBOUNDED",
            }
        if case == "cancelled":
            assert attempt.report.termination_reason == "CANCELLED"
    finally:
        model.close().unwrap()


def test_limited_continuous_lp_does_not_issue_certificate(solver: str) -> None:
    model = MetaModelFloat64.create("limited-continuous-lp").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name=f"x{i}", lower=0, upper=1) for i in range(80)]
        ).unwrap()
        rng = random.Random(42)
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"edge-{i}-{j}",
                    terms=[(variables[i], 1), (variables[j], 1)],
                    relation="<=",
                    rhs=1,
                )
                for i in range(80)
                for j in range(i)
                if rng.random() < 0.4
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variable, 1) for variable in variables], sense="maximize"
        ).unwrap()
        control = SolveHandle()
        result = model.solve_compiled(
            solver=solver, time_limit=1e-9, cancellation=control
        )
        if solver == "scip":
            assert isinstance(result, Failed)
            assert result.error.code is ErrorCode.NOT_SUPPORTED
            assert control.phase == "READY"
            return
        attempt = result.unwrap()
        assert attempt.report.termination_reason == "TIME_LIMIT"
        assert attempt.certificate.is_failed()
        assert control.phase == "FINISHED"
        assert (
            json.loads(attempt.report.raw_json)["provenance"]["effectiveConfiguration"][
                "time_limit"
            ]
            == "Some(1e-9)"
        )
    finally:
        model.close().unwrap()


def test_compiled_callback_cannot_reenter_model(solver: str) -> None:
    model = create_model()
    errors: list[ErrorCode] = []
    handle = model.constraint_handles().unwrap()[0]
    certificate = model.solve_compiled(solver=solver).unwrap().certificate.unwrap()
    nested_control = SolveHandle()

    def callback(event: object) -> None:
        for result in (
            model.constraint_handles(),
            model.source_price(certificate=certificate, handle=handle),
            model.close(),
            model.solve_compiled(solver=solver, cancellation=nested_control),
        ):
            assert isinstance(result, Failed)
            errors.append(result.error.code)

    try:
        attempt = model.solve_compiled(solver=solver, on_progress=callback).unwrap()
        assert errors and all(code is ErrorCode.FAILED_PRECONDITION for code in errors)
        assert nested_control.phase == "READY"
        assert attempt.certificate.is_ok()
    finally:
        model.close().unwrap()


def test_cancel_during_compiled_backend_callback(solver: str) -> None:
    model = MetaModelFloat64.create("cancel-compiled").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(
                    name=f"x{i}",
                    kind="binary" if solver.startswith("gurobi") else "continuous",
                    lower=0,
                    upper=1,
                )
                for i in range(80)
            ]
        ).unwrap()
        rng = random.Random(42)
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"edge-{i}-{j}",
                    terms=[(variables[i], 1), (variables[j], 1)],
                    relation="<=",
                    rhs=1,
                )
                for i in range(80)
                for j in range(i)
                if rng.random() < 0.4
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variable, 1) for variable in variables], sense="maximize"
        ).unwrap()
        control = SolveHandle()
        events: list[SolveProgress] = []

        def cancel(event: SolveProgress) -> None:
            events.append(event)
            if event.source == "backend" and not control.is_cancelled:
                control.cancel(reason="compiled backend callback").unwrap()

        attempt = model.solve_compiled(
            solver=solver, cancellation=control, on_progress=cancel
        ).unwrap()
        assert any(event.source == "backend" for event in events)
        assert control.cancellation_preceded_completion
        assert attempt.report.termination_reason == "CANCELLED"
        assert attempt.certificate.is_failed()
    finally:
        model.close().unwrap()
