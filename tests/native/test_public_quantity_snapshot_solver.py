"""恢复原生单位后装配真实热资源模型并原域复验。 / Restored native units feed real thermal models with original-domain postchecks."""

from __future__ import annotations

import copy
import pickle
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
    SnapshotAdapter,
)
from ospf_python.quantities.unit.temperature import CELSIUS
from ospf_python.utils.functional.result import Ok, Result


@dataclass(frozen=True)
class _Value:
    value: Fraction


class _Adapter(NumericAdapter[_Value], SnapshotAdapter[_Value]):
    def to_snapshot(self, value: _Value) -> Result[Any, Any, Any]:
        return Ok([hex(value.value.numerator), hex(value.value.denominator)])

    def from_snapshot(self, snapshot: Any) -> Result[_Value, Any, Any]:
        return Ok(_Value(Fraction(int(snapshot[0], 16), int(snapshot[1], 16))))

    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        return Ok(value.value)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        return Ok(_Value(value))


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("domain", ("fraction", "decimal", "custom"))
@pytest.mark.parametrize("restoration", ("json", "pickle", "deepcopy"))
def test_restored_quantity_drives_real_thermal_resource_milp(
    *, solver: str, domain: str, restoration: str
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
    export: Any = (lambda value: value.value) if domain == "custom" else Fraction
    adapter: Any = _Adapter() if domain == "custom" else None
    capacity = (
        Quantity(value=factory(80), unit=CELSIUS)
        .subtract(Quantity(value=factory(20), unit=CELSIUS), numeric_adapter=adapter)
        .unwrap()
    )
    assert not capacity.unit.is_affine
    if restoration == "json":
        capacity = Quantity.from_json(
            capacity.to_json(value_adapter=adapter).unwrap(), value_adapter=adapter
        ).unwrap()
    elif restoration == "pickle":
        capacity = pickle.loads(pickle.dumps(capacity))
    else:
        capacity = copy.deepcopy(capacity)
    assert not capacity.unit.is_affine
    costs = [
        capacity.divide(factory(divisor), numeric_adapter=adapter).unwrap()
        for divisor in (20, 12)
    ]
    coefficients = [
        Rational.from_value(export(cost.value)).unwrap().to_float().unwrap()
        for cost in costs
    ]
    bound = Rational.from_value(export(capacity.value)).unwrap().to_float().unwrap()
    model = MetaModelFloat64.create("public-snapshot-thermal-resource").unwrap()
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
        counts = tuple(round(value) for value in report.values)
        assert counts == (5, 9) and all(
            abs(value - count) <= 1e-8
            for value, count in zip(report.values, counts, strict=True)
        )
        used = [
            cost.multiply(factory(count), numeric_adapter=adapter).unwrap()
            for cost, count in zip(costs, counts, strict=True)
        ]
        total = used[0].add(used[1], numeric_adapter=adapter).unwrap()
        assert (
            type(total.value) is type(capacity.value)
            and export(total.value) == export(capacity.value) == 60
        )
        assert (
            total.to(capacity.unit, numeric_adapter=adapter).unwrap().value
            == capacity.value
        )
        assert (
            QuantityValueRange(min_qty=capacity, max_qty=capacity)
            .contains(total, numeric_adapter=adapter)
            .unwrap()
        )
    finally:
        model.close().unwrap()
