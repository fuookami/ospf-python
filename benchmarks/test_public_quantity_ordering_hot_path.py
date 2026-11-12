"""数量极值/范围的完整自然调用。 / Complete natural calls for quantity extrema and ranges."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python._binding.numeric import Rational
from ospf_python._binding.unit_registry import _families
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import (
    NumericAdapter,
    Quantity,
    QuantityValueRange,
    max_quantity,
    min_quantity,
)
from ospf_python.utils.functional.result import Ok, Result

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_benchmark.fixture import BenchmarkFixture


@dataclass(frozen=True)
class _Value:
    value: Fraction


class _Adapter(NumericAdapter[_Value]):
    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        return Ok(value.value)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        return Ok(_Value(value))


def _value(*, domain: str, value: int) -> Any:
    if domain == "fraction":
        return Fraction(value, 4)
    if domain == "decimal":
        return Decimal(value) / 4
    if domain == "rational":
        return Rational.create(numerator=value, denominator=4).unwrap()
    if domain == "public-rational":
        return PublicRational(value, 4)
    if domain == "float":
        return value / 4
    if domain == "floating":
        return Floating(value / 4)
    if domain == "custom":
        return _Value(Fraction(value, 4))
    return value


_DOMAINS = (
    "int",
    "fraction",
    "decimal",
    "rational",
    "public-rational",
    "float",
    "floating",
    "custom",
)


def _operation(
    *, family: Any, domain: str, operation: str
) -> tuple[Callable[[], Any], list[Any], Any]:
    items = [
        Quantity(value=_value(domain=domain, value=value), unit=family.cls())
        for value in (12, 4, 8)
    ]
    adapter = _Adapter() if domain == "custom" else None
    bounds = QuantityValueRange(min_qty=items[1], max_qty=items[0])
    expected = (
        True
        if operation == "contains"
        else items[1]
        if operation == "min"
        else items[0]
    )

    def call() -> Any:
        if operation == "contains":
            return bounds.contains(items[2], numeric_adapter=adapter).unwrap()
        function = min_quantity if operation == "min" else max_quantity
        return function(items, numeric_adapter=adapter).unwrap()

    return call, items, expected


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "family", list(_families.values()), ids=lambda family: family.cls.__name__
)
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("operation", ("min", "max", "contains"))
def test_public_quantity_ordering_complete_call(
    *, benchmark: BenchmarkFixture, family: Any, domain: str, operation: str
) -> None:
    call, owners, expected = _operation(
        family=family, domain=domain, operation=operation
    )
    assert benchmark(call) is expected
    assert all(set(vars(owner)) == {"value", "unit"} for owner in owners)
