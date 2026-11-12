"""公开时长 Result 与固定 Rust 单位换算合同。 / Public duration Result and pinned-unit contracts."""

from __future__ import annotations

import builtins
import gc
import importlib
import math
import subprocess
import sys
import weakref
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, Inexact, localcontext
from fractions import Fraction
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python._binding import quantity_duration as _duration
from ospf_python._binding import unit_conversion as _conversion
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.unit_registry import _families, native_family
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import (
    NumericAdapter,
    Quantity,
    from_hours,
    from_minutes,
    to_timedelta,
)
from ospf_python.quantities.unit.time_unit import SECOND, TimeUnit
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from collections.abc import Callable

_module = importlib.import_module("ospf_python.quantities.quantity.duration_extensions")
_DOMAINS = (
    "int",
    "float",
    "fraction",
    "decimal",
    "private",
    "public",
    "floating",
    "custom",
)


@dataclass(frozen=True)
class _Value:
    value: Fraction


class _Adapter(NumericAdapter[_Value]):
    def __init__(self) -> None:
        self.events: list[str] = []

    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        self.events.append("import")
        return Ok(value.value)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        self.events.append("export")
        return Ok(_Value(value))


def _value(domain: str) -> Any:
    factories: dict[str, Callable[[], Any]] = {
        "int": lambda: 1,
        "float": lambda: 0.25,
        "fraction": lambda: Fraction(1, 4),
        "decimal": lambda: Decimal("0.25"),
        "private": lambda: Rational.create(numerator=1, denominator=4).unwrap(),
        "public": lambda: PublicRational(1, 4),
        "floating": lambda: Floating(0.25),
        "custom": lambda: _Value(Fraction(1, 4)),
    }
    return factories[domain]()


def _fraction(value: Any) -> Fraction:
    if type(value) is _Value:
        return value.value
    if type(value) is Floating:
        return Fraction(value.value)
    if type(value) is Rational:
        return Fraction(*value.as_integer_ratio())
    if type(value) is PublicRational:
        return Fraction(value.numerator, value.denominator)
    return Fraction(value)


@pytest.mark.parametrize("constructor,factor", ((from_hours, 3600), (from_minutes, 60)))
@pytest.mark.parametrize("domain", _DOMAINS)
def test_constructors_use_native_domains_and_explicit_result(
    *, constructor: Any, factor: int, domain: str
) -> None:
    adapter = _Adapter()
    value = _value(domain)
    result = constructor(value, numeric_adapter=adapter if domain == "custom" else None)
    output = result.unwrap()
    assert output.unit is SECOND and type(output.value) is type(value)
    assert _fraction(output.value) == _fraction(value) * factor
    assert adapter.events == (["import", "export"] if domain == "custom" else [])


_TIME_CONSTANTS = [
    value
    for name, value in vars(importlib.import_module(TimeUnit.__module__)).items()
    if name.isupper() and type(value) is TimeUnit
]


@pytest.mark.parametrize("unit", _TIME_CONSTANTS, ids=lambda unit: unit.symbol)
@pytest.mark.parametrize("domain", _DOMAINS)
def test_all_nine_time_constants_and_eight_domains(
    *, unit: TimeUnit, domain: str
) -> None:
    assert len(_TIME_CONSTANTS) == 9
    value = _value(domain)
    adapter = _Adapter()
    output = to_timedelta(
        Quantity(value=value, unit=unit),
        numeric_adapter=adapter if domain == "custom" else None,
    ).unwrap()
    expected = (
        timedelta(seconds=0.25 * unit._factor)
        if domain in ("float", "floating")
        else timedelta(
            microseconds=round(_fraction(value) * Fraction(unit._factor) * 1000000)
        )
    )
    assert type(output) is timedelta and output == expected
    assert adapter.events == (["import"] if domain == "custom" else [])


@pytest.mark.parametrize(
    "family",
    [family for family in _families.values() if family.cls is not TimeUnit],
    ids=lambda family: family.cls.__name__,
)
@pytest.mark.parametrize("domain", _DOMAINS)
def test_all_known_nontime_families_are_rejected(*, family: Any, domain: str) -> None:
    result = to_timedelta(
        Quantity(value=_value(domain), unit=family.cls()),
        numeric_adapter=_Adapter() if domain == "custom" else None,
    )
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )


@pytest.mark.parametrize("sign", (-1, 1))
@pytest.mark.parametrize("numerator", (1, 3, 5, 7))
@pytest.mark.parametrize("epsilon", (-1, 0, 1))
def test_exact_submicrosecond_ties_and_neighbors(
    *, sign: int, numerator: int, epsilon: int
) -> None:
    value = sign * (Fraction(numerator, 2000000) + Fraction(epsilon, 10**100))
    assert to_timedelta(Quantity(value=value, unit=SECOND)).unwrap() == timedelta(
        microseconds=round(value * 1000000)
    )


@pytest.mark.parametrize(
    "value",
    [
        sign * value
        for sign in (-1, 1)
        for value in (
            0.0,
            0.5e-6,
            1.5e-6,
            2.5e-6,
            math.nextafter(2.5e-6, 0),
            math.nextafter(2.5e-6, math.inf),
            1.0000000000000002,
            86400.000001,
        )
    ],
)
def test_float_si_uses_cpython_not_exact_binary_fraction_rounding(value: float) -> None:
    assert to_timedelta(Quantity(value=value, unit=SECOND)).unwrap() == timedelta(
        seconds=value
    )


def test_full_asymmetric_range_and_exact_large_seconds() -> None:
    maximum = Fraction(1000000000 * 86400) - Fraction(1, 1000000)
    minimum = Fraction(-999999999 * 86400)
    for value, expected in ((maximum, timedelta.max), (minimum, timedelta.min)):
        assert to_timedelta(Quantity(value=value, unit=SECOND)).unwrap() == expected
    for overflow_value in (
        maximum + Fraction(1, 1000000),
        minimum - Fraction(1, 1000000),
        10**1000,
    ):
        result = to_timedelta(Quantity(value=overflow_value, unit=SECOND))
        assert isinstance(result, Failed) and result.error.code is ErrorCode.OVERFLOW
    value = Fraction(999999999 * 86400) + Fraction(999999, 1000000)
    assert to_timedelta(Quantity(value=value, unit=SECOND)).unwrap() == timedelta(
        days=999999999, microseconds=999999
    )


def test_decimal_import_does_not_round_before_microsecond_quantization() -> None:
    value = Decimal("0.000000500000000000000000000000001")
    with localcontext() as context:
        context.prec = 1
        context.traps[Inexact] = True
        context.clear_flags()
        assert to_timedelta(Quantity(value=value, unit=SECOND)).unwrap() == timedelta(
            microseconds=1
        )
        assert not any(context.flags.values())


@pytest.mark.parametrize("function", (from_hours, from_minutes, to_timedelta))
@pytest.mark.parametrize("value", (math.nan, math.inf, -math.inf))
def test_builtin_nonfinite_values_return_failure(
    *, function: Any, value: float
) -> None:
    result = (
        function(Quantity(value=value, unit=SECOND))
        if function is to_timedelta
        else function(value)
    )
    assert isinstance(result, Failed)


@pytest.mark.parametrize("constructor,factor", ((from_hours, 3600), (from_minutes, 60)))
def test_constructor_captures_factory_before_open_math_then_reads_current_second(
    *, constructor: Any, factor: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, payload, unit = object(), object(), object()
    events = []

    def factory(**kwargs: Any) -> Any:
        events.append("captured-factory")
        assert kwargs == dict(value=payload, unit=unit)
        return output

    class Value:
        def __mul__(self, other: Any) -> Any:
            events.append("multiply")
            assert type(other) is int and other == factor
            monkeypatch.setattr(
                _module, "Quantity", lambda **kwargs: pytest.fail("late factory")
            )
            monkeypatch.setattr(_module, "SECOND", unit)
            return payload

    monkeypatch.setattr(_module, "Quantity", factory)
    assert constructor(Value()).unwrap() is output
    assert events == ["multiply", "captured-factory"]


@pytest.mark.parametrize("raw", (None, object(), Ok(3)))
def test_open_source_and_late_factory_keep_opaque_data(
    *, raw: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    value, returned = object(), object()
    events = []

    def factory(**kwargs: Any) -> Any:
        events.append("factory")
        assert kwargs == {"seconds": raw}
        return returned

    class Open:
        def __getattribute__(self, name: str) -> Any:
            if name in ("_factor", "symbol", "dimension"):
                pytest.fail("unknown unit metadata")
            return object.__getattribute__(self, name)

        def to_si(self, supplied: Any) -> Any:
            events.append("source")
            assert supplied is value
            monkeypatch.setattr(_module, "timedelta", factory)
            return raw

    assert to_timedelta(Quantity(value=value, unit=Open())).unwrap() is returned
    assert events == ["source", "factory"]


@pytest.mark.parametrize("raw", (Fraction(1, 3), 1.25))
def test_native_values_export_losslessly_to_open_seconds_factory(
    *, raw: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = []
    monkeypatch.setattr(_module, "timedelta", lambda **kwargs: seen.append(kwargs))
    assert to_timedelta(Quantity(value=raw, unit=SECOND)).unwrap() is None
    assert seen == [{"seconds": raw}]
    assert type(seen[0]["seconds"]) is type(raw)


@pytest.mark.parametrize("control", (False, True))
@pytest.mark.parametrize("stage", ("multiply", "source", "factory"))
def test_external_errors_retain_identity_and_control_exceptions_propagate(
    *, stage: str, control: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Formatting:
        def __str__(self) -> str:
            pytest.fail("error formatting")

    class Ordinary(Formatting, Exception):
        pass

    class Control(Formatting, BaseException):
        pass

    error = Control() if control else Ordinary()

    class Value:
        def __mul__(self, value: Any) -> Any:
            raise error

    def source(value: Any) -> Any:
        if stage == "source":
            raise error
        return value

    def factory(**kwargs: Any) -> Any:
        raise error

    if stage == "factory":
        monkeypatch.setattr(_module, "timedelta", factory)

    def call() -> Any:
        return (
            from_hours(Value())
            if stage == "multiply"
            else to_timedelta(Quantity(value=1, unit=SimpleNamespace(to_si=source)))
        )

    if control:
        with pytest.raises(type(error)) as caught:
            call()
        assert caught.value is error
    else:
        result = call()
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
        assert error.__traceback__ is not None


def test_native_failure_is_preserved_without_factory_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = Unit.create(name="bad", symbol="", powers=(0,) * 10, scale=0)
    monkeypatch.setattr(Unit, "convert_exact", lambda *args, **kwargs: failure)
    monkeypatch.setattr(
        _module, "timedelta", lambda **kwargs: pytest.fail("factory after failure")
    )
    assert to_timedelta(Quantity(value=1, unit=SECOND)) is failure
    assert from_hours(1) is failure


@pytest.mark.parametrize(
    "module",
    (
        "ospf_python._binding.quantity_duration",
        "ospf_python.quantities.quantity.duration_extensions",
        "ospf_python.quantities",
    ),
)
def test_fresh_import_orders(module: str) -> None:
    code = "import importlib,os,sys; handles=[os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS','').split(os.pathsep) if p] if os.name=='nt' else []; importlib.import_module(sys.argv[1]); from ospf_python.quantities import from_hours,to_timedelta; from datetime import timedelta; assert to_timedelta(from_hours(1).unwrap()).unwrap()==timedelta(hours=1)"
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, module],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


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
def test_all_223_constants_keep_time_dimension_and_precision_guards(unit: Any) -> None:
    assert len(_constants()) == 223
    result = to_timedelta(Quantity(value=Fraction(1), unit=unit))
    if type(unit) is TimeUnit:
        assert result.unwrap() == timedelta(
            microseconds=round(Fraction(unit._factor) * 1000000)
        )
    else:
        assert isinstance(result, Failed)


@pytest.mark.parametrize("function", (from_hours, from_minutes))
@pytest.mark.parametrize("kwargs", ({"context": object()}, {"exact": 1}))
def test_constructor_rejects_invalid_new_output_options(
    *, function: Any, kwargs: Any
) -> None:
    assert isinstance(function(1, **kwargs), Failed)


@pytest.mark.parametrize("function,factor", ((from_hours, 3600), (from_minutes, 60)))
def test_decimal_constructor_output_policy_is_explicit(
    *, function: Any, factor: int
) -> None:
    value = Decimal("1.23456789")
    with localcontext() as context:
        context.prec = 3
        context.clear_flags()
        result = function(value)
        assert isinstance(result, Failed) and result.error.code is ErrorCode.DATA_LOSS
        context.clear_flags()
        actual = function(value, context=context, exact=False).unwrap().value
        expected = value * factor
        assert actual == expected


def test_timedelta_source_uses_one_actual_guard_and_keeps_opaque_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    code = native_family.__code__
    previous = sys.getprofile()

    def profile(frame: Any, event: str, arg: Any) -> None:
        nonlocal calls
        if event == "call" and frame.f_code is code:
            calls += 1

    try:
        sys.setprofile(profile)
        result = to_timedelta(Quantity(value=1, unit=SECOND))
    finally:
        sys.setprofile(previous)
    assert result.unwrap() == timedelta(seconds=1) and calls == 1
    source = _duration._Duration(context=None, exact=True, numeric_adapter=None)
    assert source.source((SECOND, SECOND.to_si, 1))[1] == 0
    token = source.dispatch.standard
    assert token is not None
    callback = lambda value: token
    success, kind, value, powers = source.source((SimpleNamespace(), callback, None))
    assert success and kind == 2 and value is token and powers is None
    assert source.dispatch.standard is None
    seen = []
    monkeypatch.setattr(_module, "timedelta", lambda **kwargs: seen.append(kwargs))
    assert (
        to_timedelta(
            Quantity(value=None, unit=SimpleNamespace(to_si=callback))
        ).unwrap()
        is None
    )
    assert seen == [{"seconds": token}]


def test_source_lane_change_before_dispatch_does_not_invent_native_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _conversion._Dispatch.source
    raw, output = object(), object()
    seen = []

    def dispatch(self: Any, *, unit: Any, callback: Any, value: Any) -> Any:
        return original(
            self, unit=SimpleNamespace(), callback=lambda value: raw, value=value
        )

    def factory(**kwargs: Any) -> Any:
        seen.append(kwargs)
        return output

    monkeypatch.setattr(_conversion._Dispatch, "source", dispatch)
    monkeypatch.setattr(_module, "timedelta", factory)
    assert to_timedelta(Quantity(value=1, unit=SECOND)).unwrap() is output
    assert seen == [{"seconds": raw}]


@pytest.mark.parametrize("stage", ("unit", "to_si", "value", "call"))
@pytest.mark.parametrize("control", (False, True))
def test_staged_source_errors_keep_handled_exception_state(
    *, stage: str, control: bool
) -> None:
    ordinary = RuntimeError("source")
    signal = KeyboardInterrupt()
    error = signal if control else ordinary
    ambient = ValueError("ambient")

    class Open:
        def __getattribute__(self, name: str) -> Any:
            if stage == name:
                raise error
            return object.__getattribute__(self, name)

        def to_si(self, value: Any) -> Any:
            assert sys.exception() is ambient
            if stage == "call":
                raise error
            return value

    class Owner:
        unit = Open()
        value = 1

        def __getattribute__(self, name: str) -> Any:
            if stage == name:
                raise error
            return object.__getattribute__(self, name)

    owner: Any = Owner()
    try:
        raise ambient
    except ValueError:
        if control:
            with pytest.raises(type(error)) as caught:
                to_timedelta(owner)
            assert caught.value is error
        else:
            result = to_timedelta(owner)
            assert isinstance(result, Failed)
            assert result.error.value.callback_exception is error
        assert sys.exception() is ambient and error.__context__ is ambient


@pytest.mark.parametrize("function", (from_hours, from_minutes, to_timedelta))
def test_success_does_not_cache_custom_values_or_owners(function: Any) -> None:
    class Value:
        def __mul__(self, factor: Any) -> int:
            return 1

    value = Value()
    reference = weakref.ref(value)
    owner: Any = Quantity(value=value, unit=SimpleNamespace(to_si=lambda value: 1))
    result = function(owner) if function is to_timedelta else function(value)
    assert result.is_ok()
    del value, owner
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("function", (from_hours, from_minutes, to_timedelta))
@pytest.mark.parametrize("failed", (False, True))
def test_adapter_failure_identity_and_raw_result_validation(
    *, function: Any, failed: bool
) -> None:
    original = Unit.create(name="bad", symbol="", powers=(0,) * 10, scale=0)

    class Adapter(_Adapter):
        def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
            return original if failed else 3  # type: ignore[return-value]

    adapter = Adapter()
    value = _Value(Fraction(1))
    result = (
        function(Quantity(value=value, unit=SECOND), numeric_adapter=adapter)
        if function is to_timedelta
        else function(value, numeric_adapter=adapter)
    )
    assert isinstance(result, Failed)
    if failed:
        assert result.error.value.callback_result is original
    else:
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize("constructor", (from_hours, from_minutes))
def test_adapter_output_failure_stops_before_quantity_factory(
    *, constructor: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    failure = Unit.create(name="bad", symbol="", powers=(0,) * 10, scale=0)

    class Adapter(_Adapter):
        def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
            return failure  # type: ignore[return-value]

    monkeypatch.setattr(_module, "Quantity", lambda **kwargs: pytest.fail("factory"))
    result = constructor(_Value(Fraction(1)), numeric_adapter=Adapter())
    assert isinstance(result, Failed) and result.error.value.callback_result is failure


@pytest.mark.parametrize(
    "name,function",
    (("Quantity", from_hours), ("Quantity", from_minutes), ("timedelta", to_timedelta)),
)
def test_global_factory_falls_back_to_builtins_only_when_missing(
    *, name: str, function: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    returned = object()
    seen = []

    def factory(**kwargs: Any) -> Any:
        seen.append(kwargs)
        return returned

    monkeypatch.delattr(_module, name)
    monkeypatch.setattr(builtins, name, factory, raising=False)
    argument: Any = Quantity(value=1, unit=SECOND) if function is to_timedelta else 1
    assert function(argument).unwrap() is returned
    assert len(seen) == 1 and set(seen[0]) == (
        {"seconds"} if name == "timedelta" else {"value", "unit"}
    )


@pytest.mark.parametrize(
    "name,function",
    (("Quantity", from_hours), ("Quantity", from_minutes), ("timedelta", to_timedelta)),
)
def test_missing_factory_becomes_result_without_erasing_name_error(
    *, name: str, function: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delattr(_module, name)
    monkeypatch.delattr(builtins, name, raising=False)
    argument: Any = Quantity(value=1, unit=SECOND) if function is to_timedelta else 1
    result = function(argument)
    assert isinstance(result, Failed)
    assert type(result.error.value.callback_exception) is NameError


def test_actual_c_api_timedelta_type_is_not_a_replaceable_datetime_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    datetime_module = importlib.import_module("datetime")
    seen = []

    def factory(**kwargs: Any) -> None:
        seen.append(kwargs)

    monkeypatch.setattr(datetime_module, "timedelta", factory)
    monkeypatch.setattr(_module, "timedelta", factory)
    assert to_timedelta(Quantity(value=Fraction(1, 3), unit=SECOND)).unwrap() is None
    assert seen == [{"seconds": Fraction(1, 3)}]
