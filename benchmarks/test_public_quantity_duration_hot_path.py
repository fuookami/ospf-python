"""时长自然入口的完整调用，不将私有转换当作预算验收。 / Complete duration calls, not private conversion budgets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python._binding.numeric import Rational
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import (
    NumericAdapter,
    Quantity,
    from_hours,
    from_minutes,
    to_timedelta,
)
from ospf_python.quantities.unit import time_unit
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


_DOMAINS = (
    "int",
    "fraction",
    "decimal",
    "private",
    "public",
    "float",
    "floating",
    "custom",
)
_UNITS = [
    unit
    for name, unit in vars(time_unit).items()
    if name.isupper() and type(unit) is time_unit.TimeUnit
]
_OPERATIONS = ("from_hours", "from_minutes", *(unit.symbol for unit in _UNITS))


def _operation(*, domain: str, operation: str) -> tuple[Callable[[], Any], Any, Any]:
    values: dict[str, Callable[[], Any]] = {
        "int": lambda: 1,
        "fraction": lambda: Fraction(1, 4),
        "decimal": lambda: Decimal("0.25"),
        "private": lambda: Rational.create(numerator=1, denominator=4).unwrap(),
        "public": lambda: PublicRational(1, 4),
        "float": lambda: 0.25,
        "floating": lambda: Floating(0.25),
        "custom": lambda: _Value(Fraction(1, 4)),
    }
    value = values[domain]()
    adapter = _Adapter() if domain == "custom" else None
    if operation in ("from_hours", "from_minutes"):
        function = from_hours if operation == "from_hours" else from_minutes
        factor = 3600 if operation == "from_hours" else 60
        return (
            lambda: function(value, numeric_adapter=adapter).unwrap(),
            value,
            Fraction(1, 1 if domain == "int" else 4) * factor,
        )
    unit = next(unit for unit in _UNITS if unit.symbol == operation)
    owner = Quantity(value=value, unit=unit)
    expected = (
        timedelta(seconds=0.25 * unit._factor)
        if domain in ("float", "floating")
        else timedelta(
            microseconds=round(
                Fraction(1, 1 if domain == "int" else 4)
                * Fraction(unit._factor)
                * 1000000
            )
        )
    )
    return (
        lambda: to_timedelta(owner, numeric_adapter=adapter).unwrap(),
        owner,
        expected,
    )


def _fraction(value: Any) -> Fraction:
    if type(value) is _Value:
        return value.value
    if type(value) is Rational:
        return Fraction(*value.as_integer_ratio())
    if type(value) is PublicRational:
        return Fraction(value.numerator, value.denominator)
    if type(value) is Floating:
        return Fraction(value.value)
    return Fraction(value)


@pytest.mark.benchmark
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_public_duration_complete_call(
    *, benchmark: BenchmarkFixture, domain: str, operation: str
) -> None:
    call, _, expected = _operation(domain=domain, operation=operation)
    output = benchmark(call)
    if operation in ("from_hours", "from_minutes"):
        assert _fraction(output.value) == expected and output.unit is time_unit.SECOND
    else:
        assert output == expected
