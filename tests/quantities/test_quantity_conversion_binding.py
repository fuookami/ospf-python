"""自然 Quantity.to 的 Result 与开放数值合同。 / Result and open numeric contracts for natural Quantity.to."""

from __future__ import annotations

import gc
import importlib
import os
import struct
import subprocess
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from decimal import Context, Decimal, Inexact
from fractions import Fraction
from typing import Any

import pytest

from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.unit_registry import _families
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import NumericAdapter
from ospf_python.quantities.quantity import quantity as quantity_module
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import KILOMETER, METER, Length
from ospf_python.quantities.unit.mass import ATOMIC_MASS_UNIT, KILOGRAM
from ospf_python.quantities.unit.physical_unit import PhysicalUnit
from ospf_python.quantities.unit.temperature import CELSIUS, KELVIN
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Result, Success, Warn


def _constants() -> list[Any]:
    return [
        pytest.param(value, id=f"{family.cls.__name__}.{name}")
        for family in _families.values()
        for name, value in sorted(
            vars(importlib.import_module(family.cls.__module__)).items()
        )
        if name.isupper() and type(value) is family.cls
    ]


def _fraction(value: Any) -> Fraction:
    if type(value) is Rational:
        return Fraction(*value.as_integer_ratio())
    if type(value) is PublicRational:
        return Fraction(value.numerator, value.denominator)
    return Fraction(value)


@pytest.mark.parametrize("unit", _constants())
@pytest.mark.parametrize(
    "domain", (int, Fraction, Decimal, Rational, PublicRational, float, Floating)
)
def test_natural_conversion_covers_all_223_units_and_seven_domains(
    *, unit: Any, domain: Any
) -> None:
    value = (
        Rational.create(numerator=7).unwrap()
        if domain is Rational
        else domain(7.0 if domain in (float, Floating) else 7)
    )
    result = Quantity(value=value, unit=unit).to(
        type(unit)(), context=Context(prec=400)
    )
    if unit is ATOMIC_MASS_UNIT:
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.DATA_LOSS
        return
    output = result.unwrap()
    if domain in (float, Floating):
        family = _families[id(type(unit))]
        source = Unit.create(
            name="source",
            symbol="",
            powers=family.powers,
            scale=unit._factor,
            offset=getattr(unit, "_offset", None),
        ).unwrap()
        target = Unit.create(
            name="SI",
            symbol="",
            powers=family.powers,
            offset=0 if family.affine else None,
        ).unwrap()
        reference = source.convert_float64(value=7.0, target=target).unwrap()
        assert struct.pack(
            "!d", output.value.value if domain is Floating else output.value
        ) == struct.pack("!d", reference)
    else:
        expected = Fraction(7) * Fraction(unit._factor) + Fraction(
            getattr(unit, "_offset", 0)
        )
        assert _fraction(output.value) == expected
        assert type(output.value) is (
            Fraction if domain is int and expected.denominator != 1 else domain
        )
    assert type(output.unit) is type(unit)


@pytest.mark.parametrize(
    "domain", (int, Fraction, Decimal, float, Floating, PublicRational)
)
def test_known_dimensions_reject_cross_family_without_factory(
    *, domain: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = Quantity(value=domain(2), unit=METER)
    monkeypatch.setattr(
        quantity_module, "Quantity", lambda **kw: pytest.fail("factory after failure")
    )
    result = owner.to(KILOGRAM)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize(
    "value",
    (
        2**1000 + 1,
        Fraction(1, 3),
        Decimal("0.123456789012345678901234567890"),
        PublicRational(1, 3),
        Floating(1.25),
    ),
)
def test_same_unit_does_not_coerce_to_float(value: Any) -> None:
    output = (
        Quantity(value=value, unit=METER).to(METER, context=Context(prec=100)).unwrap()
    )
    assert type(output.value) is type(value)
    assert output.value == value


@pytest.mark.parametrize("literal", ("1.2300", "0E-20", "-0.000", "100.000"))
def test_decimal_exports_context_canonical_representation_not_original_quantum(
    literal: str,
) -> None:
    context = Context(prec=80)
    value = Decimal(literal)
    result = Quantity(value=value, unit=METER).to(METER, context=context).unwrap().value
    fraction = Fraction(value)
    expected = context.divide(
        Decimal(fraction.numerator), Decimal(fraction.denominator)
    )
    assert result.as_tuple() == expected.as_tuple()
    assert result == value
    assert not result.is_signed() if value.is_zero() else True


def test_decimal_rounding_requires_opt_in_and_no_intermediate_rounding() -> None:
    context = Context(prec=1)
    context.traps[Inexact] = True
    unit = Length("three", 3)
    assert Quantity(value=Decimal("0.7"), unit=unit).to(
        unit, context=context
    ).unwrap().value == Decimal("0.7")
    assert not any(context.flags.values())
    failure = Quantity(value=Decimal(1), unit=METER).to(unit, context=Context(prec=3))
    assert isinstance(failure, Failed) and failure.error.code is ErrorCode.DATA_LOSS
    assert Quantity(value=Decimal(1), unit=METER).to(
        unit, context=Context(prec=3), exact=False
    ).unwrap().value == Decimal("0.333")


@pytest.mark.parametrize(
    "family", list(_families.values()), ids=lambda family: family.cls.__name__
)
@pytest.mark.parametrize("scale", (1.0, 2.0, -2.0))
@pytest.mark.parametrize("value", (0.0, -0.0))
def test_public_signed_zero_follows_explicit_pinned_rule_and_shortcut(
    *, family: Any, scale: float, value: float
) -> None:
    source, target = family.cls(_factor=scale), family.cls()
    native_source = Unit.create(
        name="source",
        symbol="",
        powers=family.powers,
        scale=scale,
        offset=0 if family.affine else None,
    ).unwrap()
    native_target = Unit.create(
        name="target",
        symbol="",
        powers=family.powers,
        offset=0 if family.affine else None,
    ).unwrap()
    expected = native_source.convert_float64(value=value, target=native_target).unwrap()
    output = Quantity(value=value, unit=source).to(target).unwrap().value
    assert struct.pack("!d", output) == struct.pack("!d", expected)
    if (
        not family.affine
        and scale != 1.0
        and struct.pack("!d", source.to_si(value)) == struct.pack("!d", -0.0)
    ):
        assert struct.pack("!d", output) == struct.pack("!d", 0.0)


@pytest.mark.parametrize("phase", ("import", "export"))
def test_adapter_result_class_spoof_is_not_probed(phase: str) -> None:
    spoof = type(
        "Spoof",
        (),
        {"__class__": property(lambda self: pytest.fail("result class spoof"))},
    )

    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            return spoof() if phase == "import" else Ok(Fraction(7))

        def from_fraction(self, value: Any) -> Any:
            return spoof()

    result = Quantity(value=object(), unit=METER).to(METER, numeric_adapter=Adapter())
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_adapter_failure_does_not_read_or_format_external_error() -> None:
    class Hostile:
        def __getattribute__(self, name: str) -> Any:
            pytest.fail("external error attribute read")

        def __str__(self) -> str:
            pytest.fail("external error formatting")

    returned: Any = Failed(Hostile())

    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            return returned

        def from_fraction(self, value: Any) -> Any:
            pytest.fail("export after import failure")

    result = Quantity(value=object(), unit=METER).to(METER, numeric_adapter=Adapter())
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is returned


@pytest.mark.parametrize(
    "value",
    (True, float("inf"), float("nan"), Decimal("NaN"), Decimal("sNaN"), object()),
)
def test_native_invalid_domains_are_result_without_target_lookup(value: Any) -> None:
    class Target:
        symbol = "unused"

        def to_si(self, value: Any) -> Any:
            pytest.fail("unused to_si")

        @property
        def from_si(self) -> Any:
            pytest.fail("target lookup")

    assert isinstance(Quantity(value=value, unit=METER).to(Target()), Failed)


@dataclass(frozen=True)
class _Value:
    ratio: Fraction

    def __float__(self) -> float:
        pytest.fail("implicit float on custom value")


class _Adapter(NumericAdapter[_Value]):
    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        return Ok(value.ratio)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        return Ok(_Value(value))


@pytest.mark.parametrize(
    "source,target",
    ((KILOMETER, METER), (METER, KILOMETER), (CELSIUS, KELVIN), (KELVIN, CELSIUS)),
)
def test_custom_numeric_adapter_uses_rust_conversion_and_preserves_domain(
    *, source: Any, target: Any
) -> None:
    original = _Value(Fraction(1, 3))
    output = (
        Quantity(value=original, unit=source)
        .to(target, numeric_adapter=_Adapter())
        .unwrap()
    )
    expected = (
        original.ratio * Fraction(source._factor)
        + Fraction(getattr(source, "_offset", 0))
        - Fraction(getattr(target, "_offset", 0))
    ) / Fraction(target._factor)
    assert type(output.value) is _Value and output.value.ratio == expected
    assert output.unit is target


@pytest.mark.parametrize(
    "value", (2, 1.25, Floating(1.25), Decimal("1.25"), Fraction(5, 4))
)
def test_explicit_adapter_takes_precedence_even_for_builtin_domains(value: Any) -> None:
    class Adapter:
        def to_fraction(self, item: Any) -> Any:
            assert item is value
            return Ok(Fraction(5, 4))

        def from_fraction(self, item: Fraction) -> Any:
            return Ok(("adapted", item))

    assert Quantity(value=value, unit=KILOMETER).to(
        METER, numeric_adapter=Adapter()
    ).unwrap().value == ("adapted", Fraction(1250))


def test_adapter_custom_metaclass_does_not_trigger_equality_or_hash() -> None:
    class Meta(type):
        def __eq__(cls, other: Any) -> bool:
            pytest.fail("metaclass equality")

        def __hash__(cls) -> int:
            pytest.fail("metaclass hash")

    class Value(metaclass=Meta):
        pass

    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            return Ok(Fraction(1, 3))

        def from_fraction(self, value: Fraction) -> Any:
            return Ok(value)

    assert Quantity(value=Value(), unit=KILOMETER).to(
        METER, numeric_adapter=Adapter()
    ).unwrap().value == Fraction(1000, 3)


@pytest.mark.parametrize("native_source", (True, False))
def test_adapter_mixed_callbacks_observe_exact_external_boundary(
    native_source: bool,
) -> None:
    value = _Value(Fraction(1, 3))

    class OpenUnit:
        symbol = "open"

        def to_si(self, item: Any) -> Any:
            assert item is value
            return value

        def from_si(self, item: Any) -> Any:
            assert type(item) is _Value
            assert item.ratio == Fraction(1000, 3)
            return item

    output = (
        Quantity(value=value, unit=KILOMETER if native_source else OpenUnit())
        .to(OpenUnit() if native_source else KILOMETER, numeric_adapter=_Adapter())
        .unwrap()
    )
    assert output.value.ratio == (
        Fraction(1000, 3) if native_source else Fraction(1, 3000)
    )


def test_opaque_units_ignore_adapter_entirely_and_preserve_result_as_data() -> None:
    value: Any = Failed(Err(ErrorCode.APPLICATION_ERROR, "data"))

    class Adapter:
        def __getattribute__(self, name: str) -> Any:
            pytest.fail("unused adapter read")

    class OpenUnit:
        symbol = "open"

        def to_si(self, item: Any) -> Any:
            assert item is value
            return item

        def from_si(self, item: Any) -> Any:
            return item

    unit = OpenUnit()
    assert (
        Quantity(value=value, unit=unit)
        .to(unit, numeric_adapter=Adapter())
        .unwrap()
        .value
        is value
    )


@pytest.mark.parametrize("phase", ("import", "export"))
@pytest.mark.parametrize(
    "returned",
    (
        Failed(Err(ErrorCode.APPLICATION_ERROR, "failed")),
        Fatal((Err(ErrorCode.APPLICATION_ERROR, "fatal"),)),
        Warn(7, Err(ErrorCode.APPLICATION_ERROR, "warning")),
        Success(),
    ),
)
def test_adapter_failed_or_unsupported_result_is_retained(
    *, phase: str, returned: Any
) -> None:
    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            return returned if phase == "import" else Ok(Fraction(1, 3))

        def from_fraction(self, value: Any) -> Any:
            return returned

    result = Quantity(value=object(), unit=METER).to(METER, numeric_adapter=Adapter())
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is returned
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize("phase", ("import", "export"))
@pytest.mark.parametrize("returned", (Fraction(1, 3), None, object(), Ok(7)))
def test_adapter_result_and_fraction_shape_are_checked(
    *, phase: str, returned: Any
) -> None:
    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            return returned if phase == "import" else Ok(Fraction(1, 3))

        def from_fraction(self, value: Any) -> Any:
            return returned

    result = Quantity(value=object(), unit=METER).to(METER, numeric_adapter=Adapter())
    if phase == "export" and type(returned) is Ok:
        assert result.unwrap().value == 7
    else:
        assert (
            isinstance(result, Failed)
            and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        )


@pytest.mark.parametrize("phase", ("import", "export"))
@pytest.mark.parametrize("handled", (False, True))
@pytest.mark.parametrize(
    "error_type",
    (
        ValueError,
        TypeError,
        ArithmeticError,
        AttributeError,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ),
)
def test_adapter_exception_identity_traceback_and_interrupts(
    *, phase: str, handled: bool, error_type: Any
) -> None:
    error, active = error_type("original"), RuntimeError("active")

    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            assert sys.exception() is (active if handled else None)
            if phase == "import":
                raise error
            return Ok(Fraction(1, 3))

        def from_fraction(self, value: Any) -> Any:
            assert sys.exception() is (active if handled else None)
            raise error

    def run() -> None:
        if issubclass(error_type, Exception):
            result = Quantity(value=object(), unit=METER).to(
                METER, numeric_adapter=Adapter()
            )
            assert isinstance(result, Failed)
            assert result.error.value.callback_exception is error
            assert error.__traceback__ is not None
            assert error.__context__ is (active if handled else None)
        else:
            with pytest.raises(error_type) as caught:
                Quantity(value=object(), unit=METER).to(
                    METER, numeric_adapter=Adapter()
                )
            assert caught.value is error

    if handled:
        try:
            raise active
        except RuntimeError:
            run()
            assert sys.exception() is active
    else:
        run()


def test_adapter_methods_and_quantity_factory_are_late_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = []
    adapter: Any

    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            events.append("import")
            adapter.from_fraction = export
            return Ok(Fraction(7))

        def from_fraction(self, value: Any) -> Any:
            pytest.fail("early export capture")

    def export(value: Fraction) -> Any:
        events.append("export")
        assert value == 7000
        monkeypatch.setattr(quantity_module, "Quantity", lambda **kw: marker)
        return Ok(value)

    marker, adapter = object(), Adapter()
    assert (
        Quantity(value=object(), unit=KILOMETER)
        .to(METER, numeric_adapter=adapter)
        .unwrap()
        is marker
    )
    assert events == ["import", "export"]


def test_custom_export_is_not_run_at_internal_si_or_on_native_failure() -> None:
    events = []

    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            events.append("import")
            return Ok(Fraction(7))

        def from_fraction(self, value: Fraction) -> Any:
            events.append("export")
            return Ok(value)

    assert (
        Quantity(value=object(), unit=KILOMETER)
        .to(KILOMETER, numeric_adapter=Adapter())
        .unwrap()
        .value
        == 7
    )
    assert events == ["import", "export"]
    events.clear()
    assert (
        Quantity(value=object(), unit=METER)
        .to(KILOGRAM, numeric_adapter=Adapter())
        .is_failed()
    )
    assert events == ["import"]


@pytest.mark.parametrize("output", (None, object(), Ok(7)))
def test_natural_result_wraps_opaque_late_factory_output(
    *, output: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = Quantity(value=7, unit=METER)
    monkeypatch.setattr(quantity_module, "Quantity", lambda **kw: output)
    assert owner.to(METER).unwrap() is output


def test_new_opaque_conversion_order_explicitly_excludes_float() -> None:
    events = []

    class Value:
        def __float__(self) -> float:
            pytest.fail("removed float step")

    value = Value()

    class Source:
        symbol = "unused"

        def from_si(self, value: Any) -> Any:
            pytest.fail("unused from_si")

        def to_si(self, item: Any) -> Any:
            events.append("source")
            assert item is value
            return item

    class Target:
        symbol = "unused"

        def to_si(self, value: Any) -> Any:
            pytest.fail("unused to_si")

        @property
        def from_si(self) -> Any:
            events.append("target-get")

            def call(item: Any) -> Any:
                events.append("target")
                return item

            return call

    assert Quantity(value=value, unit=Source()).to(Target()).unwrap().value is value
    assert events == ["source", "target-get", "target"]


def test_custom_values_and_adapter_are_not_cached_after_conversion() -> None:
    value, adapter = _Value(Fraction(7)), _Adapter()
    refs = weakref.ref(value), weakref.ref(adapter)
    output = (
        Quantity(value=value, unit=KILOMETER)
        .to(METER, numeric_adapter=adapter)
        .unwrap()
    )
    assert output.value.ratio == 7000
    del value, adapter
    gc.collect()
    assert all(reference() is None for reference in refs)


def test_reentrant_and_threaded_adapters_have_call_scoped_state() -> None:
    class Adapter(_Adapter):
        def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
            inner = Quantity(value=value.ratio, unit=KILOMETER).to(METER).unwrap().value
            return Ok(inner)

    def run(index: int) -> Any:
        return (
            Quantity(value=_Value(Fraction(index, 3)), unit=METER)
            .to(KILOMETER, numeric_adapter=Adapter())
            .unwrap()
            .value.ratio
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(run, range(24))) == [
            Fraction(index, 3) for index in range(24)
        ]


@pytest.mark.parametrize(
    "first",
    (
        "ospf_python.quantities",
        "ospf_python._binding.unit_conversion",
        "ospf_python.quantities.quantity.numeric_adapter",
        "ospf_python.quantities.unit.physical_unit",
        "ospf_python._binding.quantity_conversion",
        "ospf_python._binding.quantities",
        "ospf_python._binding.numeric",
        "ospf_python.math.algebra.number.floating",
        "ospf_python._binding.unit_registry",
        "ospf_python.quantities.unit.length",
    ),
)
def test_import_orders_and_runtime_unit_protocol_remain_open(first: str) -> None:
    code = f"""
import os,importlib
handles=[os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS','').split(os.pathsep) if p] if os.name=='nt' else []
importlib.import_module({first!r})
from ospf_python.quantities import Quantity,NumericAdapter
from ospf_python.quantities.unit.length import METER,KILOMETER
from ospf_python.quantities.unit.physical_unit import PhysicalUnit
assert isinstance(METER,PhysicalUnit)
assert Quantity(value=7,unit=KILOMETER).to(METER).unwrap().value==7000
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    assert completed.returncode == 0, completed.stderr


def test_numeric_adapter_does_not_close_metadata_free_physical_unit_protocol() -> None:
    class OpenUnit:
        symbol = "opaque"

        def to_si(self, value: Any) -> Any:
            return value

        def from_si(self, value: Any) -> Any:
            return value

    unit = OpenUnit()
    assert isinstance(unit, PhysicalUnit)
    assert Quantity(value=object(), unit=unit).to(unit).is_ok()
