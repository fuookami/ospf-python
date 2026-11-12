"""原生输出的完整复制/pickle及显式纯数据往返。 / Native-output copy/pickle and explicit data round trips."""

from __future__ import annotations

import copy
import gc
import importlib
import math
import os
import pickle
import struct
import subprocess
import sys
import weakref
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, fields
from decimal import Context, Decimal, localcontext
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.numeric import Rational
from ospf_python._binding.unit_registry import _families
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import Quantity, QuantityValueRange, SnapshotAdapter, Unit
from ospf_python.quantities.unit.length import METER, Length
from ospf_python.quantities.unit.temperature import CELSIUS
from ospf_python.utils.functional.result import Failed, Ok, Result

_DOMAINS = (int, Fraction, Decimal, PublicRational, Rational, float, Floating)


def _pickle_copy(protocol: int) -> Callable[[Any], Any]:
    def call(value: Any) -> Any:
        return pickle.loads(pickle.dumps(value, protocol=protocol))

    return call


_COPY: dict[str, Callable[[Any], Any]] = {
    "copy": copy.copy,
    "deepcopy": copy.deepcopy,
    **{
        f"pickle-{protocol}": _pickle_copy(protocol)
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1)
    },
}
_TEMPERATURE = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)


def _value(domain: Any, value: int = 7) -> Any:
    return Rational.from_value(value).unwrap() if domain is Rational else domain(value)


def _identity(value: Any) -> Any:
    if type(value) is float:
        return struct.pack("!d", value)
    if type(value) is Decimal:
        return value.as_tuple()
    if type(value) is PublicRational:
        return value.numerator, value.denominator
    if type(value) in (Rational, Fraction):
        return value.as_integer_ratio()
    if type(value) is Floating:
        return type(value.value), _identity(value.value)
    return value


def _unit(kind: str) -> Any:
    if kind == "difference":
        return (
            Quantity(value=80, unit=CELSIUS)
            .subtract(Quantity(value=20, unit=CELSIUS))
            .unwrap()
            .unit
        )
    return Unit.create(
        name="point" if kind == "point" else "linear",
        symbol="P" if kind == "point" else "L",
        powers=_TEMPERATURE,
        scale=Decimal("1.2300"),
        offset=Decimal("0.000") if kind == "point" else None,
    ).unwrap()


@pytest.mark.parametrize("kind", ("linear", "point", "difference"))
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("operation", _COPY)
def test_every_domain_and_actual_native_output_support_copy_and_all_pickle_protocols(
    *, kind: str, domain: Any, operation: str
) -> None:
    unit = _unit(kind)
    owner = Quantity(value=_value(domain), unit=unit)
    output = _COPY[operation](owner)
    assert type(output) is Quantity and type(output.value) is domain
    assert _identity(output.value) == _identity(owner.value)
    assert isinstance(output.unit, Unit)
    assert output.unit.descriptor() == unit.descriptor()
    assert output.unit.is_affine == (kind == "point")
    assert (
        Quantity(value=output.value, unit=output.unit).to(unit).unwrap().value
        == owner.value
    )
    assert [field.name for field in fields(output)] == ["value", "unit"]
    assert Unit.__slots__ == ("_handle",)


@pytest.mark.parametrize("operation", _COPY)
@pytest.mark.parametrize("kind", ("linear", "point", "difference"))
def test_raw_unit_and_private_rational_handles_are_independent_native_objects(
    *, operation: str, kind: str
) -> None:
    unit = _unit(kind)
    output = _COPY[operation](unit._handle)
    assert type(output) is _native._QuantityUnit
    assert output is not unit._handle
    assert output.to_json() == unit.to_json()
    exact = Rational.create(numerator=2**20000 + 1, denominator=17).unwrap()
    copied = _COPY[operation](exact._handle)
    assert type(copied) is _native.Rational and copied is not exact._handle
    assert copied.as_integer_ratio() == exact.as_integer_ratio()


@pytest.mark.parametrize(
    "family", list(_families.values()), ids=lambda family: family.cls.__name__
)
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("json_wire", (False, True))
def test_all_33_families_and_seven_domains_preserve_public_dto_representation(
    *, family: Any, domain: Any, json_wire: bool
) -> None:
    owner = Quantity(value=_value(domain), unit=family.cls())
    output = (
        Quantity.from_json(owner.to_json().unwrap()).unwrap()
        if json_wire
        else Quantity.from_dict(owner.to_dict().unwrap()).unwrap()
    )
    assert type(output.value) is domain and _identity(output.value) == _identity(
        owner.value
    )
    assert type(output.unit) is family.cls
    assert vars(output.unit) == vars(owner.unit)
    assert {name: type(value) for name, value in vars(output.unit).items()} == {
        name: type(value) for name, value in vars(owner.unit).items()
    }
    assert output == owner and hash(output) == hash(owner)


def _constants() -> list[Any]:
    return [
        pytest.param(unit, id=f"{family.cls.__name__}.{name}")
        for family in _families.values()
        for name, unit in sorted(
            vars(importlib.import_module(family.cls.__module__)).items()
        )
        if name.isupper() and type(unit) is family.cls
    ]


@pytest.mark.parametrize("unit", _constants())
@pytest.mark.parametrize("json_wire", (False, True))
def test_all_223_constant_metadata_round_trip_without_claiming_rg008_math_is_fixed(
    *, unit: Any, json_wire: bool
) -> None:
    assert len(_constants()) == 223
    owner = Quantity(value=Fraction(1, 3), unit=unit)
    output = (
        Quantity.from_json(owner.to_json().unwrap()).unwrap()
        if json_wire
        else Quantity.from_dict(owner.to_dict().unwrap()).unwrap()
    )
    assert output == owner and type(output.unit) is type(unit)
    assert {name: type(value) for name, value in vars(output.unit).items()} == {
        name: type(value) for name, value in vars(unit).items()
    }
    if type(unit).__name__ == "Mass" and unit.symbol == "u":
        assert output.to_dict().unwrap()["unit"]["native"] is None
        failure = output.add(output)
        assert isinstance(failure, Failed)
        assert failure.error.code.name == "DATA_LOSS"


@pytest.mark.parametrize(
    "value",
    [
        2**20000 + 1,
        Fraction(2**20000 + 1, 17),
        Decimal("-0.0000"),
        Decimal("1.2300e9999"),
        PublicRational(2**20000 + 1, 17),
        Rational.create(numerator=2**20000 + 1, denominator=17).unwrap(),
        -0.0,
        math.ulp(0.0),
        Floating(-0.0),
        Floating(2**20000 + 1),
        True,
    ],
    ids=[
        "big-int",
        "big-fraction",
        "decimal-zero",
        "decimal-scale",
        "big-public-rational",
        "big-native-rational",
        "negative-zero",
        "subnormal",
        "floating-zero",
        "floating-int",
        "bool",
    ],
)
@pytest.mark.parametrize("kind", ("linear", "point", "difference"))
def test_extreme_values_keep_exact_domain_sign_and_decimal_scale(
    *, value: Any, kind: str
) -> None:
    unit = _unit(kind)
    owner = Quantity(value=value, unit=unit)
    with localcontext(Context(prec=1)):
        text = owner.to_json().unwrap()
        output = Quantity.from_json(text).unwrap()
    assert type(output.value) is type(value) and _identity(output.value) == _identity(
        value
    )
    assert output.unit.descriptor() == unit.descriptor()
    assert output.unit.is_affine == unit.is_affine


def test_copy_graph_memo_asdict_subclass_hash_and_frozen_fields() -> None:
    unit = _unit("difference")
    exact = Rational.create(numerator=1, denominator=3).unwrap()
    owner = Quantity(value=exact, unit=unit)
    graph: list[Any] = [owner, owner, unit, exact]
    graph.append(graph)
    operations: tuple[Callable[[Any], Any], ...] = (
        copy.deepcopy,
        _pickle_copy(pickle.HIGHEST_PROTOCOL),
    )
    for operation in operations:
        output = operation(graph)
        assert (
            output[0] is output[1]
            and output[0].unit is output[2]
            and output[0].value is output[3]
        )
        assert output[4] is output
        assert output[0].unit.descriptor() == unit.descriptor()
        assert hash(output[0].value) == hash(exact)
    data = asdict(owner)
    assert type(data["unit"]["_handle"]) is _native._QuantityUnit
    assert type(data["value"]["_handle"]) is _native.Rational
    # asdict 是 Python 对象图，不谎称其为可互操作的纯 JSON DTO。
    # asdict is a Python object graph, not an interoperable pure JSON DTO.
    assert set(owner.to_dict().unwrap()) == {"schema", "version", "value", "unit"}

    class Derived(Quantity[Any]):
        pass

    derived = Derived(value=Fraction(3), unit=unit)
    assert type(copy.deepcopy(derived)) is Derived
    assert type(Derived.from_dict(derived.to_dict().unwrap()).unwrap()) is Derived
    assert unit != Unit.from_json(unit.to_json()).unwrap()


@pytest.mark.parametrize("operation", ("add", "subtract", "multiply", "divide"))
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("copy_operation", _COPY)
def test_native_arithmetic_outputs_support_copy_deepcopy_and_all_pickle_protocols(
    *, operation: str, domain: Any, copy_operation: str
) -> None:
    linear = _unit("linear")
    value = _value(domain, 10)
    if operation == "add":
        result = (
            Quantity(value=value, unit=linear)
            .add(Quantity(value=value, unit=linear))
            .unwrap()
        )
    elif operation == "subtract":
        result = (
            Quantity(value=value, unit=linear)
            .subtract(Quantity(value=value, unit=linear))
            .unwrap()
        )
    elif operation == "multiply":
        result = Quantity(value=value, unit=linear).multiply(2).unwrap()
    else:
        result = Quantity(value=value, unit=linear).divide(2).unwrap()

    output = _COPY[copy_operation](result)
    assert type(output) is Quantity and type(output.value) is domain
    assert _identity(output.value) == _identity(result.value)
    assert output.unit.descriptor() == result.unit.descriptor()
    assert output.to_json().unwrap() == result.to_json().unwrap()
    assert output.unit.is_affine is False
    assert (
        Quantity(value=output.value, unit=output.unit)
        .to(result.unit)
        .unwrap()
        .value
        == result.value
    )


class _Adapter(SnapshotAdapter[Any]):
    def __init__(self) -> None:
        self.events: list[Any] = []

    def to_snapshot(self, value: Any) -> Result[Any, Any, Any]:
        self.events.append(("encode", value))
        return Ok({"payload": value})

    def from_snapshot(self, snapshot: Any) -> Result[Any, Any, Any]:
        self.events.append(("decode", snapshot))
        return Ok(snapshot["payload"])


def test_explicit_adapters_preserve_arbitrary_value_and_unit_data_without_float_or_import() -> (
    None
):
    value = {"nested": [None, True, "value", -0.0]}
    unit: Any = {"dimension-proof": False, "label": "opaque"}
    value_adapter, unit_adapter = _Adapter(), _Adapter()
    owner: Any = Quantity(value=value, unit=unit)
    wire = owner.to_dict(
        value_adapter=value_adapter, unit_adapter=unit_adapter
    ).unwrap()
    output = Quantity.from_dict(
        wire, value_adapter=value_adapter, unit_adapter=unit_adapter
    ).unwrap()
    assert output.value == value and output.unit == unit
    assert len(value_adapter.events) == len(unit_adapter.events) == 2
    assert output.value is not value and output.unit is not unit
    wire["value"]["data"]["payload"]["nested"].append("later")
    assert output.value == value
    assert isinstance(Quantity.from_dict(wire), Failed)
    assert isinstance(owner.to_dict(), Failed)


@pytest.mark.parametrize(
    "stage", ("encode-value", "decode-value", "encode-unit", "decode-unit", "factory")
)
@pytest.mark.parametrize("error_type", (RuntimeError, KeyboardInterrupt, SystemExit))
def test_adapter_and_factory_exception_identity_and_base_exception_policy(
    *, stage: str, error_type: Any
) -> None:
    error = error_type("original snapshot callback")

    class Broken(_Adapter):
        def to_snapshot(self, value: Any) -> Result[Any, Any, Any]:
            raise error

        def from_snapshot(self, snapshot: Any) -> Result[Any, Any, Any]:
            raise error

    class Factory(Quantity[Any]):
        def __init__(self, **kwargs: Any) -> None:
            raise error

    owner = Quantity(value=7, unit=METER)
    adapter = _Adapter()
    wire = owner.to_dict(value_adapter=adapter).unwrap()
    wire["unit"] = {"kind": "custom", "data": {"payload": "unit"}}
    call: Callable[[], Any] = {
        "encode-value": lambda: owner.to_dict(value_adapter=Broken()),
        "decode-value": lambda: Quantity.from_dict(
            wire, value_adapter=Broken(), unit_adapter=adapter
        ),
        "encode-unit": lambda: owner.to_dict(unit_adapter=Broken()),
        "decode-unit": lambda: Quantity.from_dict(
            wire, value_adapter=adapter, unit_adapter=Broken()
        ),
        "factory": lambda: Factory.from_dict(owner.to_dict().unwrap()),
    }[stage]
    if issubclass(error_type, Exception):
        result = call()
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
    else:
        with pytest.raises(error_type) as caught:
            call()
        assert caught.value is error


def test_adapter_failed_result_is_retained_and_non_json_payload_is_rejected() -> None:
    failure: Result[Any, Any, Any] = Failed("original failure")

    class Adapter(_Adapter):
        def to_snapshot(self, value: Any) -> Result[Any, Any, Any]:
            return failure

    result = Quantity(value=1, unit=METER).to_dict(value_adapter=Adapter())
    assert isinstance(result, Failed) and result.error.value.callback_result is failure
    for payload in (object(), (1, 2), {1: "key"}, float("nan"), [float("inf")]):
        assert isinstance(
            Quantity(value=payload, unit=METER).to_dict(value_adapter=_Adapter()),
            Failed,
        )
    cycle: list[Any] = []
    cycle.append(cycle)
    assert isinstance(
        Quantity(value=cycle, unit=METER).to_dict(value_adapter=_Adapter()), Failed
    )


def test_unit_snapshot_precedes_value_callbacks_and_input_dto_is_detached() -> None:
    unit = Length("m", 2)

    class Mutate(_Adapter):
        def to_snapshot(self, value: Any) -> Result[Any, Any, Any]:
            object.__setattr__(unit, "_factor", 1000)
            return Ok(value)

        def from_snapshot(self, snapshot: Any) -> Result[Any, Any, Any]:
            return Ok(snapshot)

    wire = Quantity(value=7, unit=unit).to_dict(value_adapter=Mutate()).unwrap()
    output = Quantity.from_dict(wire, value_adapter=Mutate()).unwrap()
    assert output.unit._factor == 2 and output.value == 7

    class MutateInput(_Adapter):
        def from_snapshot(self, snapshot: Any) -> Result[Any, Any, Any]:
            wire["value"]["data"] = "changed after capture"
            return Ok(snapshot)

    output = Quantity.from_dict(wire, value_adapter=MutateInput()).unwrap()
    assert output.value == 7


@pytest.mark.parametrize(
    "mutation",
    (
        "version",
        "bool-version",
        "schema",
        "extra",
        "value-kind",
        "unit-family",
        "unit-factor",
        "unit-native",
        "unit-fields",
        "unit-null",
        "unit-symbol",
    ),
)
def test_strict_schema_refuses_metadata_conflicts_and_unregistered_class_imports(
    mutation: str,
) -> None:
    wire = Quantity(value=7, unit=METER).to_dict().unwrap()
    if mutation == "version":
        wire["version"] = 2
    elif mutation == "bool-version":
        wire["version"] = True
    elif mutation == "schema":
        wire["schema"] = "other"
    elif mutation == "extra":
        wire["extra"] = None
    elif mutation == "value-kind":
        wire["value"]["kind"] = "unknown"
    elif mutation == "unit-family":
        wire["unit"]["family"] = "os:system"
    elif mutation == "unit-factor":
        wire["unit"]["fields"]["_factor"] = {"kind": "int", "data": "0x2"}
    elif mutation == "unit-native":
        wire["unit"]["native"] = "{}"
    elif mutation == "unit-null":
        wire["unit"]["native"] = None
    elif mutation == "unit-symbol":
        wire["unit"]["fields"]["_symbol"] = "different label"
    else:
        wire["unit"]["fields"]["extra"] = None
    assert isinstance(Quantity.from_dict(wire), Failed)


@pytest.mark.parametrize(
    "text",
    (
        "{}",
        '{"schema":"ospf.quantity","schema":"other"}',
        "NaN",
        "null",
        "[]",
        "{bad",
        '"value"',
    ),
)
def test_invalid_json_remains_result_without_escaping_or_guessing(text: str) -> None:
    assert isinstance(Quantity.from_json(text), Failed)


def test_private_pickle_restore_rejects_corrupt_metadata_but_public_json_remains_result() -> (
    None
):
    for restore in (_native._restore_rational, _native._restore_quantity_unit):
        for text in ("{}", "null", '{"schema":"unknown","version":1}'):
            with pytest.raises(ValueError):
                restore(text)
    assert isinstance(Unit.from_json("{}"), Failed)
    assert isinstance(Rational.from_json("{}"), Failed)


def test_restored_difference_continues_checked_arithmetic_ranges_and_releases_callbacks() -> (
    None
):
    owner = Quantity(value=Fraction(60), unit=_unit("difference"))
    assert isinstance(owner.unit, Unit)
    expected_descriptor = owner.unit.descriptor()
    for output in (
        copy.deepcopy(owner),
        pickle.loads(pickle.dumps(owner)),
        Quantity.from_json(owner.to_json().unwrap()).unwrap(),
    ):
        assert isinstance(output.unit, Unit)
        assert not output.unit.is_affine
        doubled = output.multiply(Fraction(2)).unwrap()
        assert doubled.value == 120
        assert (
            QuantityValueRange(min_qty=owner, max_qty=owner).contains(output).unwrap()
        )
        assert isinstance(output.to(CELSIUS), Failed)
    adapter = _Adapter()
    reference = weakref.ref(adapter)
    assert Quantity(value=7, unit=owner.unit).to_json(value_adapter=adapter).is_ok()
    del adapter
    gc.collect()
    assert reference() is None

    def round_trip(_: int) -> Any:
        return Quantity.from_json(owner.to_json().unwrap()).unwrap().unit.descriptor()

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(
            item == expected_descriptor for item in pool.map(round_trip, range(32))
        )


@pytest.mark.parametrize(
    "module",
    (
        "ospf_python._binding.quantity_snapshot",
        "ospf_python._binding.quantity_arithmetic",
        "ospf_python._binding.quantity_conversion",
        "ospf_python._binding.unit_conversion",
        "ospf_python.quantities",
    ),
)
def test_cold_import_orders_and_snapshot_round_trip_in_fresh_isolated_process(
    module: str,
) -> None:
    code = """
import importlib,os,sys
handles=[os.add_dll_directory(path) for path in os.environ.get('OSPF_NATIVE_DLL_DIRS','').split(os.pathsep) if path] if os.name=='nt' else []
importlib.import_module(sys.argv[1])
from ospf_python.quantities import Quantity
from ospf_python.quantities.unit.temperature import CELSIUS
q=Quantity(value=80,unit=CELSIUS).subtract(Quantity(value=20,unit=CELSIUS)).unwrap()
r=Quantity.from_json(q.to_json().unwrap()).unwrap()
assert r.value==60 and r.unit.descriptor()==q.unit.descriptor() and not r.unit.is_affine
"""
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, module],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_explicit_adapter_none_outputs_and_reentrant_calls_are_not_failure_sentinels() -> (
    None
):
    class Adapter(_Adapter):
        def to_snapshot(self, value: Any) -> Result[Any, Any, Any]:
            nested = Quantity(value=Fraction(1, 3), unit=METER)
            assert Quantity.from_json(nested.to_json().unwrap()).unwrap() == nested
            return Ok(None)

        def from_snapshot(self, snapshot: Any) -> Result[Any, Any, Any]:
            assert snapshot is None
            return Ok(None)

    owner = Quantity(value=object(), unit=METER)
    output = Quantity.from_dict(
        owner.to_dict(value_adapter=Adapter()).unwrap(), value_adapter=Adapter()
    ).unwrap()
    assert output.value is None and output.unit == METER


@pytest.mark.parametrize(
    "scale", (Decimal("1e-400"), Decimal("-1.2300e500"), Decimal((0, (1,) * 6001, -1)))
)
def test_extreme_native_coefficients_are_snapshots_not_decimal_context_math(
    scale: Decimal,
) -> None:
    created = Unit.create(
        name="wide",
        symbol="W",
        powers=(1, -2, 3, -4, 5, -6, 7, -8, 9, -10),
        scale=scale,
        offset=Decimal("0.000"),
    )
    if isinstance(created, Failed):
        assert len(scale.as_tuple().digits) == 6001
        assert created.error.code.name == "DATA_LOSS"
        coefficient: Any = scale
        original = Length("wide", coefficient)
        owner = Quantity(value=Fraction(1, 3), unit=original)
        wire = owner.to_dict().unwrap()
        assert wire["unit"]["native"] is None
        restored = Quantity.from_json(owner.to_json().unwrap()).unwrap()
        assert (
            restored == owner and restored.unit._factor.as_tuple() == scale.as_tuple()
        )
        assert restored.add(restored).is_failed()
        return
    unit = created.unwrap()
    assert len(scale.as_tuple().digits) < 6001
    owner = Quantity(value=Fraction(1, 3), unit=unit)
    with localcontext(Context(prec=1)):
        restored = Quantity.from_json(owner.to_json().unwrap()).unwrap()
    assert restored.unit.descriptor() == unit.descriptor() and restored.unit.is_affine
    assert restored.value == owner.value
