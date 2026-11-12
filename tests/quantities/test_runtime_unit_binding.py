"""原生输出单位参与公开数量消费链路。 / Native output units participate in public quantity consumers."""

from __future__ import annotations

import copy
import gc
import importlib
import pickle
import weakref
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Context, Decimal
from fractions import Fraction
from types import SimpleNamespace
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.unit_registry import _families, native_family
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import (
    NumericAdapter,
    Quantity,
    QuantityValueRange,
    max_quantity,
    min_quantity,
    to_timedelta,
)
from ospf_python.quantities import unit as unit_package
from ospf_python.quantities.unit.physical_unit import PhysicalUnit
from ospf_python.quantities.unit.temperature import KELVIN
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result

_TEMPERATURE = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
_TIME = (0, 0, 1, 0, 0, 0, 0, 0, 0, 0)
_DOMAINS = (int, Fraction, Decimal, Rational, PublicRational, float, Floating)


def _fraction(value: Any) -> Fraction:
    if type(value) is Rational:
        return Fraction(*value.as_integer_ratio())
    if type(value) is PublicRational:
        return Fraction(value.numerator, value.denominator)
    if type(value) is Floating:
        return Fraction(value.value)
    return Fraction(value)


def _constants() -> list[Any]:
    return [
        pytest.param(unit, id=f"{family.cls.__name__}.{name}")
        for family in _families.values()
        for name, unit in sorted(
            vars(importlib.import_module(family.cls.__module__)).items()
        )
        if name.isupper() and type(unit) is family.cls
    ]


def test_public_exports_are_the_same_single_handle_unit() -> None:
    import ospf_python.quantities as quantities

    assert quantities.Unit is unit_package.Unit is Unit
    assert len(_families) == 33 and len(_constants()) == 223
    unit = Unit.create(name="seconds", symbol="s", powers=_TIME).unwrap()
    assert isinstance(unit, PhysicalUnit)
    assert Unit.__slots__ == ("_handle",)
    assert type(unit._handle) is _native._QuantityUnit


@pytest.mark.parametrize("kind", ("linear", "point", "difference"))
@pytest.mark.parametrize(
    "operation", ("copy", "deepcopy", *range(pickle.HIGHEST_PROTOCOL + 1))
)
def test_public_runtime_unit_supports_copy_deepcopy_and_all_pickle_protocols(
    *, kind: str, operation: str | int
) -> None:
    point = Unit.create(
        name="point", symbol="P", powers=_TEMPERATURE, scale=2, offset=5
    ).unwrap()
    if kind == "difference":
        _, unit = point.binary_exact(
            value=20, other=10, other_unit=point, subtract=True
        ).unwrap()
    else:
        unit = Unit.create(
            name=kind,
            symbol="P" if kind == "point" else "L",
            powers=_TEMPERATURE,
            scale=2,
            offset=5 if kind == "point" else None,
        ).unwrap()

    if operation == "copy":
        output = copy.copy(unit)
    elif operation == "deepcopy":
        output = copy.deepcopy(unit)
    else:
        assert isinstance(operation, int)
        output = pickle.loads(pickle.dumps(unit, protocol=operation))

    assert type(output) is Unit and output is not unit
    assert output != unit
    assert type(output._handle) is _native._QuantityUnit
    assert (output._handle is unit._handle) is (operation == "copy")
    assert output.descriptor() == unit.descriptor()
    assert output.to_json() == unit.to_json()
    assert output.powers == unit.powers
    assert output.is_affine is unit.is_affine
    assert unit_package.Unit is Unit


@pytest.mark.parametrize(
    "family", list(_families.values()), ids=lambda x: x.cls.__name__
)
@pytest.mark.parametrize("domain", _DOMAINS)
def test_every_family_and_domain_uses_public_conversion_consumers(
    *, family: Any, domain: Any
) -> None:
    source = Unit.create(
        name="runtime source",
        symbol="source",
        powers=family.powers,
        scale=2,
        offset=5 if family.affine else None,
    ).unwrap()
    value = Rational.from_value(7).unwrap() if domain is Rational else domain(7)
    quantity = Quantity(value=value, unit=source)
    target = family.cls()
    converted = quantity.to(target).unwrap()
    assert (
        _fraction(converted.value) == 19
        if family.affine
        else _fraction(converted.value) == 14
    )
    assert type(converted.value) is domain
    assert converted.unit is target
    assert _fraction(converted.to(source).unwrap().value) == 7
    standard = source.to_si(value).unwrap()
    assert _fraction(standard) == (19 if family.affine else 14)
    assert type(standard) is domain
    assert _fraction(source.from_si(standard).unwrap()) == 7
    assert source.symbol == "source" and source.name == "runtime source"
    assert source.powers == family.powers and source.is_affine is family.affine
    restored = Unit.from_json(source.to_json()).unwrap()
    assert restored.descriptor() == source.descriptor()
    assert quantity.to(restored).unwrap().value == value


@pytest.mark.parametrize("unit", _constants())
def test_all_223_constant_metadata_can_be_consumed_without_alias_guessing(
    unit: Any,
) -> None:
    family = _families[id(type(unit))]
    result = Unit.create(
        name="actual metadata",
        symbol=unit.symbol,
        powers=family.powers,
        scale=unit._factor,
        offset=unit._offset if family.affine else None,
    )
    if type(unit).__name__ == "Mass" and unit.symbol == "u":
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.DATA_LOSS
        return
    runtime = result.unwrap()
    value = Fraction(7, 3)
    forward = Quantity(value=value, unit=unit).to(runtime).unwrap()
    assert forward.value == value and forward.unit is runtime
    assert forward.to(unit).unwrap().value == value


@pytest.mark.parametrize("scale", (1, 2, 3))
@pytest.mark.parametrize("domain", (int, Fraction, Decimal, Rational, PublicRational))
def test_actual_native_point_subtraction_output_is_a_usable_linear_difference(
    *, scale: int, domain: Any
) -> None:
    point = Unit.create(
        name="point", symbol="P", powers=_TEMPERATURE, scale=scale, offset=5
    ).unwrap()
    value, difference = point.binary_exact(
        value=20, other=10, other_unit=point, subtract=True
    ).unwrap()
    assert type(difference) is Unit and difference.is_affine is False
    assert difference.symbol == "delta(P)"
    assert difference.descriptor()[4] is None
    raw = value if domain is Rational else domain(10)
    original = Quantity(value=raw, unit=difference)
    target = Unit.create(name="difference", symbol="dK", powers=_TEMPERATURE).unwrap()
    converted = original.to(target, context=Context(prec=60)).unwrap()
    assert _fraction(converted.value) == 10 * scale
    assert type(converted.value) is domain
    assert _fraction(converted.to(difference).unwrap().value) == 10
    assert min_quantity([original, converted]).unwrap() is original
    assert max_quantity([converted, original]).unwrap() is converted
    assert (
        QuantityValueRange(min_qty=original, max_qty=converted)
        .contains(original)
        .unwrap()
    )
    assert isinstance(to_timedelta(original), Failed)


@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("consumer", ("to", "min", "max", "range"))
def test_known_points_and_differences_cannot_be_silently_interchanged(
    *, reverse: bool, consumer: str
) -> None:
    difference = Unit.create(
        name="difference", symbol="dK", powers=_TEMPERATURE
    ).unwrap()
    left, right = Quantity(value=1, unit=KELVIN), Quantity(value=1, unit=difference)
    if reverse:
        left, right = right, left
    result = (
        left.to(right.unit)
        if consumer == "to"
        else min_quantity([left, right])
        if consumer == "min"
        else max_quantity([left, right])
        if consumer == "max"
        else QuantityValueRange(min_qty=left, max_qty=left).contains(right)
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_native_seconds_support_signed_exact_timedelta_and_reject_time_points() -> None:
    unit = Unit.create(
        name="time", symbol="custom time", powers=_TIME, scale=60
    ).unwrap()
    assert to_timedelta(
        Quantity(value=Fraction(-1, 3), unit=unit)
    ).unwrap() == timedelta(seconds=-20)
    point = Unit.create(name="epoch", symbol="t", powers=_TIME, offset=0).unwrap()
    assert isinstance(to_timedelta(Quantity(value=1, unit=point)), Failed)


def test_runtime_unit_callbacks_replaced_after_registration_remain_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unit = Unit.create(name="time", symbol="s", powers=_TIME).unwrap()
    marker = object()
    monkeypatch.setattr(Unit, "to_si", lambda self, value: marker)
    assert native_family(unit=unit, callback=unit.to_si, direction="source") is None
    target = SimpleNamespace(from_si=lambda value: value)
    assert Quantity(value=object(), unit=unit).to(target).unwrap().value is marker


@pytest.mark.parametrize("direction", ("source", "target"))
def test_runtime_handle_descriptor_replacement_is_not_speculatively_read(
    *, monkeypatch: pytest.MonkeyPatch, direction: str
) -> None:
    unit = Unit.create(name="time", symbol="s", powers=_TIME).unwrap()
    events: list[str] = []

    def getter(owner: Any) -> Any:
        events.append("handle")
        return object()

    monkeypatch.setattr(Unit, "_handle", property(getter))
    callback = unit.to_si if direction == "source" else unit.from_si
    assert native_family(unit=unit, callback=callback, direction=direction) is None
    assert events == []


def test_open_units_keep_result_as_opaque_data_without_false_native_provenance() -> (
    None
):
    marker: Any = Ok(object())
    unit = SimpleNamespace(to_si=lambda value: marker)
    target = SimpleNamespace(from_si=lambda value: value)
    assert Quantity(value=object(), unit=unit).to(target).unwrap().value is marker


def test_invalid_public_runtime_handle_is_a_result_failure() -> None:
    handle: Any = object()
    invalid = Unit(handle)
    result = Quantity(value=1, unit=invalid).to(invalid)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_public_runtime_units_reuse_explicit_numeric_adapter_without_double_export() -> (
    None
):
    events: list[str] = []

    class Adapter(NumericAdapter[Any]):
        def to_fraction(self, value: Any) -> Result[Fraction, Any, Any]:
            events.append("import")
            return Ok(Fraction(value[0]))

        def from_fraction(self, value: Fraction) -> Result[Any, Any, Any]:
            events.append("export")
            return Ok((value,))

    source = Unit.create(name="minutes", symbol="m", powers=_TIME, scale=60).unwrap()
    target = Unit.create(name="seconds", symbol="s", powers=_TIME).unwrap()
    output = (
        Quantity(value=(Fraction(1, 3),), unit=source)
        .to(target, numeric_adapter=Adapter())
        .unwrap()
    )
    assert output.value == (Fraction(20),)
    assert events == ["import", "export"]
    events.clear()
    assert to_timedelta(
        Quantity(value=(Fraction(1, 3),), unit=source), numeric_adapter=Adapter()
    ).unwrap() == timedelta(seconds=20)
    assert events == ["import"]


def test_runtime_unit_consumers_are_reentrant_thread_local_and_release_owners() -> None:
    source = Unit.create(name="minutes", symbol="m", powers=_TIME, scale=60).unwrap()
    target = Unit.create(name="seconds", symbol="s", powers=_TIME).unwrap()

    def consume(index: int) -> Fraction:
        value = (
            Quantity(value=Fraction(index, 7), unit=source).to(target).unwrap().value
        )
        assert isinstance(value, Fraction)
        return value

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(consume, range(40))) == [
            Fraction(60 * index, 7) for index in range(40)
        ]
    owner = Quantity(value=Fraction(1, 3), unit=source)
    reference = weakref.ref(owner)
    assert owner.to(target).unwrap().value == 20
    del owner
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("consumer", ("to", "min", "max", "range", "duration"))
def test_source_native_handle_is_snapshotted_before_adapter_import(
    consumer: str,
) -> None:
    source = Unit.create(name="minutes", symbol="m", powers=_TIME, scale=60).unwrap()
    replacement = Unit.create(name="seconds", symbol="s", powers=_TIME).unwrap()

    class Adapter(NumericAdapter[Any]):
        def to_fraction(self, value: Any) -> Result[Fraction, Any, Any]:
            if value == Fraction(1, 3):
                object.__setattr__(source, "_handle", replacement._handle)
            return Ok(Fraction(value))

        def from_fraction(self, value: Fraction) -> Result[Any, Any, Any]:
            return Ok(value)

    owner = Quantity(value=Fraction(1, 3), unit=source)
    if consumer == "to":
        assert owner.to(replacement, numeric_adapter=Adapter()).unwrap().value == 20
    elif consumer == "duration":
        assert to_timedelta(owner, numeric_adapter=Adapter()).unwrap() == timedelta(
            seconds=20
        )
    else:
        other = Quantity(value=Fraction(10), unit=replacement)
        if consumer == "min":
            assert (
                min_quantity([owner, other], numeric_adapter=Adapter()).unwrap()
                is other
            )
        elif consumer == "max":
            assert (
                max_quantity([owner, other], numeric_adapter=Adapter()).unwrap()
                is owner
            )
        else:
            assert (
                not QuantityValueRange(
                    min_qty=Quantity(value=Fraction(0), unit=replacement), max_qty=other
                )
                .contains(owner, numeric_adapter=Adapter())
                .unwrap()
            )


def test_replaceable_native_module_alias_does_not_prove_a_fake_handle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class Fake:
        def descriptor(self) -> Any:
            events.append("fake metadata")
            return ("fake", "s", list(_TIME), (1, 0), None)

    monkeypatch.setattr(_native, "_QuantityUnit", Fake)
    bad: Any = Fake()
    unit = Unit(bad)
    assert isinstance(Quantity(value=1, unit=unit).to(unit), Failed)
    assert events == []


@pytest.mark.parametrize("error", (RuntimeError, KeyboardInterrupt))
@pytest.mark.parametrize("direct", (False, True))
def test_runtime_unit_direct_and_quantity_boundaries_preserve_original_errors(
    *, monkeypatch: pytest.MonkeyPatch, error: Any, direct: bool
) -> None:
    original = error()

    class Value:
        def __float__(self) -> float:
            raise AssertionError("no coercion")

    class Adapter(NumericAdapter[Any]):
        def to_fraction(self, value: Any) -> Result[Fraction, Any, Any]:
            raise original

        def from_fraction(self, value: Fraction) -> Result[Any, Any, Any]:
            pytest.fail("export after failure")

    source = Unit.create(name="seconds", symbol="s", powers=_TIME).unwrap()
    call: Callable[[], Any]
    if direct:

        def context_failure() -> Any:
            raise original

        monkeypatch.setattr(
            importlib.import_module("ospf_python._binding.numeric"),
            "getcontext",
            context_failure,
        )
        call = lambda: source.to_si(Decimal(1))
    else:
        call = lambda: Quantity(value=Value(), unit=source).to(
            source, numeric_adapter=Adapter()
        )
    if error is KeyboardInterrupt:
        with pytest.raises(KeyboardInterrupt) as caught:
            call()
        assert caught.value is original
    else:
        result = call()
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is original
        assert original.__traceback__ is not None


def test_point_difference_mismatch_is_not_lost_when_an_open_item_wins() -> None:
    point = Quantity(value=20, unit=KELVIN)
    opaque = Quantity(
        value=object(), unit=SimpleNamespace(to_si=lambda value: Fraction(-100))
    )
    difference = Unit.create(
        name="difference", symbol="dK", powers=_TEMPERATURE
    ).unwrap()
    items: list[Quantity[Any]] = [point, opaque, Quantity(value=10, unit=difference)]
    result = min_quantity(items)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_kelvin_zero_offset_remains_a_point_when_converted_to_a_native_unit() -> None:
    point = Unit.create(
        name="kelvin point", symbol="K", powers=_TEMPERATURE, offset=0
    ).unwrap()
    assert Quantity(value=10, unit=KELVIN).to(point).unwrap().value == 10
    assert point.is_affine and point.descriptor()[4] is not None
    assert isinstance(point.binary_exact(value=1, other=1, other_unit=point), Failed)


def test_mixed_affine_recurring_ratio_uses_exact_pinned_conversion() -> None:
    point = Unit.create(
        name="point", symbol="P", powers=_TEMPERATURE, scale=3, offset=1
    ).unwrap()
    difference = Unit.create(
        name="difference", symbol="dK", powers=_TEMPERATURE
    ).unwrap()
    result, output = point.binary_exact(
        value=0, other=1, other_unit=difference
    ).unwrap()
    assert _fraction(result) == Fraction(1, 3)
    assert output.descriptor() == point.descriptor()
