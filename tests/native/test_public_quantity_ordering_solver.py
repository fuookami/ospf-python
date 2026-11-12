"""公开数量极值/范围参与真实资源求解。 / Public quantity ordering participates in a real resource solve."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.quantities import (
    NumericAdapter,
    Quantity,
    QuantityValueRange,
    max_quantity,
    min_quantity,
)
from ospf_python.quantities.unit.length import KILOMETER, METER
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
@pytest.mark.parametrize("domain", ("fraction", "decimal", "custom"))
def test_ordered_resource_limit_registration_and_original_domain_recheck(
    *, solver: str, domain: str
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    factory: Any = (
        Fraction
        if domain == "fraction"
        else Decimal
        if domain == "decimal"
        else lambda value: _Value(Fraction(value))
    )
    adapter: Any = _Adapter() if domain == "custom" else None
    export: Any = (lambda value: value.value) if domain == "custom" else Fraction
    capacities = [
        Quantity(value=factory("0.01"), unit=KILOMETER),
        Quantity(value=factory(14), unit=METER),
    ]
    bottleneck = min_quantity(capacities, numeric_adapter=adapter).unwrap()
    assert bottleneck is capacities[0]
    assert max_quantity(capacities, numeric_adapter=adapter).unwrap() is capacities[1]
    exact = export(bottleneck.to(METER, numeric_adapter=adapter).unwrap().value)
    # 仅求解注册边界导出裸 float，数量选择与解后验证保留领域表示。
    # Export bare float only at solver registration; selection and post-solve checks retain domain values.
    upper = Rational.from_value(exact).unwrap().to_float().unwrap()
    model = MetaModelFloat64.create("public-quantity-ordered-resource").unwrap()
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
                    name="selected-resource",
                    terms=[(variables[0], 1), (variables[1], 1)],
                    relation="<=",
                    rhs=upper,
                ),
                ConstraintSpec(
                    name="second-resource",
                    terms=[(variables[0], 2), (variables[1], 1)],
                    relation="<=",
                    rhs=14,
                ),
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 3), (variables[1], 2)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL" and report.values == pytest.approx(
            (4, 6)
        )
        consumption = Quantity(
            value=factory(
                str(sum(Fraction.from_float(value) for value in report.values))
            ),
            unit=METER,
        )
        for capacity in capacities:
            assert (
                QuantityValueRange(
                    min_qty=Quantity(value=factory(0), unit=METER), max_qty=capacity
                )
                .contains(consumption, numeric_adapter=adapter)
                .unwrap()
            )
    finally:
        model.close().unwrap()
