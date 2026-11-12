"""四类整数的公开协议基线。 / Public protocol baselines for four integer classes.

公共计算已接通原生候选；这些合同不批准缩窄精度或绕过动态协议。
Public arithmetic uses the native candidate; precision narrowing and protocol bypass are not approved.
"""

from __future__ import annotations

import copy
import dataclasses
import importlib
import operator
import pickle
import sys
from typing import Any

import pytest

from ospf_python import utils
from ospf_python.math.algebra.number.integer import Integer
from ospf_python.math.algebra.number.numeric_integer import NumericInteger
from ospf_python.math.algebra.number.numeric_u_integer import NumericUInteger
from ospf_python.math.algebra.number.uinteger import UInteger


class _IntegerSubclass(Integer):
    pass


class _UIntegerSubclass(UInteger):
    pass


class _NumericIntegerSubclass(NumericInteger):
    pass


class _NumericUIntegerSubclass(NumericUInteger):
    pass


_TYPES = (Integer, UInteger, NumericInteger, NumericUInteger)
_SUBCLASSES = (
    _IntegerSubclass,
    _UIntegerSubclass,
    _NumericIntegerSubclass,
    _NumericUIntegerSubclass,
)


@pytest.mark.parametrize("cls", (Integer, UInteger, NumericUInteger))
@pytest.mark.parametrize("bits", (65, 1024, 16385))
@pytest.mark.parametrize("operation", (operator.add, operator.mul))
def test_unbounded_public_domains_keep_values_beyond_machine_words(
    *, cls: Any, bits: int, operation: Any
) -> None:
    left, right = 2**bits + 7, 2**bits + 3
    assert operation(cls(left), cls(right)).value == operation(left, right)


@pytest.mark.parametrize("left", (-17, -7, -1, 0, 1, 7, 17))
@pytest.mark.parametrize("right", (-7, -3, 1, 3, 7))
def test_signed_division_is_floor_not_rust_truncation(left: int, right: int) -> None:
    assert (Integer(left) / Integer(right)).value == left // right


@pytest.mark.parametrize("cls", (Integer, UInteger))
def test_public_division_zero_sentinel_is_distinct_from_strict_factory(
    cls: Any,
) -> None:
    assert (cls(7) / cls(0)).value == 0


@pytest.mark.parametrize("right", (2**1000, -(2**1000), 0))
@pytest.mark.parametrize("operation", ("safe_add", "safe_mul"))
def test_bounded_integer_clamps_result_not_the_raw_rhs(
    *, right: int, operation: str
) -> None:
    left = NumericInteger(-1)
    expected = -1 + right if operation == "safe_add" else -right
    expected = max(NumericInteger.MIN_VALUE, min(NumericInteger.MAX_VALUE, expected))
    assert getattr(left, operation)(right).value == expected


def test_numeric_integer_subclass_bounds_are_followed_by_base_constructor_bounds() -> (
    None
):
    class Wide(NumericInteger):
        MIN_VALUE = -(2**500)
        MAX_VALUE = 2**500

    left = Wide(2**300)
    assert left.value == 2**300
    result = left.safe_add(1)
    assert type(result) is NumericInteger and result.value == NumericInteger.MAX_VALUE
    assert type(left.safe_mul(2)) is NumericInteger


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("value", (True, 7, 2**300))
def test_construction_and_field_dtos_do_not_require_native_handles(
    *, cls: Any, value: int
) -> None:
    source = cls(value)
    field = "_value" if cls in (NumericInteger, NumericUInteger) else "value"
    expected = min(value, NumericInteger.MAX_VALUE) if cls is NumericInteger else value
    assert dataclasses.is_dataclass(source)
    assert not isinstance(source, type)
    assert [entry.name for entry in dataclasses.fields(source)] == [field]
    assert dataclasses.asdict(source) == {field: expected}
    assert dataclasses.replace(source) == source
    if cls is not NumericInteger or value <= NumericInteger.MAX_VALUE:
        assert getattr(source, field) is value


@pytest.mark.parametrize("cls", _SUBCLASSES)
def test_copy_and_pickle_keep_class_aliases_extra_fields_and_cycles(cls: Any) -> None:
    source = cls(7)
    object.__setattr__(source, "extra", [source, source])
    shallow = copy.copy(source)
    assert type(shallow) is cls and shallow.extra is source.extra
    for restored in (copy.deepcopy(source), pickle.loads(pickle.dumps(source))):
        assert type(restored) is cls and restored.value == 7
        assert restored.extra[0] is restored and restored.extra[1] is restored
        assert set(restored.__dict__) == set(source.__dict__)


@pytest.mark.parametrize("cls", (_IntegerSubclass, _UIntegerSubclass))
def test_arithmetic_zero_one_and_copy_preserve_self_class(cls: Any) -> None:
    left, right = cls(7), cls(3)
    for result in (left + right, left - right, left * right, left / right, -left):
        assert type(result) is cls
    for result in (left.zero, left.one, left.copy()):
        assert type(result) is cls and result is not left


def test_numeric_unsigned_has_no_u64_ceiling_and_uses_base_result_class() -> None:
    left = _NumericUIntegerSubclass(2**1000)
    right = _NumericUIntegerSubclass(3)
    for result in (
        left + right,
        left * right,
        left.safe_add(right),
        left.safe_mul(right),
    ):
        assert type(result) is NumericUInteger and result.value > 2**999
    with pytest.raises(ValueError, match="NumericUInteger must be non-negative"):
        NumericUInteger(-1)


def test_unsigned_policies_are_not_the_same_and_generated_order_is_class_sensitive() -> (
    None
):
    assert UInteger(-7).value == 0
    assert (UInteger(3) - UInteger(7)).value == 0
    assert (-UInteger(7)).value == 0
    assert UInteger(7) == _UIntegerSubclass(7)
    assert UInteger.__lt__(UInteger(7), _UIntegerSubclass(8)) is NotImplemented
    assert Integer.__lt__(Integer(7), _IntegerSubclass(8)) is True
    assert NumericInteger(7) == 7 and operator.eq(NumericInteger(1), True)
    assert Integer.__eq__(Integer(7), 7) is NotImplemented
    assert NumericUInteger.__eq__(NumericUInteger(7), 7) is NotImplemented


@pytest.mark.parametrize(
    "method,hook",
    [("__add__", "__add__"), ("__mul__", "__mul__"), ("__sub__", "__sub__")],
)
def test_callable_capture_precedes_fields_and_external_arithmetic_is_not_coerced(
    *, method: str, hook: str
) -> None:
    events: list[str] = []
    marker, other_value, result_marker = object(), object(), object()

    def arithmetic(self: Any, right: Any) -> Any:
        assert right is other_value
        events.append("arithmetic")
        return marker

    value_type = type("ExternalValue", (), {hook: arithmetic})

    def constructor(value: Any) -> Any:
        assert value is marker
        events.append("construct")
        return result_marker

    class Left:
        def __getattribute__(self, name: str) -> Any:
            if name == "__class__":
                events.append("constructor")
                return constructor
            return super().__getattribute__(name)

        @property
        def value(self) -> Any:
            events.append("left")
            return value_type()

    class Right:
        @property
        def value(self) -> Any:
            events.append("right")
            return other_value

    assert getattr(Integer, method)(Left(), Right()) is result_marker
    assert events == ["constructor", "left", "right", "arithmetic", "construct"]


@pytest.mark.parametrize("zero", (True, False))
def test_division_guard_reads_rhs_before_constructor_and_reads_again_when_nonzero(
    zero: bool,
) -> None:
    events: list[str] = []

    def constructor(value: Any) -> Any:
        events.append("construct")
        return value

    class Left:
        def __getattribute__(self, name: str) -> Any:
            if name == "__class__":
                events.append("constructor")
                return constructor
            return super().__getattribute__(name)

        @property
        def value(self) -> int:
            events.append("left")
            return -7

    class Right:
        @property
        def value(self) -> int:
            events.append("right")
            return 0 if zero else 3

    left: Any = Left()
    right: Any = Right()
    assert Integer.__truediv__(left, right) == (0 if zero else -3)
    assert events == (
        ["right", "constructor", "construct"]
        if zero
        else ["right", "constructor", "left", "right", "construct"]
    )


def test_unsigned_negation_does_not_read_the_input_field() -> None:
    class Guarded(UInteger):
        def __post_init__(self) -> None:
            pass

        def __getattribute__(self, name: str) -> Any:
            if name == "value":
                pytest.fail(
                    "无符号取负不得读取源字段 / Unsigned negation must not read the source field"
                )
            return super().__getattribute__(name)

    result = -Guarded(7)
    assert type(result) is Guarded and object.__getattribute__(result, "value") == 0


@pytest.mark.parametrize(
    "error_type",
    (
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        StopIteration,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ),
)
def test_external_integer_arithmetic_preserves_error_identity_traceback_and_state(
    error_type: type[BaseException],
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    outer = RuntimeError("外层处理中异常 / Outer handled exception")
    events: list[str] = []

    class External:
        def __add__(self, right: Any) -> Any:
            assert sys.exception() is outer
            events.append("add")
            raise error

    class Owner:
        value = External()

        def __new__(cls, value: Any = None) -> Any:
            if value is not None:
                pytest.fail("失败后不能构造输出 / No publication after failure")
            return super().__new__(cls)

    try:
        raise outer
    except RuntimeError:
        with pytest.raises(error_type) as caught:
            Integer.__add__(Owner(), Owner())
        assert caught.value is error and error.__context__ is outer
        assert sys.exception() is outer
    node, nodes = error.__traceback__, []
    while node is not None:
        nodes.append(node)
        node = node.tb_next
    assert any(node is original for node in nodes) and events == ["add"]


def test_integer_partial_cmp_keeps_dynamic_cmp_dispatch() -> None:
    class Custom(Integer):
        def cmp(self, other: Any) -> utils.Order:
            return utils.Order.GT

    assert Custom(1).partial_cmp(Custom(2)) is utils.Order.GT


def test_bounded_constructor_keeps_builtin_clamp_order_and_second_value_read() -> None:
    events: list[str] = []

    class Traced(NumericInteger):
        def __getattribute__(self, name: str) -> Any:
            if name in ("MIN_VALUE", "MAX_VALUE", "_value"):
                events.append(name)
            return super().__getattribute__(name)

    result = Traced(7)
    assert events == ["MIN_VALUE", "MAX_VALUE", "_value", "_value"]
    assert result.value == 7


@pytest.mark.parametrize("operation", ("safe_add", "safe_mul"))
def test_bounded_arithmetic_resolves_global_constructor_only_after_clamping(
    *, operation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    module = importlib.import_module(NumericInteger.__module__)
    published = object()

    def constructor(value: Any) -> Any:
        assert value == 9
        events.append("construct")
        return published

    class External:
        def __add__(self, right: Any) -> int:
            assert right == 3
            events.append("arithmetic")
            monkeypatch.setattr(module, "NumericInteger", constructor)
            return 100

        __mul__ = __add__

    class Traced(NumericInteger):
        MIN_VALUE = 2
        MAX_VALUE = 9

        def __post_init__(self) -> None:
            pass

        def __getattribute__(self, name: str) -> Any:
            if name in ("MIN_VALUE", "MAX_VALUE", "_value"):
                events.append(name)
            return super().__getattribute__(name)

    source = Traced(7)
    object.__setattr__(source, "_value", External())
    assert getattr(source, operation)(3) is published
    assert events == ["_value", "arithmetic", "MIN_VALUE", "MAX_VALUE", "construct"]


@pytest.mark.parametrize("operation", ("safe_add", "safe_mul"))
def test_bounded_rhs_field_is_read_before_left_field(operation: str) -> None:
    events: list[str] = []

    class Traced(NumericInteger):
        def __post_init__(self) -> None:
            pass

        def __getattribute__(self, name: str) -> Any:
            if name == "_value":
                events.append(object.__getattribute__(self, "label"))
            return super().__getattribute__(name)

    left, right = Traced(7), Traced(3)
    object.__setattr__(left, "label", "left")
    object.__setattr__(right, "label", "right")
    events.clear()
    assert getattr(left, operation)(right).value == (
        10 if operation == "safe_add" else 21
    )
    assert events == ["right", "left"]


@pytest.mark.parametrize("operation", ("__add__", "__mul__", "safe_add", "safe_mul"))
def test_numeric_unsigned_captures_global_constructor_before_external_arithmetic(
    *, operation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(NumericUInteger.__module__)
    original = NumericUInteger
    marker = object()
    calls: list[Any] = []

    def replacement(value: Any) -> Any:
        calls.append(value)
        return marker

    class External:
        def __add__(self, right: Any) -> int:
            assert right == 3
            monkeypatch.setattr(module, "NumericUInteger", replacement)
            return 11

        __mul__ = __add__

    source = original(7)
    object.__setattr__(source, "_value", External())
    result = getattr(source, operation)(original(3))
    assert type(result) is original and result.value == 11 and calls == []


@pytest.mark.parametrize("operation", ("safe_add", "safe_mul"))
def test_bounded_clamp_looks_up_builtin_hooks_in_the_module(
    *, operation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(NumericInteger.__module__)
    events: list[tuple[str, Any, Any]] = []

    def custom_min(left: Any, right: Any) -> int:
        events.append(("min", left, right))
        return 13

    def custom_max(left: Any, right: Any) -> int:
        events.append(("max", left, right))
        return 17

    source = NumericInteger(7)
    monkeypatch.setattr(module, "min", custom_min, raising=False)
    monkeypatch.setattr(module, "max", custom_max, raising=False)
    result = getattr(source, operation)(3)
    expected = 10 if operation == "safe_add" else 21
    assert events == [
        ("min", NumericInteger.MAX_VALUE, expected),
        ("max", NumericInteger.MIN_VALUE, 13),
        ("min", NumericInteger.MAX_VALUE, 17),
        ("max", NumericInteger.MIN_VALUE, 13),
    ]
    assert result.value == 17


def test_bounded_legacy_reversed_bounds_are_not_the_strict_normalizer_contract() -> (
    None
):
    class ReversedBounds(NumericInteger):
        MIN_VALUE = 9
        MAX_VALUE = 2

    assert ReversedBounds(7).value == 9
    assert ReversedBounds(7).safe_add(-100).value == 9


def test_second_divisor_read_can_fail_instead_of_using_the_zero_sentinel() -> None:
    values = iter((3, 0))

    class Right:
        @property
        def value(self) -> int:
            return next(values)

    right: Any = Right()
    with pytest.raises(ZeroDivisionError):
        Integer(7) / right


@pytest.mark.parametrize("cls", _TYPES)
def test_int_subclass_arithmetic_hooks_are_not_silently_extracted_as_bigint(
    cls: Any,
) -> None:
    calls: list[int] = []

    class ExternalInt(int):
        def __add__(self, right: int) -> int:
            calls.append(right)
            return 23

    value = ExternalInt(7)
    source = cls(value)
    assert source.value is value
    result = source.safe_add(cls(3)) if cls is NumericInteger else source + cls(3)
    assert result.value == 23 and calls == [3]


@pytest.mark.parametrize("cls", _TYPES)
def test_noninteger_field_values_are_an_existing_external_numeric_protocol(
    cls: Any,
) -> None:
    left: Any = 1.5
    right: Any = 2.5
    source = cls(left)
    result = (
        source.safe_add(cls(right)) if cls is NumericInteger else source + cls(right)
    )
    assert type(source.value) is float and result.value == 4.0
