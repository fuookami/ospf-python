"""真实原生温差输出单位参与热资源MILP。 / Real native difference output units drive a thermal-resource MILP."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.quantities import NumericAdapter, Quantity, QuantityValueRange, Unit
from ospf_python.utils.functional.result import Ok, Result


@dataclass(frozen=True)
class _Value:
    value: Fraction


class _Adapter(NumericAdapter[_Value]):
    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        return Ok(value.value)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        return Ok(_Value(value))


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
def test_exact_mixed_affine_capacity_reaches_real_solver(solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    powers = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    point = Unit.create(
        name="point", symbol="P", powers=powers, scale=3, offset=1
    ).unwrap()
    difference = Unit.create(name="difference", symbol="D", powers=powers).unwrap()
    standard = Unit.create(
        name="standard point", symbol="S", powers=powers, offset=0
    ).unwrap()
    total = (
        Quantity(value=Fraction(10), unit=point) + Quantity(value=1, unit=difference)
    ).unwrap()
    assert total.value == Fraction(31, 3) and total.unit is point
    capacity = total.to(standard).unwrap()
    assert capacity.value == 32
    model = MetaModelFloat64.create("exact-mixed-affine-resource").unwrap()
    try:
        variable = model.add_variables(
            [
                VariableSpec(
                    name="x", kind="integer", lower=0, upper=float(capacity.value)
                )
            ]
        ).unwrap()[0]
        model.set_objective(terms=[(variable, 1)], sense="maximize").unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL" and report.values == pytest.approx(
            (32,)
        )
        recovered = Quantity(value=Fraction.from_float(report.values[0]), unit=standard)
        assert recovered.to(point).unwrap().value == total.value
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("domain", ("fraction", "decimal", "custom"))
def test_native_difference_capacity_and_original_domain_postcheck(
    *, solver: str, domain: str
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    powers = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    point = Unit.create(
        name="temperature point", symbol="P", powers=powers, offset=Decimal("273.15")
    ).unwrap()
    capacity_value, actual_difference = point.binary_exact(
        value=80, other=20, other_unit=point, subtract=True
    ).unwrap()
    assert not actual_difference.is_affine
    factory: Any = (
        Fraction
        if domain == "fraction"
        else Decimal
        if domain == "decimal"
        else lambda value: _Value(Fraction(value))
    )
    adapter: Any = _Adapter() if domain == "custom" else None
    export: Any = (lambda value: value.value) if domain == "custom" else Fraction
    capacity_fraction = Fraction(*capacity_value.as_integer_ratio())
    capacity = Quantity(value=factory(str(capacity_fraction)), unit=actual_difference)
    standard = Unit.create(
        name="temperature difference", symbol="dK", powers=powers
    ).unwrap()
    converted = capacity.to(standard, numeric_adapter=adapter).unwrap()
    costs = [
        Quantity(value=factory(value), unit=actual_difference)
        .to(standard, numeric_adapter=adapter)
        .unwrap()
        for value in (3, 5)
    ]
    coefficients = [
        Rational.from_value(export(cost.value)).unwrap().to_float().unwrap()
        for cost in costs
    ]
    bound = Rational.from_value(export(converted.value)).unwrap().to_float().unwrap()
    model = MetaModelFloat64.create("public-native-difference-resource").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(name="x", kind="integer", lower=0),
                VariableSpec(name="y", kind="integer", lower=0),
            ]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name="heat",
                    terms=list(zip(variables, coefficients, strict=True)),
                    relation="<=",
                    rhs=bound,
                ),
                ConstraintSpec(
                    name="count",
                    terms=[(variable, 1) for variable in variables],
                    relation="<=",
                    rhs=14,
                ),
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 3), (variables[1], 4)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL" and report.values == pytest.approx(
            (5, 9)
        )
        raw_used = sum(
            Fraction.from_float(value) * export(cost.value)
            for value, cost in zip(report.values, costs, strict=True)
        )
        assert (
            QuantityValueRange(
                min_qty=Quantity(value=Fraction(0), unit=standard),
                max_qty=Quantity(value=capacity_fraction, unit=standard),
            )
            .contains(Quantity(value=raw_used, unit=standard))
            .unwrap()
        )
        # 先证明求解器浮点结果的整数性，再按原数值域重建离散解。
        # Prove solver-output integrality before reconstructing the discrete solution in its original domain.
        counts = tuple(round(value) for value in report.values)
        assert counts == (5, 9)
        assert all(
            abs(value - count) <= 1e-8
            for value, count in zip(report.values, counts, strict=True)
        )
        used = sum(
            count * export(cost.value)
            for count, cost in zip(counts, costs, strict=True)
        )
        consumption = Quantity(value=factory(str(used)), unit=standard)
        zero = Quantity(value=factory(0), unit=standard)
        assert (
            QuantityValueRange(min_qty=zero, max_qty=converted)
            .contains(consumption, numeric_adapter=adapter)
            .unwrap()
        )
        assert (
            export(
                consumption.to(actual_difference, numeric_adapter=adapter)
                .unwrap()
                .value
            )
            == capacity_fraction
        )
    finally:
        model.close().unwrap()
