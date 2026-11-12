"""公开时长入口参与资源 MILP 及解后时间校验。 / Public durations drive resource MILP and post-solve checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.quantities import (
    NumericAdapter,
    from_hours,
    from_minutes,
    to_timedelta,
)
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
def test_time_capacity_registration_and_original_domain_recheck(
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
    capacity = from_hours(factory(2), numeric_adapter=adapter).unwrap()
    costs = [
        from_minutes(factory(value), numeric_adapter=adapter).unwrap()
        for value in (10, 5)
    ]
    # 仅求解注册边界导出 float，公开时长构造和解后检查保留领域表示。
    # Export float only at solver registration; constructors/postchecks retain domain values.
    coefficients = [
        Rational.from_value(export(cost.value)).unwrap().to_float().unwrap()
        for cost in costs
    ]
    upper = Rational.from_value(export(capacity.value)).unwrap().to_float().unwrap()
    model = MetaModelFloat64.create("public-quantity-duration-resource").unwrap()
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
                    name="time",
                    terms=list(zip(variables, coefficients, strict=True)),
                    relation="<=",
                    rhs=upper,
                ),
                ConstraintSpec(
                    name="count",
                    terms=[(variable, 1) for variable in variables],
                    relation="<=",
                    rhs=18,
                ),
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 3), (variables[1], 2)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL" and report.values == pytest.approx(
            (6, 12)
        )
        minutes = sum(
            Fraction.from_float(value) * cost
            for value, cost in zip(report.values, (10, 5), strict=True)
        )
        used = from_minutes(factory(str(minutes)), numeric_adapter=adapter).unwrap()
        assert to_timedelta(used, numeric_adapter=adapter).unwrap() == timedelta(
            hours=2
        )
        assert (
            to_timedelta(used, numeric_adapter=adapter).unwrap()
            <= to_timedelta(capacity, numeric_adapter=adapter).unwrap()
        )
    finally:
        model.close().unwrap()
