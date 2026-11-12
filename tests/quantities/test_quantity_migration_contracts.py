"""物理量迁移前的公开协议基线。 / Public protocol baseline before quantity migration."""

from __future__ import annotations

import copy
import importlib
import math
import operator
import pickle
import struct
import sys
from dataclasses import FrozenInstanceError, asdict, fields, replace
from decimal import Decimal
from fractions import Fraction
from types import FunctionType
from typing import Any

import pytest

from ospf_python.math.algebra.number.floating import Floating
from ospf_python.quantities import unit as unit_package
from ospf_python.quantities.dimension.dimensions import Dimensions
from ospf_python.quantities.quantity import min_max as min_max_module
from ospf_python.quantities.quantity import quantity as quantity_module
from ospf_python.quantities.quantity import value_range as value_range_module
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.quantity.value_range import QuantityValueRange
from ospf_python.quantities.unit.length import KILOMETER, METER, Length
from ospf_python.quantities.unit.mass import KILOGRAM
from ospf_python.quantities.unit.physical_unit import PhysicalUnit
from ospf_python.quantities.unit.temperature import CELSIUS, Temperature
from tests.quantities._arithmetic_before import legacy_operation


def _legacy_to(self: Any, target_unit: Any) -> Any:
    """仅测试中冻结旧转换，不是生产 fallback。 / Test-only frozen conversion, never a production fallback."""
    si_val = self.unit.to_si(float(self.value))
    new_val = target_unit.from_si(si_val)
    return Quantity(value=new_val, unit=target_unit)


# 原方法的 globals/builtins 仍来自真实模块，保留动态工厂基线。
# Keep the original module globals/builtins for the dynamic-factory baseline.
_legacy_to = FunctionType(_legacy_to.__code__, quantity_module.__dict__)


def _legacy_min_quantity(items: Any) -> Any:
    """仅测试中冻结旧极值政策。 / Test-only frozen old extrema policy."""
    return min(items, key=lambda q: q.unit.to_si(float(q.value)))


def _legacy_max_quantity(items: Any) -> Any:
    """仅测试中冻结旧极值政策。 / Test-only frozen old extrema policy."""
    return max(items, key=lambda q: q.unit.to_si(float(q.value)))


def _legacy_contains(self: Any, qty: Any) -> Any:
    """仅测试中冻结旧跨维度/float 范围政策。 / Test-only frozen old cross-dimensional/float range policy."""
    min_si = self.min_qty.unit.to_si(float(self.min_qty.value))
    max_si = self.max_qty.unit.to_si(float(self.max_qty.value))
    val_si = qty.unit.to_si(float(qty.value))
    return min_si <= val_si <= max_si


_legacy_min_quantity = FunctionType(
    _legacy_min_quantity.__code__, min_max_module.__dict__
)
_legacy_max_quantity = FunctionType(
    _legacy_max_quantity.__code__, min_max_module.__dict__
)


class _LegacyQuantityValueRange(QuantityValueRange[Any]):
    contains = FunctionType(_legacy_contains.__code__, value_range_module.__dict__)


def _unit_classes() -> list[type[Any]]:
    return [
        cls
        for name in unit_package.__all__
        if isinstance(cls := getattr(unit_package, name), type)
        and hasattr(cls, "__dataclass_fields__")
        and "_factor" in cls.__dataclass_fields__
    ]


def _predefined_units() -> list[Any]:
    return [
        pytest.param(value, id=f"{cls.__name__}.{name}")
        for cls in _unit_classes()
        for name, value in sorted(vars(importlib.import_module(cls.__module__)).items())
        if name.isupper() and type(value) is cls
    ]


def _same_float(actual: float, expected: float) -> None:
    if math.isnan(expected):
        assert math.isnan(actual)
    else:
        assert struct.pack("!d", actual) == struct.pack("!d", expected)


def test_all_unit_families_and_constants_are_in_the_baseline() -> None:
    assert len(_unit_classes()) == 33
    assert len(_predefined_units()) == 223


@pytest.mark.parametrize("unit", _predefined_units())
@pytest.mark.parametrize("value", (0.0, -0.0, 1.25, -273.15, 1e308, math.inf, math.nan))
def test_all_predefined_unit_rules_preserve_operation_order_and_ieee_values(
    *, unit: Any, value: float
) -> None:
    standard = value * unit._factor
    reverse = value
    if isinstance(unit, Temperature):
        standard += unit._offset
        reverse -= unit._offset
    _same_float(unit.to_si(value), standard)
    _same_float(unit.from_si(value), reverse / unit._factor)


@pytest.mark.parametrize("cls", _unit_classes(), ids=lambda cls: cls.__name__)
def test_all_unit_families_accept_custom_zero_and_negative_scales(cls: Any) -> None:
    zero = cls(_symbol="zero", _factor=0.0)
    _same_float(zero.to_si(-1.0), 0.0 if cls is Temperature else -0.0)
    with pytest.raises(ZeroDivisionError):
        zero.from_si(1.0)
    negative = cls(_symbol="negative", _factor=-2.0)
    assert negative.to_si(3.0) == -6.0
    assert negative.from_si(-6.0) == 3.0
    assert isinstance(negative, PhysicalUnit)


@pytest.mark.parametrize("value", (2**100 + 1, Fraction(1, 3), Decimal("0.1"), True))
def test_legacy_to_coerces_values_to_float_even_for_identical_units(value: Any) -> None:
    original = Quantity(value=value, unit=METER)
    result = _legacy_to(original, METER)
    assert result is not original
    assert type(result.value) is float
    assert result.value == float(value)
    assert result.unit is METER


def test_legacy_to_has_no_dimension_guard_and_no_floating_coercion() -> None:
    result = _legacy_to(Quantity(value=2.0, unit=METER), KILOGRAM)
    assert result.value == 2.0
    assert result.unit is KILOGRAM
    with pytest.raises(TypeError):
        _legacy_to(Quantity(value=Floating(2.0), unit=METER), KILOMETER)


@pytest.mark.parametrize(
    "operation", (operator.add, operator.sub, operator.mul, operator.truediv)
)
@pytest.mark.parametrize("factory", (int, Fraction, Decimal, Floating))
def test_arithmetic_preserves_numeric_slots_without_float_coercion(
    *, operation: Any, factory: Any
) -> None:
    left, right = factory(6), factory(2)
    quantity = Quantity(value=left, unit=METER)
    other = (
        Quantity(value=right, unit=METER)
        if operation in (operator.add, operator.sub)
        else right
    )
    result = legacy_operation(operation=operation, owner=quantity, other=other)
    expected = operation(left, right)
    assert type(result.value) is type(expected)
    assert result.value == expected
    assert result.unit is METER


@pytest.mark.parametrize("operation", (operator.add, operator.sub))
def test_add_sub_compare_only_symbols_not_unit_equality_or_dimensions(
    operation: Any,
) -> None:
    right_unit = Temperature(_symbol="m", _factor=1000.0, _offset=273.15)
    result = legacy_operation(
        operation=operation,
        owner=Quantity(value=6, unit=METER),
        other=Quantity(value=2, unit=right_unit),
    )
    assert result.value == operation(6, 2)
    assert result.unit is METER
    result = legacy_operation(
        operation=operation,
        owner=Quantity(value=20, unit=CELSIUS),
        other=Quantity(value=10, unit=CELSIUS),
    )
    assert result.value == operation(20, 10)
    assert result.unit is CELSIUS
    with pytest.raises(TypeError, match="different units"):
        legacy_operation(
            operation=operation,
            owner=Quantity(value=1, unit=METER),
            other=Quantity(value=1, unit=KILOMETER),
        )


class _TraceQuantity(Quantity[Any]):
    def __getattribute__(self, name: str) -> Any:
        if name in ("value", "unit"):
            object.__getattribute__(self, "record")(f"self.{name}")
        return object.__getattribute__(self, name)


def _traced_conversion(record: Any) -> tuple[Any, Any]:
    class Unit:
        def __init__(self, name: str) -> None:
            self.name = name

        def __getattribute__(self, name: str) -> Any:
            if name in ("to_si", "from_si"):
                record(f"{object.__getattribute__(self, 'name')}.{name}.get")
            return object.__getattribute__(self, name)

        def to_si(self, value: Any) -> Any:
            record("source.call")
            assert type(value) is float
            return value + 1

        def from_si(self, value: Any) -> Any:
            record("target.call")
            assert value == 3.0
            return output

    class Value:
        def __float__(self) -> float:
            record("value.float")
            return 2.0

    output = object()
    quantity = _TraceQuantity(value=Value(), unit=Unit("source"))
    object.__setattr__(quantity, "record", record)
    return quantity, Unit("target")


_TO_EVENTS = (
    "self.unit",
    "source.to_si.get",
    "self.value",
    "value.float",
    "source.call",
    "target.from_si.get",
    "target.call",
    "factory",
)


def test_to_preserves_dynamic_callback_capture_and_late_global_constructor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    quantity, target = _traced_conversion(events.append)
    marker = object()

    def factory(**kwargs: Any) -> Any:
        events.append("factory")
        assert kwargs["unit"] is target
        assert type(kwargs["value"]) is object
        return marker

    monkeypatch.setattr(quantity_module, "Quantity", factory)
    assert _legacy_to(quantity, target) is marker
    assert events == list(_TO_EVENTS)


@pytest.mark.parametrize("failure_at", _TO_EVENTS)
@pytest.mark.parametrize("error_type", (ValueError, KeyboardInterrupt, SystemExit))
def test_conversion_stops_at_first_failure_and_keeps_original_exception_state(
    *, monkeypatch: pytest.MonkeyPatch, failure_at: str, error_type: Any
) -> None:
    events: list[str] = []
    exception = error_type("sentinel")
    active = RuntimeError("already handled")

    def record(event: str) -> None:
        assert sys.exception() is active
        events.append(event)
        if event == failure_at:
            raise exception

    quantity, target = _traced_conversion(record)

    def factory(**kwargs: Any) -> Any:
        record("factory")
        return kwargs

    monkeypatch.setattr(quantity_module, "Quantity", factory)
    try:
        raise active
    except RuntimeError:
        with pytest.raises(error_type) as caught:
            _legacy_to(quantity, target)
        assert caught.value is exception
        assert caught.value.__context__ is active
        assert sys.exception() is active
        frames = []
        traceback = caught.value.__traceback__
        while traceback is not None:
            frames.append(traceback.tb_frame.f_code.co_name)
            traceback = traceback.tb_next
        assert "record" in frames
    assert events == list(_TO_EVENTS[: _TO_EVENTS.index(failure_at) + 1])


@pytest.mark.parametrize("operation", (operator.add, operator.sub))
def test_mismatch_reads_symbols_again_for_error_without_reading_values(
    operation: Any,
) -> None:
    events: list[str] = []

    class Unit:
        def __init__(self, name: str) -> None:
            self.name = name
            self.reads = 0

        @property
        def symbol(self) -> str:
            self.reads += 1
            events.append(f"{self.name}.{self.reads}")
            return f"{self.name}-{self.reads}"

    left: Any = Unit("left")
    right: Any = Unit("right")
    with pytest.raises(TypeError) as caught:
        legacy_operation(
            operation=operation,
            owner=Quantity(value=object(), unit=left),
            other=Quantity(value=object(), unit=right),
        )
    verb = "add" if operation is operator.add else "subtract"
    assert (
        str(caught.value)
        == f"Cannot {verb} quantities with different units: left-2 and right-2"
    )
    assert events == ["left.1", "right.1", "left.2", "right.2"]


@pytest.mark.parametrize(
    "operation", (operator.add, operator.sub, operator.mul, operator.truediv)
)
def test_arithmetic_captures_constructor_before_numeric_slot_but_reads_unit_after(
    *, monkeypatch: pytest.MonkeyPatch, operation: Any
) -> None:
    events: list[str] = []
    old_unit, new_unit = Length("m", 1.0), Length("changed", 2.0)

    def captured_factory(**kwargs: Any) -> Any:
        events.append("captured factory")
        assert kwargs == {"value": "slot output", "unit": new_unit}
        return output

    def replacement_factory(**kwargs: Any) -> Any:
        pytest.fail("constructor was not captured before the numeric slot")

    class Value:
        def compute(self, other: Any) -> str:
            events.append("slot")
            object.__setattr__(quantity, "unit", new_unit)
            monkeypatch.setattr(quantity_module, "Quantity", replacement_factory)
            return "slot output"

        __add__ = compute
        __sub__ = compute
        __mul__ = compute
        __truediv__ = compute

    output = object()
    quantity = Quantity(value=Value(), unit=old_unit)
    other = (
        Quantity(value=2, unit=old_unit)
        if operation in (operator.add, operator.sub)
        else 2
    )
    monkeypatch.setattr(quantity_module, "Quantity", captured_factory)
    assert legacy_operation(operation=operation, owner=quantity, other=other) is output
    assert events == ["slot", "captured factory"]


def test_to_allows_reentrant_callback_and_keeps_target_output_opaque() -> None:
    seen: list[Any] = []
    marker = object()

    class Unit:
        symbol = "custom"

        def to_si(self, value: float) -> Any:
            seen.append(_legacy_to(Quantity(value=3.0, unit=METER), KILOMETER).value)
            return marker

        def from_si(self, value: Any) -> Any:
            assert value is marker
            return marker

    unit = Unit()
    assert isinstance(unit, PhysicalUnit)
    result = _legacy_to(Quantity(value=2, unit=unit), unit)
    assert result.value is marker
    assert result.unit is unit
    assert seen == [0.003]


def test_to_captures_source_method_before_float_but_target_and_factory_after_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    marker = object()

    def final_factory(**kwargs: Any) -> Any:
        events.append("final factory")
        assert kwargs == {"value": marker, "unit": target}
        return marker

    class Source:
        symbol = "source"

        def to_si(self, value: float) -> float:
            events.append("captured source")
            target.from_si = target_method
            return value + 1

        def from_si(self, value: float) -> float:
            return value

    class Target:
        symbol = "target"

        def to_si(self, value: float) -> float:
            return value

        def from_si(self, value: float) -> Any:
            pytest.fail("target method was captured too early")

    def target_method(value: float) -> Any:
        events.append("late target")
        assert value == 3.0
        monkeypatch.setattr(quantity_module, "Quantity", final_factory)
        return marker

    class Value:
        def __float__(self) -> float:
            events.append("float")
            object.__setattr__(quantity, "unit", METER)
            return 2.0

    target: Any = Target()
    quantity = Quantity(value=Value(), unit=Source())
    assert _legacy_to(quantity, target) is marker
    assert events == ["float", "captured source", "late target", "final factory"]


@pytest.mark.parametrize("cls", _unit_classes(), ids=lambda cls: cls.__name__)
@pytest.mark.parametrize("factory", (Fraction, Decimal))
def test_unit_fields_and_values_are_not_runtime_float_coerced(
    *, cls: Any, factory: Any
) -> None:
    kwargs = {"_symbol": "custom", "_factor": factory(2)}
    if cls is Temperature:
        kwargs["_offset"] = factory(3)
    unit = cls(**kwargs)
    actual = unit.to_si(factory(7))
    assert type(actual) is factory
    assert actual == factory(17 if cls is Temperature else 14)
    assert unit.from_si(actual) == factory(7)


def test_quantity_equality_uses_dataclass_unit_fields_and_exact_quantity_class() -> (
    None
):
    class Derived(Quantity[int]):
        pass

    original = Quantity(value=1, unit=METER)
    assert original != Derived(value=1, unit=METER)
    assert original != Quantity(value=1, unit=Length("m", 2.0))
    assert (
        legacy_operation(
            operation=operator.add,
            owner=original,
            other=Quantity(value=2, unit=Length("m", 2.0)),
        )
    ).value == 3


def test_dataclass_schema_serialization_and_base_constructor_are_stable() -> None:
    class Derived(Quantity[Fraction]):
        pass

    value = Fraction(1, 7)
    original = Quantity(value=value, unit=METER)
    assert [field.name for field in fields(original)] == ["value", "unit"]
    assert original.__match_args__ == ("value", "unit")
    assert vars(original) == {"value": value, "unit": METER}
    assert asdict(original) == {
        "value": value,
        "unit": {"_symbol": "m", "_factor": 1.0},
    }
    assert pickle.loads(pickle.dumps(original)) == original
    assert copy.copy(original) == original
    assert copy.deepcopy(original) == original
    assert replace(original, value=Fraction(2, 7)).value == Fraction(2, 7)
    assert hash(pickle.loads(pickle.dumps(original))) == hash(original)
    assert (
        type(
            legacy_operation(
                operation=operator.mul, owner=Derived(value=value, unit=METER), other=2
            )
        )
        is Quantity
    )
    untyped_original: Any = original
    with pytest.raises(FrozenInstanceError):
        untyped_original.value = 2


def test_string_formats_value_before_dynamic_unit_read() -> None:
    class Value:
        def __format__(self, spec: str) -> str:
            assert spec == ""
            object.__setattr__(quantity, "unit", Length("changed", 2.0))
            return "formatted"

    quantity = Quantity(value=Value(), unit=METER)
    assert str(quantity) == "formatted changed"


def test_min_max_and_range_retain_legacy_si_policy_and_original_items() -> None:
    lower = Quantity(value=100.0, unit=METER)
    upper = Quantity(value=1.0, unit=KILOMETER)
    tie = Quantity(value=0.1, unit=KILOMETER)
    assert _legacy_min_quantity(iter((lower, tie, upper))) is lower
    assert _legacy_max_quantity(iter((lower, upper))) is upper
    assert _LegacyQuantityValueRange(min_qty=lower, max_qty=upper).contains(upper)
    assert _LegacyQuantityValueRange(min_qty=lower, max_qty=upper).contains(
        Quantity(value=500.0, unit=KILOGRAM)
    )
    with pytest.raises(ValueError, match="empty"):
        _legacy_min_quantity([])


def test_dimensions_allow_fractional_exponents_and_have_no_unit_linkage() -> None:
    original = Dimensions(length=1.0)
    half = original**0.5
    assert half.length == 0.5
    assert (half * half) == original
    assert (original / original).is_dimensionless()
    assert Dimensions(length=-0.0).is_dimensionless()
    assert not Dimensions(length=math.nan).is_dimensionless()
    assert not hasattr(METER, "dimension")
