"""公开物理量换算用于真实 Rust 资源模型。 / Public quantity conversion feeds a real Rust resource model."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.quantities import NumericAdapter, Quantity
from ospf_python.quantities.unit.length import KILOMETER, METER
from ospf_python.utils.functional.result import Ok, Result

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True)
class _Value:
    fraction: Fraction


class _Adapter(NumericAdapter[_Value]):
    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        return Ok(value.fraction)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        return Ok(_Value(value))


@dataclass(frozen=True)
class _Resource[V]:
    capacity: Quantity[V]
    factors: tuple[Quantity[V], Quantity[V]]
    adapter: NumericAdapter[V] | None
    export: Callable[[V], Fraction]

    def standard(self, value: Quantity[V]) -> Fraction:
        converted = value.to(METER, numeric_adapter=self.adapter).unwrap()
        return self.export(converted.value)

    def coefficients(self) -> tuple[float, float, float]:
        # 求解边界显式无损导出，业务模型仍保留带单位的泛型值。
        # Export losslessly at the solver boundary; the business model retains generic quantities.
        capacity, first, second = (
            Rational.from_value(self.standard(value)).unwrap().to_float().unwrap()
            for value in (self.capacity, *self.factors)
        )
        return capacity, first, second


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("domain", ("fraction", "decimal", "custom"))
def test_public_result_conversion_registration_and_resource_recheck(
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
    export: Any = (lambda value: value.fraction) if domain == "custom" else Fraction
    resources = [
        _Resource(
            capacity=Quantity(value=factory("0.01"), unit=KILOMETER),
            factors=(
                Quantity(value=factory(1), unit=METER),
                Quantity(value=factory(1), unit=METER),
            ),
            adapter=adapter,
            export=export,
        ),
        _Resource(
            capacity=Quantity(value=factory("0.014"), unit=KILOMETER),
            factors=(
                Quantity(value=factory(2), unit=METER),
                Quantity(value=factory(1), unit=METER),
            ),
            adapter=adapter,
            export=export,
        ),
    ]
    model = MetaModelFloat64.create("public-quantity-result-resource-MILP").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(name="x", kind="integer", lower=0),
                VariableSpec(name="y", kind="integer", lower=0),
            ]
        ).unwrap()
        constraints = []
        for index, resource in enumerate(resources):
            capacity, first, second = resource.coefficients()
            constraints.append(
                ConstraintSpec(
                    name=f"resource-{index}",
                    terms=[(variables[0], first), (variables[1], second)],
                    relation="<=",
                    rhs=capacity,
                )
            )
        model.add_constraints(constraints).unwrap()
        model.set_objective(
            terms=[(variables[0], 3), (variables[1], 2)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((4, 6))
        assert report.objective == pytest.approx(24)
        for resource in resources:
            consumption = sum(
                resource.standard(value) * Fraction.from_float(count)
                for value, count in zip(resource.factors, report.values, strict=True)
            )
            assert consumption <= resource.standard(resource.capacity)
    finally:
        model.close().unwrap()
