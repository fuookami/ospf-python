"""数量快照完整调用成本，新 DTO 不假称存在旧同义预算。 / Complete snapshot call cost; new DTO APIs have no invented legacy budget."""

from __future__ import annotations

import copy
import pickle
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python._binding.numeric import Rational
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import Quantity, SnapshotAdapter, Unit
from ospf_python.quantities.unit.length import METER
from ospf_python.quantities.unit.temperature import CELSIUS
from ospf_python.utils.functional.result import Ok, Result

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_benchmark.fixture import BenchmarkFixture

_DOMAINS = (
    "int",
    "fraction",
    "decimal",
    "public-rational",
    "rational",
    "float",
    "floating",
    "custom",
)
_UNITS = ("builtin", "runtime", "difference")
_OPERATIONS = ("to_dict", "to_json", "from_dict", "from_json", "deepcopy", "pickle")


@dataclass(frozen=True)
class _Value:
    fraction: Fraction


class _Adapter(SnapshotAdapter[_Value]):
    def to_snapshot(self, value: _Value) -> Result[Any, Any, Any]:
        return Ok([hex(value.fraction.numerator), hex(value.fraction.denominator)])

    def from_snapshot(self, snapshot: Any) -> Result[_Value, Any, Any]:
        return Ok(_Value(Fraction(int(snapshot[0], 16), int(snapshot[1], 16))))


def _operation(
    *, domain: str, units: str, operation: str
) -> tuple[Callable[[], Any], Any]:
    value: Any = (
        Rational.from_value(7).unwrap()
        if domain == "rational"
        else _Value(Fraction(7))
        if domain == "custom"
        else {
            "int": int,
            "fraction": Fraction,
            "decimal": Decimal,
            "public-rational": PublicRational,
            "float": float,
            "floating": Floating,
        }[domain](7)
    )
    unit: Any = METER
    if units == "runtime":
        unit = Unit.create(
            name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
        ).unwrap()
    elif units == "difference":
        unit = (
            Quantity(value=80, unit=CELSIUS)
            .subtract(Quantity(value=20, unit=CELSIUS))
            .unwrap()
            .unit
        )
    owner = Quantity(value=value, unit=unit)
    adapter = _Adapter() if domain == "custom" else None
    wire = owner.to_dict(value_adapter=adapter).unwrap()
    text = owner.to_json(value_adapter=adapter).unwrap()
    operations: dict[str, Callable[[], Any]] = {
        "to_dict": lambda: owner.to_dict(value_adapter=adapter).unwrap(),
        "to_json": lambda: owner.to_json(value_adapter=adapter).unwrap(),
        "from_dict": lambda: Quantity.from_dict(wire, value_adapter=adapter).unwrap(),
        "from_json": lambda: Quantity.from_json(text, value_adapter=adapter).unwrap(),
        "deepcopy": lambda: copy.deepcopy(owner),
        "pickle": lambda: pickle.loads(pickle.dumps(owner)),
    }
    return operations[operation], owner


@pytest.mark.benchmark
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("units", _UNITS)
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_natural_quantity_snapshot_complete_call(
    *, benchmark: BenchmarkFixture, domain: str, units: str, operation: str
) -> None:
    call, owner = _operation(domain=domain, units=units, operation=operation)
    output = benchmark(call)
    adapter = _Adapter() if domain == "custom" else None
    if operation == "to_dict":
        output = Quantity.from_dict(output, value_adapter=adapter).unwrap()
    elif operation == "to_json":
        output = Quantity.from_json(output, value_adapter=adapter).unwrap()
    assert type(output.value) is type(owner.value) and output.value == owner.value
    if units == "builtin":
        assert output.unit == owner.unit
    else:
        assert output.unit.descriptor() == owner.unit.descriptor()
