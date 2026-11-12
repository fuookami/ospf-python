"""自然四则完整调用成本，不减去边界开销。 / Complete natural arithmetic cost, without subtracting boundary overhead."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from operator import add, sub
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python._binding.numeric import Rational
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import NumericAdapter, Quantity, Unit
from ospf_python.quantities.unit.length import METER, Length
from ospf_python.utils.functional.result import Ok, Result

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_benchmark.fixture import BenchmarkFixture

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
_OPERATIONS = ("add", "subtract", "multiply", "divide")
_UNITS = ("linear-identical", "same-symbol-different-scale", "runtime-linear")


@dataclass(frozen=True)
class _Value:
    fraction: Fraction


class _Adapter(NumericAdapter[_Value]):
    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        return Ok(value.fraction)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        return Ok(_Value(value))


def _value(domain: str, number: int) -> Any:
    if domain == "rational":
        return Rational.from_value(number).unwrap()
    if domain == "custom":
        return _Value(Fraction(number))
    return {
        "int": int,
        "fraction": Fraction,
        "decimal": Decimal,
        "public-rational": PublicRational,
        "float": float,
        "floating": Floating,
    }[domain](number)


def _fraction(value: Any) -> Fraction:
    if type(value) is _Value:
        return value.fraction
    if type(value) is Rational:
        return Fraction(*value.as_integer_ratio())
    if type(value) is PublicRational:
        return Fraction(value.numerator, value.denominator)
    if type(value) is Floating:
        return Fraction(value.value)
    return Fraction(value)


def _operation(
    *, domain: str, operation: str, units: str
) -> tuple[Callable[[], Any], Any, Any, Fraction]:
    source: Any = METER
    if units == "runtime-linear":
        source = Unit.create(
            name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
        ).unwrap()
    target = Length("m", 1000) if units == "same-symbol-different-scale" else source
    owner = Quantity(value=_value(domain, 6), unit=source)
    binary = operation in ("add", "subtract")
    other = (
        Quantity(value=_value(domain, 2), unit=target) if binary else _value(domain, 2)
    )
    adapter = _Adapter() if domain == "custom" else None

    def call() -> Any:
        return getattr(owner, operation)(other, numeric_adapter=adapter).unwrap().value

    rhs = 2000 if binary and units == "same-symbol-different-scale" else 2
    expected = Fraction(
        {"add": 6 + rhs, "subtract": 6 - rhs, "multiply": 12, "divide": 3}[operation]
    )
    return call, owner, other, expected


@pytest.mark.benchmark
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("operation", _OPERATIONS)
@pytest.mark.parametrize("units", _UNITS)
def test_natural_quantity_complete_arithmetic(
    *, benchmark: BenchmarkFixture, domain: str, operation: str, units: str
) -> None:
    call, owner, _, expected = _operation(
        domain=domain, operation=operation, units=units
    )
    output = benchmark(call)
    assert type(output) is type(owner.value)
    assert _fraction(output) == expected


@pytest.mark.benchmark
@pytest.mark.parametrize("point_scale", (1, 2, 3))
@pytest.mark.parametrize("operation", ("point+delta", "delta+point", "point-delta"))
def test_exact_mixed_affine_complete_arithmetic(
    *, benchmark: BenchmarkFixture, point_scale: int, operation: str
) -> None:
    powers = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    point = Unit.create(
        name="point", symbol="P", powers=powers, scale=point_scale, offset=1
    ).unwrap()
    difference = Unit.create(name="difference", symbol="D", powers=powers).unwrap()
    point_value = Quantity(value=Fraction(10), unit=point)
    difference_value = Quantity(value=Fraction(1), unit=difference)
    left, right = (
        (difference_value, point_value)
        if operation == "delta+point"
        else (point_value, difference_value)
    )
    calculate = sub if operation == "point-delta" else add
    output = benchmark(lambda: calculate(left, right).unwrap())
    delta = Fraction(1, point_scale)
    assert output.value == 10 + (-delta if operation == "point-delta" else delta)
    assert output.unit is point
