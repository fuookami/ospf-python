"""公开物理量转换完整调用基准。 / Complete-call public quantity conversion benchmarks."""

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
from ospf_python.quantities import NumericAdapter, Quantity
from ospf_python.utils.functional.result import Ok, Result

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_benchmark.fixture import BenchmarkFixture


@dataclass(frozen=True)
class _Value:
    fraction: Fraction


class _Adapter(NumericAdapter[_Value]):
    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        return Ok(value.fraction)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        return Ok(_Value(value))


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


def _value(domain: str) -> Any:
    if domain == "int":
        return 2**100 + 1
    if domain == "decimal":
        return Decimal("1.2345")
    if domain == "rational":
        return Rational.create(numerator=1, denominator=3).unwrap()
    if domain == "public-rational":
        return PublicRational(1, 3)
    if domain == "float":
        return 1.25
    if domain == "floating":
        return Floating(1.25)
    if domain == "custom":
        return _Value(Fraction(1, 3))
    return Fraction(1, 3)


def _operation(
    *, family: Any, scale: float, domain: str
) -> tuple[Callable[[], Any], Quantity[Any], Any]:
    owner = Quantity(value=_value(domain), unit=family.cls(_factor=scale))
    target = family.cls()
    adapter = _Adapter() if domain == "custom" else None

    def call() -> Any:
        return owner.to(target, numeric_adapter=adapter).unwrap().value

    return call, owner, target


def _fraction(value: Any) -> Fraction:
    if type(value) is Rational:
        return Fraction(*value.as_integer_ratio())
    if type(value) is PublicRational:
        return Fraction(value.numerator, value.denominator)
    if type(value) is Floating:
        return Fraction(value.value)
    if type(value) is _Value:
        return value.fraction
    return Fraction(value)


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "family", list(_families.values()), ids=lambda family: family.cls.__name__
)
@pytest.mark.parametrize("scale", (1.0, 1000.0))
@pytest.mark.parametrize("domain", _DOMAINS)
def test_public_quantity_complete_conversion(
    *, benchmark: BenchmarkFixture, family: Any, scale: float, domain: str
) -> None:
    operation, owner, _ = _operation(family=family, scale=scale, domain=domain)
    value = benchmark(operation)
    assert type(value) is type(owner.value)
    assert _fraction(value) == _fraction(owner.value) * Fraction(scale)
