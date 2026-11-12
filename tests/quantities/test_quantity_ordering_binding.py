"""公开数量极值/范围的原生合同。 / Native contracts for public quantity extrema and ranges."""

from __future__ import annotations

import gc
import importlib
import math
import pickle
import subprocess
import sys
import weakref
from dataclasses import asdict, dataclass, fields
from decimal import Decimal, Inexact, localcontext
from fractions import Fraction
from types import SimpleNamespace
from typing import Any, cast

import pytest

from ospf_python import _native
from ospf_python._binding import quantity_ordering as _ordering
from ospf_python._binding import unit_conversion as _conversion
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
)
from ospf_python.quantities.unit.length import KILOMETER, METER, Length
from ospf_python.quantities.unit.mass import KILOGRAM
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result


@dataclass(frozen=True)
class _Value:
    value: Fraction


class _Adapter(NumericAdapter[_Value]):
    def to_fraction(self, value: _Value) -> Result[Fraction, Any, Any]:
        return Ok(value.value)

    def from_fraction(self, value: Fraction) -> Result[_Value, Any, Any]:
        pytest.fail("ordering must not reconstruct a custom value")


def _value(*, domain: str, numerator: int) -> Any:
    if domain == "fraction":
        return Fraction(numerator, 4)
    if domain == "decimal":
        return Decimal(numerator) / 4
    if domain == "private-rational":
        return Rational.create(numerator=numerator, denominator=4).unwrap()
    if domain == "public-rational":
        return PublicRational(numerator, 4)
    if domain == "float":
        return numerator / 4
    if domain == "floating":
        return Floating(numerator / 4)
    if domain == "custom":
        return _Value(Fraction(numerator, 4))
    return numerator


_DOMAINS = (
    "int",
    "fraction",
    "decimal",
    "private-rational",
    "public-rational",
    "float",
    "floating",
    "custom",
)
_OPERATIONS = ("min", "max", "contains")


def _call(*, operation: str, items: list[Any], adapter: Any = None) -> Any:
    if operation == "contains":
        return QuantityValueRange(min_qty=items[1], max_qty=items[0]).contains(
            items[2], numeric_adapter=adapter
        )
    function = min_quantity if operation == "min" else max_quantity
    return function(iter(items), numeric_adapter=adapter)


@pytest.mark.parametrize(
    "family", list(_families.values()), ids=lambda family: family.cls.__name__
)
@pytest.mark.parametrize("domain", _DOMAINS)
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_all_33_families_and_eight_domains_use_original_items_or_boolean(
    *, family: Any, domain: str, operation: str
) -> None:
    items = [
        Quantity(value=_value(domain=domain, numerator=n), unit=family.cls())
        for n in (12, 4, 8)
    ]
    result = _call(
        operation=operation,
        items=items,
        adapter=_Adapter() if domain == "custom" else None,
    )
    assert result.unwrap() is (
        True
        if operation == "contains"
        else items[1]
        if operation == "min"
        else items[0]
    )


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
def test_all_223_constants_keep_precision_guards_and_positive_order(
    *, unit: Any, operation: str
) -> None:
    assert len(_constants()) == 223
    items = [Quantity(value=Fraction(n, 7), unit=unit) for n in (14, 0, 7)]
    result = _call(operation=operation, items=items)
    if (
        unit
        is importlib.import_module("ospf_python.quantities.unit.mass").ATOMIC_MASS_UNIT
    ):
        assert isinstance(result, Failed) and result.error.code is ErrorCode.DATA_LOSS
    else:
        assert result.unwrap() is (
            True
            if operation == "contains"
            else items[1]
            if operation == "min"
            else items[0]
        )


@pytest.mark.parametrize("function", (min_quantity, max_quantity))
def test_exact_mixed_domains_huge_values_and_first_ties(function: Any) -> None:
    first: Any = Quantity(value=10**1000 + 1, unit=METER)
    second = Quantity(value=10**1000 + 2, unit=METER)
    assert function([first, second]).unwrap() is (
        first if function is min_quantity else second
    )
    first = Quantity(value=Fraction(1, 10), unit=KILOMETER)
    tie = Quantity(value=Decimal("100.000"), unit=METER)
    assert function([first, tie]).unwrap() is first
    below = Quantity(value=Fraction(1, 10), unit=METER)
    above = Quantity(value=0.1, unit=METER)
    assert function([above, below]).unwrap() is (
        below if function is min_quantity else above
    )


@pytest.mark.parametrize("operation", _OPERATIONS)
def test_decimal_context_is_not_used_for_exact_si_ordering(operation: str) -> None:
    items = [
        Quantity(
            value=Decimal(text), unit=Length(_factor=cast("Any", Decimal("0.125")))
        )
        for text in (
            "3.000000000000000000001",
            "1.000000000000000000001",
            "2.000000000000000000001",
        )
    ]
    with localcontext() as context:
        context.prec = 1
        context.traps[Inexact] = True
        context.clear_flags()
        result = _call(operation=operation, items=items)
        assert result.unwrap() is (
            True
            if operation == "contains"
            else items[1]
            if operation == "min"
            else items[0]
        )
        assert not any(context.flags.values())


@pytest.mark.parametrize("operation", _OPERATIONS)
def test_builtin_dimensions_are_checked_without_reading_symbols(operation: str) -> None:
    items = [
        Quantity(value=3, unit=METER),
        Quantity(value=1, unit=METER),
        Quantity(value=2, unit=KILOGRAM),
    ]
    result = _call(operation=operation, items=items)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )


@pytest.mark.parametrize(
    "value",
    (
        math.inf,
        -math.inf,
        math.nan,
        Floating(math.inf),
        Decimal("NaN"),
        Decimal("sNaN"),
        True,
        object(),
    ),
)
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_builtin_invalid_domains_do_not_become_successful_comparisons(
    *, value: Any, operation: str
) -> None:
    result = _call(operation=operation, items=[Quantity(value=value, unit=METER)] * 3)
    assert isinstance(result, Failed)


@pytest.mark.parametrize("function", (min_quantity, max_quantity))
def test_empty_single_ties_and_one_pass_no_length_or_float(function: Any) -> None:
    result = function([])
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )
    item = Quantity(value=Fraction(1, 3), unit=METER)

    class Once:
        def __iter__(self) -> Any:
            assert not hasattr(self, "used")
            self.used = True
            yield item
            yield item

        def __len__(self) -> int:
            pytest.fail("no length hint")

    assert function(Once()).unwrap() is item


@pytest.mark.parametrize("operation", _OPERATIONS)
def test_open_callback_keys_are_opaque_and_do_not_call_float(operation: str) -> None:
    calls: list[Any] = []

    class Key:
        def __init__(self, value: int) -> None:
            self.value = value

        def __float__(self) -> float:
            pytest.fail("implicit float")

        def __lt__(self, other: Any) -> Any:
            calls.append(("lt", self.value, other.value))
            return self.value < other.value

        def __gt__(self, other: Any) -> Any:
            calls.append(("gt", self.value, other.value))
            return self.value > other.value

        def __le__(self, other: Any) -> Any:
            calls.append(("le", self.value, other.value))
            return self.value <= other.value

    class Open:
        def to_si(self, value: Any) -> Any:
            calls.append(("source", value.value))
            return value

    items = [Quantity(value=Key(n), unit=Open()) for n in (3, 1, 2)]  # type: ignore[arg-type]
    result = _call(operation=operation, items=items)
    assert result.unwrap() is (
        True
        if operation == "contains"
        else items[1]
        if operation == "min"
        else items[0]
    )
    assert sum(row[0] == "source" for row in calls) == 3
    if operation == "contains":
        assert calls == [
            ("source", 1),
            ("source", 3),
            ("source", 2),
            ("le", 1, 2),
            ("le", 2, 3),
        ]


def test_open_mixed_exact_comparison_exports_fraction_only_at_boundary() -> None:
    seen = []

    class Key:
        def __lt__(self, other: Any) -> Any:
            seen.append(other)
            return False

    key = Key()
    owner: Any = Quantity(value=key, unit=SimpleNamespace(to_si=lambda value: value))
    exact = Quantity(value=Decimal("1.25"), unit=METER)
    assert min_quantity([exact, owner]).unwrap() is exact
    assert seen == [Fraction(5, 4)] and type(seen[0]) is Fraction


@pytest.mark.parametrize(
    "exception_type",
    (
        ValueError,
        TypeError,
        OverflowError,
        RuntimeError,
        StopIteration,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ),
)
@pytest.mark.parametrize(
    "stage",
    ("source-unit", "source-method", "source-value", "source-key", "comparison"),
)
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_original_external_errors_and_base_exception_contract(
    *, exception_type: type[BaseException], stage: str, operation: str
) -> None:
    class Unformattable(exception_type):  # type: ignore[misc,valid-type]
        def __str__(self) -> str:
            pytest.fail("must not format an external error")

    error = Unformattable()

    def fail() -> Any:
        raise error

    class Key:
        def __lt__(self, other: Any) -> Any:
            return fail()

        def __gt__(self, other: Any) -> Any:
            return fail()

        def __le__(self, other: Any) -> Any:
            return fail()

    class Open:
        @property
        def to_si(self) -> Any:
            if stage == "source-method":
                return fail()
            return lambda value: fail() if stage == "source-key" else value

    class Owner:
        @property
        def unit(self) -> Any:
            return fail() if stage == "source-unit" else Open()

        @property
        def value(self) -> Any:
            return fail() if stage == "source-value" else Key()

    def call() -> Any:
        return _call(operation=operation, items=[Owner(), Owner(), Owner()])

    if issubclass(exception_type, Exception):
        result = call()
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
        assert result.error.value.callback_index == (
            (2 if operation == "contains" else 1) if stage == "comparison" else 0
        )
        assert result.error.message.endswith(stage)
        assert error.__traceback__ is not None
    else:
        with pytest.raises(exception_type) as raised:
            call()
        assert raised.value is error


def test_iterator_error_and_native_failure_stop_before_later_items() -> None:
    error = RuntimeError("iterator")

    def source() -> Any:
        yield Quantity(value=1, unit=METER)
        raise error

    result = min_quantity(source())
    assert isinstance(result, Failed) and result.error.value.callback_exception is error
    assert result.error.value.callback_index == 1

    def invalid() -> Any:
        yield Quantity(value=1, unit=Length(_factor=0))
        pytest.fail("continued past failed input")

    assert min_quantity(invalid()).is_failed()


def test_failed_numeric_adapter_result_is_preserved_without_export() -> None:
    from ospf_python._binding.result import invalid

    failure: Any = invalid("expected / 预期")

    class Adapter:
        def to_fraction(self, value: Any) -> Any:
            return failure

        def from_fraction(self, value: Any) -> Any:
            pytest.fail("ordering export")

    result = min_quantity(
        [Quantity(value=object(), unit=METER)], numeric_adapter=Adapter()
    )
    assert isinstance(result, Failed) and result.error.value.callback_result is failure


def test_range_eager_si_import_then_comparison_short_circuit_and_late_bounds() -> None:
    calls: list[Any] = []

    class Key:
        def __le__(self, other: Any) -> Any:
            calls.append("compare")
            return False

    def key(value: Any) -> Any:
        calls.append(value)
        return Key()

    unit: Any = SimpleNamespace(to_si=key)
    bounds: Any = QuantityValueRange(
        min_qty=Quantity(value="lower", unit=unit),
        max_qty=Quantity(value="upper", unit=unit),
    )
    assert bounds.contains(Quantity(value="candidate", unit=unit)).unwrap() is False
    assert calls == ["lower", "upper", "candidate", "compare"]

    def lower(value: Any) -> Any:
        object.__setattr__(bounds, "max_qty", Quantity(value=3, unit=METER))
        return 1

    object.__setattr__(
        bounds, "min_qty", Quantity(value=0, unit=SimpleNamespace(to_si=lower))
    )
    assert bounds.contains(Quantity(value=2, unit=METER)).unwrap() is True


def test_known_dimensions_remain_checked_even_if_an_opaque_item_wins() -> None:
    class Key:
        def __lt__(self, other: Any) -> Any:
            return True

    opaque: Any = Quantity(value=Key(), unit=SimpleNamespace(to_si=lambda value: value))
    result = min_quantity(
        [Quantity(value=1, unit=METER), opaque, Quantity(value=1, unit=KILOGRAM)]
    )
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )


def test_original_failure_identity_no_old_python_kernel_and_no_instance_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ospf_python._binding.result import invalid

    failure: Any = invalid("unit failure / 单位失败")
    monkeypatch.setattr(Unit, "convert_exact", lambda *args, **kwargs: failure)
    result = min_quantity([Quantity(value=1, unit=METER)])
    assert result is failure
    monkeypatch.undo()
    value = Quantity(value=Fraction(1, 3), unit=METER)
    bounds = QuantityValueRange(min_qty=value, max_qty=value)
    assert min_quantity([value]).unwrap() is value
    assert bounds.contains(value).unwrap() is True
    assert set(vars(value)) == {"value", "unit"}
    assert set(vars(bounds)) == {"min_qty", "max_qty"}


def test_reentry_and_released_inputs_do_not_leave_global_owners() -> None:
    class Open:
        def to_si(self, value: Any) -> Any:
            assert min_quantity([Quantity(value=1, unit=METER)]).unwrap().value == 1
            return value

    owner: Any = Quantity(value=2, unit=cast("Any", Open()))
    reference = weakref.ref(owner)
    result = min_quantity([owner])
    assert result.unwrap() is owner
    del owner, result
    gc.collect()
    assert reference() is None


def test_generic_range_dto_and_closed_reversed_bounds() -> None:
    low = Quantity(value=Fraction(1, 3), unit=METER)
    high = Quantity(value=Fraction(2, 3), unit=METER)
    bounds = QuantityValueRange[Fraction](min_qty=low, max_qty=high)
    assert [field.name for field in fields(bounds)] == ["min_qty", "max_qty"]
    assert pickle.loads(pickle.dumps(bounds)) == bounds
    assert asdict(bounds)["min_qty"]["value"] == Fraction(1, 3)
    assert bounds.contains(low).unwrap() and bounds.contains(high).unwrap()
    assert not QuantityValueRange(min_qty=high, max_qty=low).contains(low).unwrap()


@pytest.mark.parametrize(
    "module",
    (
        "ospf_python._binding.quantity_ordering",
        "ospf_python.quantities.quantity.min_max",
        "ospf_python.quantities.quantity.value_range",
        "ospf_python.quantities",
        "ospf_python._binding.quantity_conversion",
        "ospf_python._binding.unit_conversion",
    ),
)
def test_fresh_import_orders_do_not_introduce_cycles(module: str) -> None:
    code = "import importlib,os,sys; handles=[os.add_dll_directory(path) for path in os.environ.get('OSPF_NATIVE_DLL_DIRS','').split(os.pathsep) if path] if os.name=='nt' else []; importlib.import_module(sys.argv[1]); from ospf_python.quantities import Quantity,min_quantity,QuantityValueRange; from ospf_python.quantities.unit.length import METER; q=Quantity(value=1,unit=METER); assert min_quantity([q]).unwrap() is q; assert QuantityValueRange(q,q).contains(q).unwrap() is True"
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, module],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_private_endpoints_are_in_the_current_extension() -> None:
    assert callable(_native._quantity_extreme) and callable(_native._quantity_contains)


@pytest.mark.parametrize("function", (min_quantity, max_quantity))
@pytest.mark.parametrize("raw", (None, object(), Ok(3)))
def test_single_opaque_none_object_and_result_are_not_unwrapped(
    *, function: Any, raw: Any
) -> None:
    owner: Any = Quantity(value=raw, unit=SimpleNamespace(to_si=lambda value: value))
    assert function([owner]).unwrap() is owner


@pytest.mark.parametrize("operation", _OPERATIONS)
def test_rich_comparison_truth_errors_and_handled_state(operation: str) -> None:
    error = RuntimeError("truth")
    ambient = ValueError("ambient")
    le_calls = 0

    class Truth:
        def __bool__(self) -> bool:
            assert sys.exception() is ambient
            raise error

    class Key:
        def __lt__(self, other: Any) -> Any:
            return Truth()

        def __gt__(self, other: Any) -> Any:
            return Truth()

        def __le__(self, other: Any) -> Any:
            nonlocal le_calls
            le_calls += 1
            if operation == "contains" and le_calls == 1:
                return True
            return Truth()

    unit: Any = SimpleNamespace(to_si=lambda value: value)
    try:
        raise ambient
    except ValueError:
        result = _call(
            operation=operation, items=[Quantity(value=Key(), unit=unit)] * 3
        )
        assert (
            isinstance(result, Failed)
            and result.error.value.callback_exception is error
        )
        assert error.__context__ is ambient and sys.exception() is ambient
        if operation == "contains":
            assert le_calls == 2
    assert sys.exception() is None


def test_late_coefficient_snapshots_are_per_item_and_not_cached_between_calls() -> None:
    unit = Length(_factor=1)
    first = Quantity(value=10, unit=unit)
    second = Quantity(value=1, unit=unit)

    def items() -> Any:
        yield first
        object.__setattr__(unit, "_factor", 100)
        yield second

    assert min_quantity(items()).unwrap() is first
    assert min_quantity([first, second]).unwrap() is second


def test_open_units_do_not_read_symbol_or_unknown_metadata() -> None:
    class Open:
        def __getattribute__(self, name: str) -> Any:
            if name in ("symbol", "_symbol", "_factor", "_offset", "dimension"):
                pytest.fail("speculative unit metadata read")
            return object.__getattribute__(self, name)

        def to_si(self, value: Any) -> Any:
            return value

    unit: Any = Open()
    lower = Quantity(value=Fraction(1, 3), unit=unit)
    upper = Quantity(value=Fraction(2, 3), unit=unit)
    assert min_quantity([lower, upper]).unwrap() is lower
    assert QuantityValueRange(min_qty=lower, max_qty=upper).contains(lower).unwrap()


def test_streamed_losers_and_winner_have_no_untraversed_native_owners() -> None:
    references = []

    def items() -> Any:
        for value in range(100):
            owner = Quantity(value=value, unit=METER)
            references.append(weakref.ref(owner))
            yield owner

    result = min_quantity(items())
    gc.collect()
    assert sum(reference() is not None for reference in references) == 1
    del result
    gc.collect()
    assert all(reference() is None for reference in references)


@pytest.mark.parametrize("function", (min_quantity, max_quantity))
@pytest.mark.parametrize("raw", (None, object(), Ok(3)))
def test_source_lane_changes_before_dispatch_keep_opaque_owner(
    *, function: Any, raw: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _conversion._Dispatch.source
    method = cast("Any", Length.to_si)

    def changed(self: Any, value: Any) -> Any:
        return value

    def dispatch(self: Any, *, unit: Any, callback: Any, value: Any) -> Any:
        monkeypatch.setattr(method, "__code__", changed.__code__)
        return source(self, unit=unit, callback=callback, value=value)

    monkeypatch.setattr(_conversion._Dispatch, "source", dispatch)
    owner: Any = Quantity(value=raw, unit=METER)
    assert function([owner]).unwrap() is owner


@pytest.mark.parametrize("operation", _OPERATIONS)
def test_source_lane_changes_before_dispatch_keep_open_comparisons(
    *, operation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _conversion._Dispatch.source
    method = cast("Any", Length.to_si)

    def changed(self: Any, value: Any) -> Any:
        return value

    def dispatch(self: Any, *, unit: Any, callback: Any, value: Any) -> Any:
        monkeypatch.setattr(method, "__code__", changed.__code__)
        return source(self, unit=unit, callback=callback, value=value)

    monkeypatch.setattr(_conversion._Dispatch, "source", dispatch)
    items: list[Any] = [Quantity(value=value, unit=METER) for value in (3, 1, 2)]
    assert _call(operation=operation, items=items).unwrap() is (
        True if operation == "contains" else items[1 if operation == "min" else 0]
    )


@pytest.mark.parametrize("previous", (False, True))
def test_open_standard_objects_cannot_claim_native_provenance(previous: bool) -> None:
    keys = _ordering._Keys(None)
    assert keys.prepare((METER, METER.to_si, 1))[1] == 0
    standard = keys.dispatch.standard
    assert standard is not None
    raw = (
        standard
        if previous
        else _conversion._Standard(standard.value, standard.unit, int)
    )
    callback = lambda value: raw
    unit = SimpleNamespace(to_si=callback)
    success, kind, result, powers = keys.prepare((unit, callback, None))
    assert success and kind == 2 and result is raw and powers is None
    assert keys.dispatch.standard is None


@pytest.mark.parametrize("operation", _OPERATIONS)
def test_each_key_uses_one_existing_family_guard(operation: str) -> None:
    calls = 0
    code = native_family.__code__
    previous = sys.getprofile()

    def profile(frame: Any, event: str, arg: Any) -> None:
        nonlocal calls
        if event == "call" and frame.f_code is code:
            calls += 1

    items: list[Any] = [Quantity(value=value, unit=METER) for value in (3, 1, 2)]
    try:
        sys.setprofile(profile)
        result = _call(operation=operation, items=items)
    finally:
        sys.setprofile(previous)
    assert result.unwrap() is (
        True if operation == "contains" else items[1 if operation == "min" else 0]
    )
    assert calls == 3
