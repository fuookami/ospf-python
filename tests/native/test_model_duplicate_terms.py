"""重复线性项的精确输入合同。 / Exact input contract for repeated linear terms."""

from __future__ import annotations

from fractions import Fraction
from sys import float_info

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


@pytest.mark.parametrize("kind", ("row", "objective"))
@pytest.mark.parametrize(
    ("coefficients", "code"),
    (
        ((1.0, 2.0**-53), ErrorCode.DATA_LOSS),
        ((-1.0, -(2.0**-53)), ErrorCode.DATA_LOSS),
        ((0.1, 0.2), ErrorCode.DATA_LOSS),
        ((float_info.max, float_info.max), ErrorCode.OVERFLOW),
        ((float_info.max, 1.0), ErrorCode.DATA_LOSS),
        ((-float_info.max, -1.0), ErrorCode.DATA_LOSS),
        ((float_info.max, -1.0), ErrorCode.DATA_LOSS),
        ((-float_info.max, 1.0), ErrorCode.DATA_LOSS),
        ((float_info.max, 2.0**970), ErrorCode.OVERFLOW),
        ((-float_info.max, -(2.0**970)), ErrorCode.OVERFLOW),
    ),
)
def test_unrepresentable_combined_coefficient_is_atomic(
    kind: str, coefficients: tuple[float, float], code: ErrorCode
) -> None:
    model = MetaModelFloat64.create("unrepresentable duplicates").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=1)]).unwrap()[0]
        model.add_constraints(
            [ConstraintSpec(name="existing", terms=[(x, 1)], relation="<=", rhs=1)]
        ).unwrap()
        model.set_objective(terms=[(x, 1)], sense="maximize").unwrap()
        before = model.snapshot().unwrap(), model.generation().unwrap()
        handle = model.constraint_handles().unwrap()[0]
        terms = [(x, coefficient) for coefficient in coefficients]
        if kind == "row":
            result = model.add_constraints(
                [
                    ConstraintSpec(name="first", terms=[(x, 1)], relation="<=", rhs=1),
                    ConstraintSpec(name="bad", terms=terms, relation="<=", rhs=0),
                ]
            )
        else:
            result = model.set_objective(terms=terms, sense="minimize")
        assert isinstance(result, Failed)
        assert result.error.code is code
        assert (model.snapshot().unwrap(), model.generation().unwrap()) == before
        assert model.constraint_index(handle=handle).unwrap() == 0
        assert (
            model.constraint_handles().unwrap()[0].source_identity
            == handle.source_identity
        )
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("sign", (-1, 1))
def test_sum_just_outside_finite_range_can_round_to_maximum(sign: int) -> None:
    maximum = Fraction.from_float(float_info.max)
    exact_sum = sign * (maximum + 1)
    assert abs(exact_sum) > maximum
    assert float(exact_sum) == sign * float_info.max


def test_exact_combination_avoids_intermediate_overflow() -> None:
    model = MetaModelFloat64.create("finite combined coefficient").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
        terms = [(x, float_info.max), (x, float_info.max), (x, -float_info.max)]
        assert sum(
            Fraction.from_float(value) for _, value in terms
        ) == Fraction.from_float(float_info.max)
        model.add_constraints(
            [ConstraintSpec(name="finite", terms=terms, relation="<=", rhs=1)]
        ).unwrap()
        assert model.constraint_handles().unwrap()[0].name == "finite"
        model.set_objective(terms=terms, sense="maximize").unwrap()
        assert model.constraint_handles().unwrap()[0].name == "finite"
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("kind", ("row", "objective"))
def test_only_final_exact_sum_must_be_representable(kind: str) -> None:
    model = MetaModelFloat64.create("exact final coefficient").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
        terms = [(x, 1.0), (x, 2.0**-53), (x, -(2.0**-53))]
        assert sum(Fraction.from_float(value) for _, value in terms) == 1
        if kind == "row":
            model.add_constraints(
                [ConstraintSpec(name="row", terms=terms, relation="<=", rhs=1)]
            ).unwrap()
        else:
            model.set_objective(terms=terms, sense="minimize").unwrap()
        assert model.constraint_handles().is_ok()
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("kind", ("row", "objective"))
@pytest.mark.parametrize("compiled", (False, True))
def test_combined_cancellation_reaches_real_solver(
    solver: str, kind: str, compiled: bool
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    model = MetaModelFloat64.create("duplicate-cancellation").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", kind="binary")]).unwrap()[0]
        coefficients = (1e16, 1.0, -1e16)
        assert sum(map(Fraction.from_float, coefficients)) == 1
        terms = [(x, coefficient) for coefficient in coefficients]
        if kind == "row":
            model.add_constraints(
                [ConstraintSpec(name="upper", terms=terms, relation="<=", rhs=0)]
            ).unwrap()
            model.set_objective(terms=[(x, 1)], sense="maximize").unwrap()
        else:
            model.set_objective(terms=terms, sense="maximize").unwrap()
        if compiled:
            report = model.solve_compiled(solver=solver).unwrap().report
        else:
            report = model.solve(solver=solver).unwrap()
        expected = 0.0 if kind == "row" else 1.0
        assert report.termination_reason == "COMPLETED"
        assert report.values == pytest.approx((expected,))
        assert report.objective == pytest.approx(-expected if compiled else expected)
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
def test_duplicate_row_certificate_refers_to_the_original_exact_model(
    solver: str,
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    model = MetaModelFloat64.create("duplicate row certificate").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", upper=1)]).unwrap()[0]
        coefficients = (1e16, 1.0, -1e16)
        model.add_constraints(
            [
                ConstraintSpec(
                    name="upper",
                    terms=[(x, coefficient) for coefficient in coefficients],
                    relation="<=",
                    rhs=0,
                )
            ]
        ).unwrap()
        model.set_objective(terms=[(x, 1)], sense="maximize").unwrap()
        attempt = model.solve_compiled(solver=solver).unwrap()
        solution = Fraction.from_float(attempt.report.values[0])
        assert sum(Fraction.from_float(c) * solution for c in coefficients) <= 0
        assert solution == 0
        certificate = attempt.certificate.unwrap()
        row = model.constraint_handles().unwrap()[0]
        assert model.source_price(certificate=certificate, handle=row).unwrap() == 1
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("kind", ("row", "objective"))
def test_rejected_duplicates_preserve_prior_solution_and_certificate(
    solver: str, kind: str
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    model = MetaModelFloat64.create("duplicate rejection rollback").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=2)]).unwrap()[0]
        model.add_constraints(
            [ConstraintSpec(name="limit", terms=[(x, 1)], relation="<=", rhs=1)]
        ).unwrap()
        model.set_objective(terms=[(x, 3)], sense="maximize").unwrap()
        row = model.constraint_handles().unwrap()[0]
        certificate = model.solve_compiled(solver=solver).unwrap().certificate.unwrap()
        generation = model.generation().unwrap()
        terms = [(x, 1.0), (x, 2.0**-53)]
        if kind == "row":
            result = model.add_constraints(
                [
                    ConstraintSpec(name="first", terms=[(x, 1)], relation="<=", rhs=1),
                    ConstraintSpec(name="bad", terms=terms, relation="<=", rhs=1),
                ]
            )
        else:
            result = model.set_objective(terms=terms, sense="minimize")
        assert isinstance(result, Failed) and result.error.code is ErrorCode.DATA_LOSS
        assert model.generation().unwrap() == generation
        assert model.source_price(certificate=certificate, handle=row).unwrap() == 3
        report = model.solve(solver=solver).unwrap()
        assert report.values == pytest.approx((1,))
        assert report.objective == pytest.approx(3)
        assert model.source_price(certificate=certificate, handle=row).unwrap() == 3
    finally:
        model.close().unwrap()
