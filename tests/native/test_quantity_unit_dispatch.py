"""内置、开放及混合单位派发合同。 / Builtin, open and mixed unit-dispatch contracts."""

from __future__ import annotations

import builtins
import gc
import importlib
import os
import struct
import subprocess
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from decimal import Context, Decimal, Inexact, Rounded
from fractions import Fraction
from types import SimpleNamespace
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import BindingResult, invalid
from ospf_python._binding.unit_conversion import _Standard, convert_quantity
from ospf_python._binding.unit_registry import _families, native_family
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import unit as unit_package
from ospf_python.quantities.quantity import quantity as quantity_module
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import KILOMETER, METER, Length
from ospf_python.quantities.unit.mass import ATOMIC_MASS_UNIT, KILOGRAM
from ospf_python.quantities.unit.temperature import CELSIUS, KELVIN, Temperature
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok


def _constants() -> list[Any]:
    return [
        pytest.param(value, id=f"{family.cls.__name__}.{name}")
        for family in _families.values()
        for name, value in sorted(
            vars(importlib.import_module(family.cls.__module__)).items()
        )
        if name.isupper() and type(value) is family.cls
    ]


def _quantity(*, value: Any, unit: Any) -> Quantity[Any]:
    return Quantity(value=value, unit=unit)


def _fraction(value: Any) -> Fraction:
    if type(value) is Rational:
        return Fraction(*value.as_integer_ratio())
    if type(value) is PublicRational:
        return Fraction(value.numerator, value.denominator)
    return Fraction(value)


def test_definition_time_registry_has_all_33_families_and_223_constants() -> None:
    assert len(_families) == 33
    assert len(_constants()) == 223
    assert {family.cls for family in _families.values()} == {
        getattr(unit_package, family.cls.__name__) for family in _families.values()
    }
    for family in _families.values():
        unit = family.cls()
        assert (
            native_family(unit=unit, callback=unit.to_si, direction="source") is family
        )
        assert family.affine is (family.cls is Temperature)
        assert len(family.powers) == 10


@pytest.mark.parametrize("unit", _constants())
@pytest.mark.parametrize("domain", (int, Fraction, Decimal, Rational, PublicRational))
def test_all_registered_constants_use_exact_rust_and_preserve_domain(
    *, unit: Any, domain: Any
) -> None:
    value = Rational.create(numerator=7).unwrap() if domain is Rational else domain(7)
    result = convert_quantity(
        owner=_quantity(value=value, unit=unit),
        target=type(unit)(),
        context=Context(prec=400),
    )
    # RG-008 的防护不是消除缺口；旧八条公开切换门禁仍须真实失败。
    # The RG-008 guard does not resolve the gap; the eight existing switch gates remain red.
    if unit is ATOMIC_MASS_UNIT:
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.DATA_LOSS
        return
    converted = result.unwrap()
    expected = Fraction(7) * Fraction(unit._factor) + Fraction(
        getattr(unit, "_offset", 0)
    )
    assert _fraction(converted.value) == expected
    assert type(converted.value) is (
        Fraction if domain is int and expected.denominator != 1 else domain
    )
    assert type(converted.unit) is type(unit)


@pytest.mark.parametrize("unit", _constants())
@pytest.mark.parametrize("domain", (float, Floating))
def test_all_registered_constants_use_explicit_float64_lane(
    *, unit: Any, domain: Any
) -> None:
    target = type(unit)()
    result = convert_quantity(
        owner=_quantity(value=domain(1.25), unit=unit), target=target
    )
    family = _families[id(type(unit))]
    source = Unit.create(
        name="source",
        symbol="",
        powers=family.powers,
        scale=unit._factor,
        offset=getattr(unit, "_offset", None),
    )
    if isinstance(source, Failed):
        assert unit is ATOMIC_MASS_UNIT
        assert isinstance(result, Failed)
        assert result.error.code is source.error.code is ErrorCode.DATA_LOSS
        return
    standard = Unit.create(
        name="SI",
        symbol="",
        powers=family.powers,
        offset=0 if family.affine else None,
    ).unwrap()
    reference = source.unwrap().convert_float64(value=1.25, target=standard)
    if isinstance(reference, Failed):
        assert isinstance(result, Failed)
        assert result.error.code is reference.error.code
        assert unit is ATOMIC_MASS_UNIT
    else:
        output = result.unwrap().value
        assert type(output) is domain
        assert struct.pack(
            "!d", output.value if domain is Floating else output
        ) == struct.pack("!d", reference.unwrap())


@pytest.mark.parametrize("value", (1, Fraction(2, 3), Decimal("1.25"), 1.25))
def test_known_dimension_mismatch_is_rejected_before_factory(
    *, value: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        quantity_module, "Quantity", lambda **kw: pytest.fail("factory")
    )
    result = convert_quantity(owner=_quantity(value=value, unit=METER), target=KILOGRAM)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize("source,target", ((CELSIUS, KELVIN), (KELVIN, CELSIUS)))
def test_affine_points_keep_exact_binary_offsets(*, source: Any, target: Any) -> None:
    output = convert_quantity(
        owner=_quantity(value=0, unit=source), target=target
    ).unwrap()
    assert _fraction(output.value) == Fraction(source._offset) - Fraction(
        target._offset
    )


def test_decimal_is_not_exported_at_internal_si_boundary() -> None:
    unit = Length("third", 3)
    context = Context(prec=1)
    context.traps[Inexact] = True
    output = convert_quantity(
        owner=_quantity(value=Decimal("0.7"), unit=unit), target=unit, context=context
    ).unwrap()
    assert output.value == Decimal("0.7")
    assert not any(context.flags.values())


def test_decimal_export_exact_and_opt_in_rounding_use_original_context() -> None:
    owner = _quantity(value=Decimal(1), unit=METER)
    target = Length("third", 3)
    exact_context = Context(prec=4)
    failure = convert_quantity(owner=owner, target=target, context=exact_context)
    assert isinstance(failure, Failed)
    assert failure.error.code is ErrorCode.DATA_LOSS
    assert exact_context.flags[Inexact] and exact_context.flags[Rounded]
    context = Context(prec=4)
    assert convert_quantity(
        owner=owner, target=target, context=context, exact=False
    ).unwrap().value == Decimal("0.3333")
    assert context.flags[Inexact] and context.flags[Rounded]


@pytest.mark.parametrize("value", (True, object(), float("nan"), float("inf")))
def test_unsupported_or_nonfinite_native_values_fail_without_target_lookup(
    value: Any,
) -> None:
    class Target:
        @property
        def from_si(self) -> Any:
            pytest.fail("target lookup after source failure")

    assert convert_quantity(
        owner=_quantity(value=value, unit=METER), target=Target()
    ).is_failed()


def test_unknown_numeric_does_not_call_float_or_arithmetic() -> None:
    class Value:
        def __float__(self) -> float:
            pytest.fail("float")

        def __mul__(self, other: Any) -> Any:
            pytest.fail("old numeric kernel")

    result = convert_quantity(owner=_quantity(value=Value(), unit=METER), target=METER)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.NOT_SUPPORTED


@pytest.mark.parametrize("native_source", (True, False))
def test_unknown_numeric_metaclass_is_not_executed_during_domain_selection(
    native_source: bool,
) -> None:
    class Meta(type):
        def __eq__(cls, other: Any) -> bool:
            pytest.fail("unknown numeric metaclass equality")

        def __hash__(cls) -> int:
            pytest.fail("unknown numeric metaclass hash")

    class Value(metaclass=Meta):
        pass

    value = Value()
    source = METER if native_source else SimpleNamespace(to_si=lambda argument: value)
    result = convert_quantity(owner=_quantity(value=value, unit=source), target=METER)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.NOT_SUPPORTED


@pytest.mark.parametrize("payload", (2, 2**100 + 1, True, object()))
def test_floating_integer_bridge_is_lossless_not_arbitrary_coercion(
    payload: Any,
) -> None:
    result = convert_quantity(
        owner=_quantity(value=Floating(payload), unit=METER), target=METER
    )
    if type(payload) is int and payload == 2:
        assert result.unwrap().value.value == 2.0
        assert type(result.unwrap().value.value) is float
    else:
        assert isinstance(result, Failed)
        assert result.error.code is (
            ErrorCode.DATA_LOSS if type(payload) is int else ErrorCode.ILLEGAL_ARGUMENT
        )


def test_native_factor_is_read_after_value_and_never_uses_symbol() -> None:
    unit = Length("initial", 2)

    class Owner:
        @property
        def unit(self) -> Length:
            return unit

        @property
        def value(self) -> int:
            object.__setattr__(unit, "_factor", 3)
            return 7

    assert convert_quantity(owner=Owner(), target=METER).unwrap().value == 21


def test_symbol_descriptor_is_not_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Length, "symbol", property(lambda self: pytest.fail("symbol")))
    assert (
        convert_quantity(owner=_quantity(value=7, unit=KILOMETER), target=METER)
        .unwrap()
        .value
        == 7000
    )


def test_target_factor_and_method_are_late_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unit = Length("late", 2)

    class Source:
        def to_si(self, value: Any) -> Any:
            object.__setattr__(unit, "_factor", 4)
            return value

    assert (
        convert_quantity(owner=_quantity(value=8, unit=Source()), target=unit)
        .unwrap()
        .value
        == 2
    )
    monkeypatch.setattr(Length, "from_si", lambda self, value: ("custom", value))
    assert convert_quantity(
        owner=_quantity(value=3, unit=METER), target=unit
    ).unwrap().value == ("custom", 3)


def test_captured_original_method_survives_class_slot_replacement() -> None:
    original = Length.to_si
    unit_class: Any = Length

    class Owner:
        unit = KILOMETER

        @property
        def value(self) -> int:
            unit_class.to_si = lambda self, value: pytest.fail("late replacement")
            return 2

    try:
        assert convert_quantity(owner=Owner(), target=METER).unwrap().value == 2000
    finally:
        unit_class.to_si = original


def test_mutated_function_code_is_not_mistaken_for_original() -> None:
    function = Length.to_si
    original = function.__code__

    def replacement(self: Any, value: Any) -> Any:
        return value

    class Owner:
        unit = KILOMETER

        @property
        def value(self) -> object:
            function.__code__ = replacement.__code__
            return token

    token = object()

    class Target:
        def from_si(self, value: Any) -> Any:
            assert value is token
            return token

    try:
        assert convert_quantity(owner=Owner(), target=Target()).unwrap().value is token
    finally:
        function.__code__ = original


def test_dynamic_factor_descriptor_uses_one_real_callback_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = []

    def factor(self: Any) -> int:
        events.append("factor")
        return 5

    monkeypatch.setattr(Length, "_factor", property(factor))
    assert (
        convert_quantity(owner=_quantity(value=2, unit=METER), target=METER)
        .unwrap()
        .value
        == 2
    )
    assert events == ["factor", "factor"]


def test_field_becoming_dynamic_after_prepare_is_rechecked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = []

    def factor(self: Any) -> int:
        events.append("factor")
        return 5

    class Owner:
        unit = METER

        @property
        def value(self) -> int:
            monkeypatch.setattr(Length, "_factor", property(factor))
            return 2

    assert convert_quantity(owner=Owner(), target=METER).unwrap().value == 2
    assert events == ["factor", "factor"]


@pytest.mark.parametrize("metadata", (Decimal(1), Fraction(1, 3), None, object()))
def test_plain_class_field_metadata_does_not_select_legacy_arithmetic(
    *, metadata: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Length, "_factor", metadata)
    value = (1 << 100) + 1
    output = convert_quantity(
        owner=_quantity(value=value, unit=KILOMETER), target=METER
    ).unwrap()
    assert type(output.value) is int
    assert output.value == value * 1000


def test_class_field_metaclass_is_not_executed_by_descriptor_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Meta(type):
        def __getattribute__(cls, name: str) -> Any:
            pytest.fail("external metaclass lookup")

    class Metadata(metaclass=Meta):
        pass

    monkeypatch.setattr(Length, "_factor", Metadata())
    assert (
        convert_quantity(owner=_quantity(value=2, unit=KILOMETER), target=METER)
        .unwrap()
        .value
        == 2000
    )


def test_subclass_and_dynamic_getattribute_remain_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Custom(Length):
        def to_si(self, value: Any) -> Any:
            return value

    value = object()

    class Target:
        def from_si(self, value: Any) -> Any:
            return value

    assert (
        convert_quantity(owner=_quantity(value=value, unit=Custom()), target=Target())
        .unwrap()
        .value
        is value
    )
    original = object.__getattribute__
    events = []

    def getattribute(self: Any, name: str) -> Any:
        if name == "_factor":
            events.append(name)
        return original(self, name)

    monkeypatch.setattr(Length, "__getattribute__", getattribute)
    assert (
        convert_quantity(owner=_quantity(value=2, unit=METER), target=METER)
        .unwrap()
        .value
        == 2
    )
    assert events == ["_factor", "_factor"]


@pytest.mark.parametrize(
    "domain", (int, Fraction, Decimal, Rational, PublicRational, float, Floating)
)
def test_native_to_open_exports_domain_after_target_lookup(domain: Any) -> None:
    value = Rational.create(numerator=2).unwrap() if domain is Rational else domain(2)
    events = []

    class Target:
        @property
        def from_si(self) -> Any:
            events.append("method")

            def call(value: Any) -> Any:
                assert events == ["method"]
                assert type(value) is domain
                assert _fraction(value.value if domain is Floating else value) == 2000
                return token

            return call

    token = object()
    assert (
        convert_quantity(owner=_quantity(value=value, unit=KILOMETER), target=Target())
        .unwrap()
        .value
        is token
    )


@pytest.mark.parametrize(
    "domain", (int, Fraction, Decimal, Rational, PublicRational, float, Floating)
)
def test_open_to_native_imports_explicit_target_si_domain(domain: Any) -> None:
    value = (
        Rational.create(numerator=2000).unwrap() if domain is Rational else domain(2000)
    )

    class Source:
        def to_si(self, argument: Any) -> Any:
            assert argument is token
            return value

    token = object()
    output = (
        convert_quantity(owner=_quantity(value=token, unit=Source()), target=KILOMETER)
        .unwrap()
        .value
    )
    assert type(output) is domain
    assert _fraction(output.value if domain is Floating else output) == 2


@pytest.mark.parametrize(
    "value", (None, object(), Ok(7), Failed(Err(ErrorCode.APPLICATION_ERROR, "data")))
)
def test_open_values_and_result_as_data_are_not_unwrapped(value: Any) -> None:
    class Unit:
        def to_si(self, item: Any) -> Any:
            assert item is value
            return item

        def from_si(self, item: Any) -> Any:
            assert item is value
            return item

    unit = Unit()
    assert (
        convert_quantity(owner=_quantity(value=value, unit=unit), target=unit)
        .unwrap()
        .value
        is value
    )


def test_external_marker_shaped_data_is_not_a_call_scoped_si_token() -> None:
    value = _Standard(
        Rational.create(numerator=7).unwrap(),
        Unit.create(
            name="fake", symbol="", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        ).unwrap(),
        Rational,
    )
    unit = SimpleNamespace(
        to_si=lambda argument: argument, from_si=lambda argument: argument
    )
    assert (
        convert_quantity(owner=_quantity(value=value, unit=unit), target=unit)
        .unwrap()
        .value
        is value
    )
    failure = convert_quantity(owner=_quantity(value=value, unit=unit), target=METER)
    assert isinstance(failure, Failed)
    assert failure.error.code is ErrorCode.NOT_SUPPORTED


@pytest.mark.parametrize(
    "phase", ("unit", "source", "value", "target", "target-call", "factory")
)
@pytest.mark.parametrize(
    "error_type", (ValueError, TypeError, KeyboardInterrupt, SystemExit, GeneratorExit)
)
def test_external_exceptions_and_interrupts_preserve_identity(
    *, phase: str, error_type: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = error_type("original")

    class Source:
        @property
        def to_si(self) -> Any:
            if phase == "source":
                raise error
            return lambda value: value

    class Owner:
        @property
        def unit(self) -> Any:
            if phase == "unit":
                raise error
            return Source()

        @property
        def value(self) -> int:
            if phase == "value":
                raise error
            return 1

    class Target:
        @property
        def from_si(self) -> Any:
            if phase == "target":
                raise error

            def call(value: Any) -> Any:
                if phase == "target-call":
                    raise error
                return value

            return call

    def factory(**kwargs: Any) -> Any:
        if phase == "factory":
            raise error
        return kwargs

    monkeypatch.setattr(quantity_module, "Quantity", factory)
    if issubclass(error_type, Exception):
        result = convert_quantity(owner=Owner(), target=Target())
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
        assert error.__traceback__ is not None
    else:
        with pytest.raises(error_type) as caught:
            convert_quantity(owner=Owner(), target=Target())
        assert caught.value is error


def test_typed_failure_retains_original_result_and_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure: BindingResult[Any] = invalid("sentinel")
    monkeypatch.setattr(Unit, "convert_exact", lambda *args, **kwargs: failure)

    class Target:
        @property
        def from_si(self) -> Any:
            pytest.fail("target after source failure")

    assert (
        convert_quantity(owner=_quantity(value=1, unit=METER), target=Target())
        is failure
    )


def test_target_typed_failure_retains_identity_and_stops_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure: BindingResult[Any] = invalid("target sentinel")
    original = Unit.convert_exact
    calls = []

    def convert(self: Unit, *, value: Any, target: Unit) -> BindingResult[Any]:
        calls.append(self)
        if len(calls) == 2:
            return failure
        return original(self, value=value, target=target)

    monkeypatch.setattr(Unit, "convert_exact", convert)
    monkeypatch.setattr(
        quantity_module, "Quantity", lambda **kwargs: pytest.fail("factory")
    )
    assert (
        convert_quantity(owner=_quantity(value=1, unit=METER), target=METER) is failure
    )
    assert len(calls) == 2


@pytest.mark.parametrize("output", (None, object(), Ok(7)))
def test_factory_output_is_opaque_and_late(
    output: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Target:
        def from_si(self, value: Any) -> Any:
            monkeypatch.setattr(quantity_module, "Quantity", lambda **kwargs: output)
            return value

    assert (
        convert_quantity(owner=_quantity(value=1, unit=METER), target=Target()).unwrap()
        is output
    )


def test_factory_uses_builtins_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(quantity_module, "Quantity")
    monkeypatch.setattr(builtins, "Quantity", lambda **kwargs: kwargs, raising=False)
    assert convert_quantity(
        owner=_quantity(value=1, unit=METER), target=METER
    ).unwrap() == dict(value=1, unit=METER)


def test_no_call_scoped_unit_or_value_is_cached() -> None:
    source = Length("temporary", 2)
    value = PublicRational(7)
    source_ref, value_ref = weakref.ref(source), weakref.ref(value)
    result = convert_quantity(owner=_quantity(value=value, unit=source), target=METER)
    assert result.unwrap().value == PublicRational(14)
    del source, value
    gc.collect()
    assert source_ref() is None and value_ref() is None


def test_opaque_temporary_source_is_not_retained_by_preparation() -> None:
    events = []

    class Source:
        to_si = staticmethod(lambda value: value)

        def __del__(self) -> None:
            events.append("source-drop")

    class Owner:
        @property
        def unit(self) -> Source:
            return Source()

        @property
        def value(self) -> int:
            assert events == ["source-drop"]
            return 7

    assert convert_quantity(owner=Owner(), target=METER).unwrap().value == 7


def test_exported_si_snapshot_lives_through_factory_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = []
    token = object()

    class Target:
        def from_si(self, value: Any) -> Any:
            observed.append(weakref.ref(value))
            return token

    def factory(**kwargs: Any) -> Any:
        assert observed[0]() == PublicRational(7000)
        assert kwargs["value"] is token
        return token

    monkeypatch.setattr(quantity_module, "Quantity", factory)
    assert (
        convert_quantity(
            owner=_quantity(value=PublicRational(7), unit=KILOMETER), target=Target()
        ).unwrap()
        is token
    )
    gc.collect()
    assert observed[0]() is None


def test_malicious_exception_class_and_formatting_are_not_read() -> None:
    def forbidden(self: Any) -> Any:
        pytest.fail("exception class property or formatting")

    hostile = type(
        "Hostile",
        (Exception,),
        {"__class__": property(forbidden), "__str__": forbidden},
    )
    error = hostile()

    class Source:
        def to_si(self, value: Any) -> Any:
            raise error

    result = convert_quantity(owner=_quantity(value=1, unit=Source()), target=METER)
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error


def test_reentrant_and_threaded_dispatch_has_no_shared_state() -> None:
    class Source:
        def to_si(self, value: int) -> Any:
            return (
                convert_quantity(
                    owner=_quantity(value=value, unit=KILOMETER), target=METER
                )
                .unwrap()
                .value
            )

    def run(value: int) -> Any:
        return (
            convert_quantity(
                owner=_quantity(value=value, unit=Source()), target=KILOMETER
            )
            .unwrap()
            .value
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(run, range(32))) == list(range(32))


def test_monkeypatch_before_private_dispatch_import_remains_open() -> None:
    script = """
import os
handles=[os.add_dll_directory(path) for path in os.environ.get('OSPF_NATIVE_DLL_DIRS','').split(os.pathsep) if path] if os.name=='nt' else []
from ospf_python.quantities.unit.length import Length, KILOMETER
Length.to_si = lambda self, value: value
from ospf_python._binding.unit_conversion import convert_quantity
from types import SimpleNamespace
token = object()
target = SimpleNamespace(from_si=lambda value: value)
assert convert_quantity(owner=SimpleNamespace(unit=KILOMETER, value=token), target=target).unwrap().value is token
"""
    process = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    assert process.returncode == 0, process.stderr


@pytest.mark.parametrize("stage", ("source", "target"))
def test_native_prepare_failure_preserves_phase(stage: str) -> None:
    error = ValueError("prepare")

    def prepare(unit: Any, callback: Any, direction: str) -> Any:
        if direction == stage:
            raise error
        return callback, False

    unit = SimpleNamespace(to_si=lambda value: value, from_si=lambda value: value)
    complete, output, failure = _native._convert_quantity_dispatched(
        owner=SimpleNamespace(unit=unit, value=1),
        target=unit,
        namespace={"Quantity": lambda **kwargs: kwargs},
        builtins={},
        prepare=prepare,
    )
    assert complete is False and output is None
    assert failure == (f"{stage}-prepare", error)
