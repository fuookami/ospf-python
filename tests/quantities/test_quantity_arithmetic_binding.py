"""自然方法/默认四则的完整数值域与单位合同。 / Natural/default arithmetic numeric and unit contracts."""

from __future__ import annotations

import gc
import importlib
import math
import operator
import weakref
from concurrent.futures import ThreadPoolExecutor
from decimal import Context, Decimal, localcontext
from fractions import Fraction
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from ospf_python._binding.numeric import Rational
from ospf_python._binding.unit_registry import _families
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities import (
    NumericAdapter,
    Quantity,
    QuantityValueRange,
    Unit,
    min_quantity,
    to_timedelta,
)
from ospf_python.quantities.unit.length import KILOMETER, METER, Length
from ospf_python.quantities.unit.mass import KILOGRAM
from ospf_python.quantities.unit.temperature import CELSIUS
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result

_OPERATIONS = dict(
    add=operator.add,
    subtract=operator.sub,
    multiply=operator.mul,
    divide=operator.truediv,
)
_DOMAINS = (int, Fraction, PublicRational, Rational, Decimal, float, Floating)


def _value(kind: Any, number: int) -> Any:
    return Rational.from_value(number).unwrap() if kind is Rational else kind(number)


def _fraction(value: Any) -> Fraction:
    if type(value) is Rational:
        return Fraction(*value.as_integer_ratio())
    if type(value) is PublicRational:
        return Fraction(value.numerator, value.denominator)
    if type(value) is Floating:
        return Fraction(value.value)
    return Fraction(value)


@pytest.mark.parametrize("left_type", _DOMAINS)
@pytest.mark.parametrize("right_type", _DOMAINS)
@pytest.mark.parametrize("operation", _OPERATIONS)
@pytest.mark.parametrize("named", (False, True))
def test_complete_builtin_mixed_domain_promotion_and_default_result(
    *, left_type: Any, right_type: Any, operation: str, named: bool
) -> None:
    left, raw = Quantity(value=_value(left_type, 6), unit=METER), _value(right_type, 2)
    right = Quantity(value=raw, unit=METER) if operation in ("add", "subtract") else raw
    result = (
        getattr(left, operation)(right)
        if named
        else _OPERATIONS[operation](left, right)
    )
    assert isinstance(result, Ok)
    output = result.unwrap()
    domain = next(
        kind for kind in reversed(_DOMAINS) if kind in (left_type, right_type)
    )
    assert type(output.value) is domain
    assert (
        _fraction(output.value)
        == {"add": 8, "subtract": 4, "multiply": 12, "divide": 3}[operation]
    )
    assert output.unit is METER


@pytest.mark.parametrize(
    "family", list(_families.values()), ids=lambda value: value.cls.__name__
)
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_all_33_families_domains_and_four_operations(
    *, family: Any, domain: Any, operation: str
) -> None:
    source = family.cls()
    left = Quantity(value=_value(domain, 6), unit=source)
    right = (
        Quantity(value=_value(domain, 2), unit=source)
        if operation in ("add", "subtract")
        else _value(domain, 2)
    )
    result = _OPERATIONS[operation](left, right)
    if family.affine and operation != "subtract":
        assert (
            isinstance(result, Failed)
            and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        )
    else:
        value = result.unwrap()
        assert type(value.value) is domain
        assert (
            _fraction(value.value)
            == {"add": 8, "subtract": 4, "multiply": 12, "divide": 3}[operation]
        )
        if family.affine:
            assert isinstance(value.unit, Unit) and not value.unit.is_affine
            assert value.unit.symbol.startswith("delta(")


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
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_all_223_actual_units_keep_precision_and_point_guards(
    *, unit: Any, operation: str
) -> None:
    assert len(_constants()) == 223
    left = Quantity(value=Fraction(6), unit=unit)
    right = (
        Quantity(value=Fraction(2), unit=unit)
        if operation in ("add", "subtract")
        else Fraction(2)
    )
    result = _OPERATIONS[operation](left, right)
    if type(unit).__name__ == "Mass" and unit.symbol == "u":
        assert isinstance(result, Failed) and result.error.code is ErrorCode.DATA_LOSS
    elif _families[id(type(unit))].affine and operation != "subtract":
        assert (
            isinstance(result, Failed)
            and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        )
    else:
        assert (
            _fraction(result.unwrap().value)
            == {"add": 8, "subtract": 4, "multiply": 12, "divide": 3}[operation]
        )


def test_actual_temperature_difference_output_continues_through_all_consumers() -> None:
    difference = (
        Quantity(value=Decimal(80), unit=CELSIUS)
        - Quantity(value=Decimal(20), unit=CELSIUS)
    ).unwrap()
    assert not difference.unit.is_affine
    target = Unit.create(
        name="difference", symbol="dK", powers=(0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    ).unwrap()
    converted = difference.to(target).unwrap()
    assert converted.value == 60
    assert min_quantity([difference, converted]).unwrap() is difference
    assert (
        QuantityValueRange(min_qty=converted, max_qty=converted)
        .contains(difference)
        .unwrap()
    )
    assert isinstance(to_timedelta(difference), Failed)
    assert (difference / 3).unwrap().value == Decimal(20)
    point = (difference + Quantity(value=Decimal(20), unit=CELSIUS)).unwrap()
    assert point.value == 80 and point.unit is CELSIUS
    assert isinstance((difference - point), Failed)


def test_true_unit_conversion_not_symbol_comparison_and_exact_integer_division() -> (
    None
):
    assert (
        Quantity(value=1, unit=METER) + Quantity(value=1, unit=KILOMETER)
    ).unwrap().value == 1001
    assert (
        Quantity(value=1, unit=Length("m", 2)) + Quantity(value=1, unit=METER)
    ).unwrap().value == Fraction(3, 2)
    assert isinstance(
        Quantity(value=1, unit=METER) + Quantity(value=1, unit=KILOGRAM), Failed
    )
    assert (Quantity(value=1, unit=METER) / 3).unwrap().value == Fraction(1, 3)
    assert type((Quantity(value=1, unit=METER) / 3).unwrap().value) is Fraction
    assert (Quantity(value=2**1000, unit=METER) / 3).unwrap().value == Fraction(
        2**1000, 3
    )


def test_mixed_float_import_is_lossless_by_default_and_explicitly_approximate() -> None:
    value = Quantity(value=Fraction(1, 3), unit=METER)
    assert isinstance(value.multiply(1.0), Failed)
    assert value.multiply(1.0, exact=False).unwrap().value == float(Fraction(1, 3))
    assert isinstance(Quantity(value=2**100 + 1, unit=METER).multiply(1.0), Failed)
    assert (
        type(Quantity(value=Decimal("0.5"), unit=METER).multiply(1.0).unwrap().value)
        is float
    )


def test_decimal_context_only_applies_at_final_export() -> None:
    with localcontext(Context(prec=2)) as context:
        before = dict(context.flags)
        left = Quantity(value=Decimal("123456.75"), unit=METER)
        right = Quantity(value=Fraction(1, 4), unit=METER)
        output = left.add(right, context=Context(prec=12)).unwrap()
        assert output.value == Decimal(123457) and dict(context.flags) == before
        assert isinstance(left + right, Failed)
        third = Quantity(value=Decimal(1), unit=METER)
        assert isinstance(third.divide(3), Failed)
        assert third.divide(3, exact=False).unwrap().value == Decimal("0.33")


@pytest.mark.parametrize("operation", ("multiply", "divide"))
@pytest.mark.parametrize("domain", _DOMAINS)
def test_scalar_zero_and_affine_guards(*, operation: str, domain: Any) -> None:
    left = Quantity(value=_value(domain, 1), unit=METER)
    result = getattr(left, operation)(_value(domain, 0))
    if operation == "divide":
        assert (
            isinstance(result, Failed)
            and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        )
    else:
        assert _fraction(result.unwrap().value) == 0
    assert isinstance(
        getattr(Quantity(value=_value(domain, 1), unit=CELSIUS), operation)(
            _value(domain, 1)
        ),
        Failed,
    )


@pytest.mark.parametrize("operation", _OPERATIONS)
@pytest.mark.parametrize("number", (math.inf, -math.inf, math.nan))
def test_float_inputs_are_finite(*, operation: str, number: float) -> None:
    left = Quantity(value=number, unit=METER)
    right = Quantity(value=1.0, unit=METER) if operation in ("add", "subtract") else 1.0
    assert isinstance(_OPERATIONS[operation](left, right), Failed)


class _Int(int):
    pass


class _Fraction(Fraction):
    pass


class _Open:
    def __init__(self, value: int) -> None:
        self.value = value

    def compute(self, other: Any) -> tuple[str, int, str]:
        return "opaque", self.value, type(other).__name__

    __add__ = __sub__ = __mul__ = __truediv__ = compute


_EXTERNAL = (bool, str, np.float64, np.int64, _Int, _Fraction, _Open)


@pytest.mark.parametrize("left_type", (*_DOMAINS, *_EXTERNAL))
@pytest.mark.parametrize("right_type", (*_DOMAINS, *_EXTERNAL))
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_full_14_by_14_matrix_keeps_open_numeric_slot_protocols(
    *, left_type: Any, right_type: Any, operation: str
) -> None:
    if left_type in _DOMAINS and right_type in _DOMAINS:
        # 内置混合域的数学与输出类型由独立矩阵验证。 / The separate matrix proves builtin math and promotion.
        result = _OPERATIONS[operation](
            Quantity(value=_value(left_type, 6), unit=METER),
            Quantity(value=_value(right_type, 2), unit=METER)
            if operation in ("add", "subtract")
            else _value(right_type, 2),
        )
        assert isinstance(result, Ok)
        return
    a, b = _value(left_type, 6), _value(right_type, 2)
    expected_error: type[Exception] | None
    try:
        expected = _OPERATIONS[operation](a, b)
    except Exception as error:
        expected_error = type(error)
    else:
        expected_error = None
    result = _OPERATIONS[operation](
        Quantity(value=a, unit=METER),
        Quantity(value=b, unit=METER) if operation in ("add", "subtract") else b,
    )
    if expected_error is not None:
        assert isinstance(result, Failed)
        assert type(result.error.value.callback_exception) is expected_error
    else:
        assert isinstance(result, Ok)
        assert type(result.unwrap().value) is type(expected)
        assert result.unwrap().value == expected


@pytest.mark.parametrize("error_type", (ValueError, KeyboardInterrupt, SystemExit))
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_open_slot_retains_original_exception_and_interrupt_identity(
    *, error_type: Any, operation: str
) -> None:
    error = error_type("original")

    class Value:
        def compute(self, other: Any) -> Any:
            raise error

        __add__ = __sub__ = __mul__ = __truediv__ = compute

    left = Quantity(value=Value(), unit=METER)
    right = Quantity(value=2, unit=METER) if operation in ("add", "subtract") else 2
    if error_type is ValueError:
        result = _OPERATIONS[operation](left, right)
        assert (
            isinstance(result, Failed)
            and result.error.value.callback_exception is error
        )
        assert error.__traceback__ is not None
    else:
        with pytest.raises(error_type) as caught:
            _OPERATIONS[operation](left, right)
        assert caught.value is error


def test_open_factory_capture_opaque_result_and_late_open_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("ospf_python.quantities.quantity.quantity")
    original: Any = object()
    changed = object()
    marker: Any = Ok(object())

    class Value:
        def __mul__(self, other: Any) -> Any:
            object.__setattr__(left, "unit", changed)
            monkeypatch.setattr(
                module, "Quantity", lambda **kwargs: pytest.fail("late factory")
            )
            return marker

    left = Quantity(value=Value(), unit=original)

    def factory(**kwargs: Any) -> Any:
        assert kwargs == dict(value=marker, unit=changed)
        return marker

    monkeypatch.setattr(module, "Quantity", factory)
    assert left.multiply(2).unwrap() is marker


def test_adapter_snapshots_actual_units_imports_both_operands_and_exports_once() -> (
    None
):
    events = []
    left = Quantity(value=Fraction(1, 3), unit=Length("m", 3))
    right = Quantity(value=Fraction(2, 3), unit=METER)

    class Adapter(NumericAdapter[Any]):
        def to_fraction(self, value: Any) -> Result[Fraction, Any, Any]:
            events.append(("import", value))
            object.__setattr__(left.unit, "_factor", 1000)
            return Ok(value)

        def from_fraction(self, value: Fraction) -> Result[Any, Any, Any]:
            events.append(("export", value))
            return Ok(value)

    result = left.add(right, numeric_adapter=Adapter()).unwrap()
    assert result.value == Fraction(5, 9)
    assert isinstance(result.unit, Unit)
    assert result.to(METER).unwrap().value == Fraction(5, 3)
    assert events == [
        ("import", Fraction(1, 3)),
        ("import", Fraction(2, 3)),
        ("export", Fraction(5, 9)),
    ]


def test_open_unit_does_not_probe_symbol_or_si_properties() -> None:
    class OpenUnit:
        @property
        def symbol(self) -> str:
            pytest.fail("symbol is not a dimension proof")

        @property
        def to_si(self) -> Any:
            pytest.fail("arithmetic must not speculate open conversion")

    unit: Any = OpenUnit()
    assert (
        Quantity(value=3, unit=unit) + Quantity(value=2, unit=unit)
    ).unwrap().value == 5
    assert isinstance(
        Quantity(value=3, unit=unit) + Quantity(value=2, unit=SimpleNamespace()), Failed
    )


def test_reflected_subclass_priority_and_opaque_result_remain_python_protocols() -> (
    None
):
    marker: Any = Ok(object())

    class Right(int):
        def __radd__(self, other: Any) -> Any:
            return marker

    result = Quantity(value=1, unit=METER) + Quantity(value=Right(2), unit=METER)
    assert result.unwrap().value is marker


def test_native_float_safety_and_signed_zero_branch_order() -> None:
    left = Quantity(value=-0.0, unit=METER)
    right = Quantity(value=0.0, unit=METER)
    assert math.copysign(1, (left - right).unwrap().value) == -1
    assert math.copysign(1, (left + right).unwrap().value) == 1
    assert isinstance(Quantity(value=1e308, unit=METER) * 2.0, Failed)
    tiny = Unit.create(
        name="tiny",
        symbol="t",
        powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0),
        scale=Decimal("1e-400"),
    ).unwrap()
    result = Quantity(value=0.0, unit=METER) + Quantity(value=1.0, unit=tiny)
    assert isinstance(result, Failed) and result.error.code is ErrorCode.DATA_LOSS


def test_factory_lookup_uses_lazy_builtin_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins

    module = importlib.import_module("ospf_python.quantities.quantity.quantity")
    left = Quantity(value=3, unit=METER)
    marker = object()
    monkeypatch.delattr(module, "Quantity")
    monkeypatch.setattr(builtins, "Quantity", lambda **kwargs: marker, raising=False)
    assert left.multiply(2).unwrap() is marker


def test_extended_family_descriptors_are_not_speculatively_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    left, unit = Quantity(value=3, unit=METER), METER
    monkeypatch.setattr(
        Length, "_factor", property(lambda self: pytest.fail("speculative factor"))
    )
    assert (left + Quantity(value=2, unit=unit)).unwrap().value == 5


def test_runtime_handle_snapshot_survives_adapter_replacement() -> None:
    unit = Unit.create(
        name="triple", symbol="t", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0), scale=3
    ).unwrap()
    replacement = Unit.create(name="single", symbol="s", powers=unit.powers).unwrap()

    class Adapter(NumericAdapter[Any]):
        def to_fraction(self, value: Any) -> Result[Fraction, Any, Any]:
            object.__setattr__(unit, "_handle", replacement._handle)
            return Ok(Fraction(value))

        def from_fraction(self, value: Fraction) -> Result[Any, Any, Any]:
            return Ok(value)

    result = (
        Quantity(value=1, unit=unit).multiply(2, numeric_adapter=Adapter()).unwrap()
    )
    assert result.value == 2 and result.unit is not unit
    assert result.to(METER).unwrap().value == 6


def test_active_exception_state_reentry_threads_and_owner_release() -> None:
    import sys

    active = RuntimeError("handled")
    original = ValueError("slot")

    class Value:
        def __mul__(self, other: Any) -> Any:
            assert sys.exception() is active
            assert (Quantity(value=1, unit=METER) / 3).unwrap().value == Fraction(1, 3)
            raise original

    try:
        raise active
    except RuntimeError:
        result = Quantity(value=Value(), unit=METER).multiply(2)
        assert (
            isinstance(result, Failed)
            and result.error.value.callback_exception is original
        )
        assert original.__context__ is active and sys.exception() is active

    def compute(index: int) -> Fraction:
        value = (Quantity(value=Fraction(index, 7), unit=METER) * 3).unwrap().value
        assert isinstance(value, Fraction)
        return value

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(compute, range(40))) == [
            Fraction(index * 3, 7) for index in range(40)
        ]
    owner = Quantity(value=1, unit=METER)
    reference = weakref.ref(owner)
    assert (owner * 2).unwrap().value == 2
    del owner
    gc.collect()
    assert reference() is None
