"""运行时单位与精确物理量的真实原生合同。 / Real native runtime-unit and exact-quantity contracts."""

from __future__ import annotations

import gc
import importlib
import json
import math
import struct
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python import _native
from ospf_python._binding.quantities import Unit
from ospf_python.quantities import unit as unit_package
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

if TYPE_CHECKING:
    from ospf_python._binding.numeric import Rational

_LENGTH = (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
_MASS = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
_TEMPERATURE = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
_DIMENSIONS = {
    "Acceleration": (0, 1, -2, 0, 0, 0, 0, 0, 0, 0),
    "Amount": (0, 0, 0, 0, 0, 1, 0, 0, 0, 0),
    "AngularAcceleration": (0, 0, -2, 0, 0, 0, 0, 0, 1, 0),
    "AngularVelocity": (0, 0, -1, 0, 0, 0, 0, 0, 1, 0),
    "Area": (0, 2, 0, 0, 0, 0, 0, 0, 0, 0),
    "Bandwidth": (0, 0, -1, 0, 0, 0, 0, 1, 0, 0),
    "CatalyticActivity": (0, 0, -1, 0, 0, 1, 0, 0, 0, 0),
    "Current": (0, 0, 0, 1, 0, 0, 0, 0, 0, 0),
    "ElectricCharge": (0, 0, 1, 1, 0, 0, 0, 0, 0, 0),
    "Energy": (1, 2, -2, 0, 0, 0, 0, 0, 0, 0),
    "FlowRate": (0, 3, -1, 0, 0, 0, 0, 0, 0, 0),
    "Force": (1, 1, -2, 0, 0, 0, 0, 0, 0, 0),
    "Frequency": (0, 0, -1, 0, 0, 0, 0, 0, 0, 0),
    "Information": (0, 0, 0, 0, 0, 0, 0, 1, 0, 0),
    "Length": _LENGTH,
    "LuminousIntensity": (0, 0, 0, 0, 0, 0, 1, 0, 0, 0),
    "Mass": _MASS,
    "MassDensity": (1, -3, 0, 0, 0, 0, 0, 0, 0, 0),
    "Momentum": (1, 1, -1, 0, 0, 0, 0, 0, 0, 0),
    "PlaneAngle": (0, 0, 0, 0, 0, 0, 0, 0, 1, 0),
    "Power": (1, 2, -3, 0, 0, 0, 0, 0, 0, 0),
    "Pressure": (1, -1, -2, 0, 0, 0, 0, 0, 0, 0),
    "Resistance": (1, 2, -3, -2, 0, 0, 0, 0, 0, 0),
    "SolidAngle": (0, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    "Stress": (1, -1, -2, 0, 0, 0, 0, 0, 0, 0),
    "SurfaceDensity": (1, -2, 0, 0, 0, 0, 0, 0, 0, 0),
    "Temperature": _TEMPERATURE,
    "TimeUnit": (0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
    "Torque": (1, 2, -2, 0, 0, 0, 0, 0, 0, 0),
    "Velocity": (0, 1, -1, 0, 0, 0, 0, 0, 0, 0),
    "Voltage": (1, 2, -3, -1, 0, 0, 0, 0, 0, 0),
    "Volume": (0, 3, 0, 0, 0, 0, 0, 0, 0, 0),
    "Wavenumber": (0, -1, 0, 0, 0, 0, 0, 0, 0, 0),
}


def _constants() -> list[Any]:
    return [
        pytest.param(value, id=f"{family}.{name}")
        for family in _DIMENSIONS
        for name, value in sorted(
            vars(
                importlib.import_module(getattr(unit_package, family).__module__)
            ).items()
        )
        if name.isupper() and type(value) is getattr(unit_package, family)
    ]


def _fraction(value: Rational) -> Fraction:
    return Fraction(*value.as_integer_ratio())


def _length(scale: Any = 1) -> Unit:
    return Unit.create(name="length", symbol="m", powers=_LENGTH, scale=scale).unwrap()


def _is_atomic_mass(unit: Any) -> bool:
    return type(unit).__name__ == "Mass" and unit.symbol == "u"


def test_all_public_unit_families_and_constants_are_explicitly_covered() -> None:
    assert len(_DIMENSIONS) == 33
    assert len(_constants()) == 223


@pytest.mark.parametrize("unit", _constants())
@pytest.mark.parametrize(
    "value", (2**200 + 1, Fraction(23, 7), Decimal("-0.12345678901234567890123456789"))
)
def test_all_unit_constants_convert_exactly_without_float_or_decimal_context(
    *, unit: Any, value: Any
) -> None:
    powers = _DIMENSIONS[type(unit).__name__]
    source_result = Unit.create(
        name="source",
        symbol=unit.symbol,
        powers=powers,
        scale=unit._factor,
        offset=getattr(unit, "_offset", None),
    )
    if _is_atomic_mass(unit):
        assert isinstance(source_result, Failed)
        assert source_result.error.code is ErrorCode.DATA_LOSS
        return
    source = source_result.unwrap()
    target = Unit.create(name="standard", symbol="SI", powers=powers).unwrap()
    with localcontext() as context:
        context.prec = 3
        context.clear_flags()
        result = source.convert_exact(value=value, target=target).unwrap()
        expected = Fraction(value) * Fraction(unit._factor) + Fraction(
            getattr(unit, "_offset", 0)
        )
        assert _fraction(result) == expected
        assert _fraction(
            target.convert_exact(value=result, target=source).unwrap()
        ) == Fraction(value)
        assert not any(context.flags.values())


@pytest.mark.parametrize("unit", _constants())
@pytest.mark.parametrize("value", (0.0, -0.0, 1.25, -273.15, 1e308))
def test_all_unit_constants_float64_results_match_pinned_rule_order(
    *, unit: Any, value: float
) -> None:
    powers = _DIMENSIONS[type(unit).__name__]
    offset = getattr(unit, "_offset", None)
    source_result = Unit.create(
        name="source",
        symbol=unit.symbol,
        powers=powers,
        scale=unit._factor,
        offset=offset,
    )
    if _is_atomic_mass(unit):
        assert isinstance(source_result, Failed)
        assert source_result.error.code is ErrorCode.DATA_LOSS
        return
    source = source_result.unwrap()
    target = Unit.create(name="standard", symbol="SI", powers=powers).unwrap()
    expected = (
        value
        if unit._factor == 1.0 and offset is None
        else value * unit._factor + (offset or 0.0)
    )
    actual = source.convert_float64(value=value, target=target)
    if not math.isfinite(expected):
        assert isinstance(actual, Failed)
        assert actual.error.code is ErrorCode.OVERFLOW
    else:
        assert struct.pack("!d", actual.unwrap()) == struct.pack("!d", expected)


@pytest.mark.parametrize(
    "bad",
    (True, "1", None, Fraction(1, 3), float("inf"), float("nan"), Decimal("sNaN")),
)
def test_invalid_coefficients_are_structured_failures_without_user_coercion(
    bad: Any,
) -> None:
    assert Unit.create(name="bad", symbol="bad", powers=_LENGTH, scale=bad).is_failed()
    if bad is not None:
        assert Unit.create(
            name="bad", symbol="bad", powers=_LENGTH, offset=bad
        ).is_failed()


@pytest.mark.parametrize(
    "powers", ((), _LENGTH[:-1], (True,) * 10, (0.5,) * 10, (1 << 64,) * 10, [0] * 10)
)
def test_native_integer_dimension_domain_does_not_truncate_or_accept_bool(
    powers: Any,
) -> None:
    assert Unit.create(name="bad", symbol="same", powers=powers).is_failed()


def test_dimension_checks_do_not_use_symbol_and_metadata_snapshots_are_independent() -> (
    None
):
    length = _length()
    mass = Unit.create(name="mass", symbol="m", powers=_MASS).unwrap()
    assert not length.same_dimension(mass).unwrap()
    assert length.convert_exact(value=1, target=mass).is_failed()
    alias = Unit.create(name="other", symbol="other", powers=_LENGTH).unwrap()
    assert length.same_unit(alias).unwrap()
    assert length.descriptor()[:2] == ("length", "m")
    descriptor = length._handle.descriptor()
    descriptor[2][1] = 0
    assert length.descriptor()[2] == _LENGTH
    assert not hasattr(length, "__dict__")
    with pytest.raises(FrozenInstanceError):
        length._handle = mass._handle  # type: ignore[misc]
    with pytest.raises(TypeError):
        _native._QuantityUnit()


@pytest.mark.parametrize("axis", range(10))
def test_all_ten_dimensions_remain_distinct(axis: int) -> None:
    powers = tuple(int(index == axis) for index in range(10))
    native = Unit.create(name="dimension", symbol="same", powers=powers).unwrap()
    assert native.descriptor()[2] == powers
    for other in range(10):
        target = Unit.create(
            name="other",
            symbol="same",
            powers=tuple(int(index == other) for index in range(10)),
        ).unwrap()
        assert native.same_dimension(target).unwrap() is (axis == other)


def test_affine_points_and_differences_return_actual_native_units() -> None:
    point = Unit.create(
        name="Celsius", symbol="C", powers=_TEMPERATURE, offset=Decimal("273.15")
    ).unwrap()
    delta = Unit.create(
        name="Kelvin difference", symbol="dK", powers=_TEMPERATURE
    ).unwrap()
    assert point.binary_exact(value=20, other=10, other_unit=point).is_failed()
    value, output = point.binary_exact(
        value=20, other=10, other_unit=point, subtract=True
    ).unwrap()
    assert _fraction(value) == 10
    assert output.descriptor()[1] == "delta(C)"
    assert output.descriptor()[-1] is None
    value, output = point.binary_exact(value=20, other=10, other_unit=delta).unwrap()
    assert _fraction(value) == 30
    assert output.same_unit(point).unwrap()
    assert delta.binary_exact(
        value=20, other=10, other_unit=point, subtract=True
    ).is_failed()


def test_pinned_precision_losses_are_explicit_failures_not_falsely_exact_values() -> (
    None
):
    coefficient = Decimal("0." + "1" * 150)
    lost = Unit.create(name="precise", symbol="p", powers=_LENGTH, scale=coefficient)
    assert isinstance(lost, Failed)
    assert lost.error.code is ErrorCode.DATA_LOSS
    point = Unit.create(
        name="point", symbol="p", powers=_TEMPERATURE, scale=3, offset=1
    ).unwrap()
    delta = Unit.create(name="delta", symbol="d", powers=_TEMPERATURE).unwrap()
    mixed, output = point.binary_exact(value=0, other=1, other_unit=delta).unwrap()
    assert _fraction(mixed) == Fraction(1, 3)
    assert output.descriptor() == point.descriptor()
    third = delta.convert_exact(
        value=1,
        target=Unit.create(
            name="three", symbol="3", powers=_TEMPERATURE, scale=3
        ).unwrap(),
    ).unwrap()
    assert _fraction(third) == Fraction(1, 3)


@pytest.mark.parametrize("value", (math.inf, -math.inf, math.nan, 1, True))
def test_float64_is_explicit_and_finite(value: Any) -> None:
    unit = _length()
    assert unit.convert_float64(value=value, target=unit).is_failed()


def test_zero_negative_and_extreme_scales_have_explicit_domain_policies() -> None:
    assert Unit.create(name="zero", symbol="0", powers=_LENGTH, scale=0).is_failed()
    source, target = _length(-2), _length()
    assert _fraction(source.convert_exact(value=3, target=target).unwrap()) == -6
    for exponent in (1000, -1000):
        unit = _length(Decimal(f"1e{exponent}"))
        assert unit.convert_float64(value=1.0, target=target).is_failed()
        assert _fraction(
            unit.convert_exact(value=1, target=target).unwrap()
        ) == Fraction(Decimal(f"1e{exponent}"))


def test_snapshots_preserve_huge_offsets_without_python_string_digit_limits() -> None:
    big = (1 << 20000) + 1
    point = Unit.create(
        name="巨大点 / huge point", symbol="p", powers=_LENGTH, offset=big
    ).unwrap()
    text = point.to_json()
    assert len(json.loads(text)["offset"]["coefficient"]) > 4300
    restored = Unit.from_json(text).unwrap()
    assert restored.to_json() == text
    assert restored.descriptor() == point.descriptor()
    assert (
        _fraction(restored.convert_exact(value=1, target=_length()).unwrap()) == big + 1
    )


@pytest.mark.parametrize(
    "mutate",
    (
        lambda wire: wire.update(version=2),
        lambda wire: wire.update(schema="other"),
        lambda wire: wire.update(extra=1),
        lambda wire: wire.update(powers=[0.5] * 10),
        lambda wire: wire["scale"].update(coefficient="0"),
        lambda wire: wire["scale"].update(coefficient="01"),
        lambda wire: wire["scale"].update(scale=2**63),
    ),
)
def test_invalid_snapshots_fail_without_changing_original(mutate: Any) -> None:
    original = _length()
    text = original.to_json()
    wire = json.loads(text)
    mutate(wire)
    assert Unit.from_json(json.dumps(wire)).is_failed()
    assert original.to_json() == text


def test_threads_and_repeated_conversions_retain_no_python_payloads() -> None:
    source, target = _length(1000), _length()
    left_refs, right_refs = (
        sys.getrefcount(source._handle),
        sys.getrefcount(target._handle),
    )

    def convert(index: int) -> tuple[int, int]:
        value = Fraction((1 << 512) + index, 17)
        native = source.convert_exact(value=value, target=target).unwrap()
        assert _fraction(native) == value * 1000
        return (
            target.convert_exact(value=native, target=source)
            .unwrap()
            .as_integer_ratio()
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(convert, range(80)))
    assert len(results) == 80
    gc.collect()
    final_left_refs = sys.getrefcount(source._handle)
    final_right_refs = sys.getrefcount(target._handle)
    assert final_left_refs == left_refs
    assert final_right_refs == right_refs
