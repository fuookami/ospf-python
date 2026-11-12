"""浮点门面的完整域与动态协议基线。 / Full-domain and dynamic-protocol baselines for Floating."""

from __future__ import annotations

import copy
import math
import operator
import pickle
import struct
import sys
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from fractions import Fraction
from typing import Any, cast

import numpy as np
import pytest

import ospf_python.utils.functional.ord as ord_module
from ospf_python.math.algebra.number.floating import Floating

_OPERATIONS = (operator.add, operator.sub, operator.mul, operator.truediv)
_VALUES = (
    (0.0, -0.0),
    (-0.0, 0.0),
    (1.25, -3.5),
    (sys.float_info.max, sys.float_info.max),
    (sys.float_info.min, -sys.float_info.min),
    (float.fromhex("0x0.0000000000001p-1022"), 0.5),
    (math.inf, -math.inf),
    (math.inf, math.inf),
    (math.nan, 3.0),
    (3.0, math.nan),
)


def _same_float(actual: Any, expected: float) -> None:
    assert type(actual) is float
    if math.isnan(expected):
        assert math.isnan(actual)
    else:
        assert struct.pack("!d", actual) == struct.pack("!d", expected)


@pytest.mark.parametrize("operation", _OPERATIONS)
@pytest.mark.parametrize(("left", "right"), _VALUES)
def test_ieee_arithmetic_preserves_domain_rounding_and_signed_zero(
    *, operation: Any, left: float, right: float
) -> None:
    expected = (
        0.0
        if operation is operator.truediv and right == 0.0
        else operation(left, right)
    )
    _same_float(operation(Floating(left), Floating(right)).value, expected)


@pytest.mark.parametrize("value", (0.0, -0.0, math.inf, -math.inf, math.nan, 1e-320))
def test_negation_preserves_ieee_specials(value: float) -> None:
    _same_float((-Floating(value)).value, -value)


@pytest.mark.parametrize("operation", _OPERATIONS)
@pytest.mark.parametrize(
    ("left", "right"),
    (
        (7, 3),
        (2**10000, 2**9999),
        (-1, 2**10000),
        (0, -3),
        (True, False),
        (1.5, 3),
        (3, 1.5),
        (Fraction(7, 3), Fraction(2, 5)),
        (Decimal("1.25"), Decimal("2.50")),
        (1.0 + 2.0j, 3.0 - 4.0j),
        (np.float64(1.25), np.float64(2.5)),
    ),
)
def test_non_float_fields_keep_existing_numeric_domains(
    *, operation: Any, left: Any, right: Any
) -> None:
    expected = (
        0.0
        if operation is operator.truediv and right == 0.0
        else operation(left, right)
    )
    actual = operation(Floating(left), Floating(right)).value
    assert type(actual) is type(expected)
    if isinstance(expected, float):
        _same_float(float(actual), float(expected))
    else:
        assert actual == expected


@pytest.mark.parametrize("operation", _OPERATIONS)
@pytest.mark.parametrize("reverse", (False, True))
def test_mixed_float_huge_integer_keeps_conversion_overflow(
    *, operation: Any, reverse: bool
) -> None:
    left, right = (1.5, 2**10000) if reverse else (2**10000, 1.5)
    with pytest.raises(OverflowError) as reference:
        operation(left, right)
    with pytest.raises(OverflowError) as caught:
        operation(Floating(left), Floating(right))
    assert caught.value.args == reference.value.args


@pytest.mark.parametrize(
    "name", ("__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__")
)
@pytest.mark.parametrize(
    ("left", "right"), ((math.nan, math.nan), (0.0, -0.0), (math.inf, 2.0), (3.0, 4.0))
)
def test_comparison_and_nan_are_not_replaced_by_a_total_float_order(
    *, name: str, left: float, right: float
) -> None:
    assert getattr(Floating(left), name)(Floating(right)) is getattr(left, name)(right)
    if math.isnan(left):
        assert Floating(left).cmp(Floating(right)) is ord_module.Order.EQ


def test_dto_fields_copy_pickle_and_dynamic_cmp_remain_python_integration() -> None:
    value = float("1.25")
    source = Floating(value)
    assert source.value is value and source.copy().value is value
    assert [field.name for field in fields(source)] == ["value"]
    assert list(source.__dict__) == ["value"]
    with pytest.raises(FrozenInstanceError):
        source.value = 7.0  # type: ignore[misc]
    object.__setattr__(source, "extra", [source, source])
    for cloned in (copy.deepcopy(source), pickle.loads(pickle.dumps(source))):
        restored: Any = cloned
        assert cloned is not source and cloned.value == value
        assert restored.extra[0] is restored.extra[1] is cloned

    class Custom(Floating):
        def cmp(self, other: Any) -> Any:
            return marker

    marker = object()
    assert Custom(1.0).partial_cmp(cast("Any", Floating(2.0))) is marker
    assert Floating(1.0).__eq__(1.0) is NotImplemented
    assert Floating(1.0).__ne__(1.0) is NotImplemented


@pytest.mark.parametrize(
    ("name", "expected"),
    (
        ("zero", 0.0),
        ("one", 1.0),
        ("two", 2.0),
        ("three", 3.0),
        ("five", 5.0),
        ("ten", 10.0),
        ("half", 0.5),
        ("min_value", -math.inf),
        ("max_value", math.inf),
        ("positive_inf", math.inf),
        ("negative_inf", -math.inf),
        ("nan", math.nan),
    ),
)
def test_all_constant_properties_keep_subclass_construction(
    *, name: str, expected: float
) -> None:
    class Custom(Floating):
        pass

    actual = getattr(Custom(7.0), name)
    assert type(actual) is Custom
    _same_float(actual.value, expected)


@pytest.mark.parametrize("first", (0.0, -0.0, 2.0))
def test_division_guard_and_second_read_keep_constructor_and_field_order(
    first: float,
) -> None:
    events: list[Any] = []
    values = iter((first, 4.0))

    def constructor(value: Any) -> Any:
        events.append(("construct", value))
        return Floating(value)

    class Left(Floating):
        def __getattribute__(self, name: str) -> Any:
            if name == "__class__":
                events.append("class")
                return constructor
            if name == "value":
                events.append("left")
            return super().__getattribute__(name)

    class Right(Floating):
        def __getattribute__(self, name: str) -> Any:
            if name == "value":
                events.append("right")
                return next(values)
            return super().__getattribute__(name)

    result = cast("Any", Left(8.0)) / Right(7.0)
    assert result.value == (0.0 if first == 0.0 else 2.0)
    assert events == (
        ["right", "class", ("construct", 0.0)]
        if first == 0.0
        else ["right", "class", "left", "right", ("construct", 2.0)]
    )


def test_second_divisor_read_can_raise_instead_of_using_zero_sentinel() -> None:
    values = iter((1.0, 0.0))

    class Right(Floating):
        def __getattribute__(self, name: str) -> Any:
            return next(values) if name == "value" else super().__getattribute__(name)

    with pytest.raises(ZeroDivisionError, match=r"(float )?division by zero"):
        Floating(7.0) / Right(3.0)


@pytest.mark.parametrize("operation", _OPERATIONS)
@pytest.mark.parametrize(
    "error_type", (RuntimeError, KeyboardInterrupt, SystemExit, GeneratorExit)
)
def test_external_failure_keeps_original_traceback_and_handled_exception(
    *, operation: Any, error_type: type[BaseException]
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    outer = ValueError()

    class External:
        def __eq__(self, other: Any) -> bool:
            return False

        def __add__(self, other: Any) -> Any:
            assert sys.exception() is outer
            raise error

        __sub__ = __mul__ = __truediv__ = __add__

        def __float__(self) -> float:
            pytest.fail("不能转型外部协议 / External protocols must not be coerced")

    try:
        raise outer
    except ValueError:
        with pytest.raises(error_type) as caught:
            operation(
                Floating(cast("Any", External())), Floating(cast("Any", External()))
            )
        assert caught.value is error and sys.exception() is outer
    node = error.__traceback__
    assert node is not None
    while node is not None and node is not original:
        node = node.tb_next
    assert node is original


def test_float_subclass_reflected_hooks_and_non_bool_comparison_survive() -> None:
    marker = object()

    class External(float):
        def __radd__(self, other: Any) -> Any:
            return marker

        def __lt__(self, other: Any) -> Any:
            return marker

        def __float__(self) -> float:
            pytest.fail("不能抽取子类载荷 / Subclass payload must not be extracted")

    assert (Floating(7.0) + Floating(External(3.0))).value is marker
    assert Floating(External(3.0)).__lt__(Floating(7.0)) is marker


def test_zero_guard_keeps_the_same_literal_identity_for_result_construction() -> None:
    seen: list[Any] = []

    class External:
        def __eq__(self, other: Any) -> bool:
            seen.append(other)
            return True

    result = Floating(7.0) / Floating(cast("Any", External()))
    assert len(seen) == 1 and result.value is seen[0]


def test_ephemeral_operands_release_left_then_right_before_result_construction() -> (
    None
):
    events: list[str] = []
    published = object()

    class Leaf:
        def __init__(self, label: str) -> None:
            self.label = label

        def __add__(self, other: Any) -> Any:
            events.append("arithmetic")
            return Leaf("result")

        def __del__(self) -> None:
            events.append("del-" + self.label)

    def constructor(value: Any) -> Any:
        assert value.label == "result"
        events.append("construct")
        return published

    class Left(Floating):
        def __getattribute__(self, name: str) -> Any:
            if name == "__class__":
                events.append("class")
                return constructor
            if name == "value":
                events.append("left")
                return Leaf("left")
            return super().__getattribute__(name)

    class Right(Floating):
        def __getattribute__(self, name: str) -> Any:
            if name == "value":
                events.append("right")
                return Leaf("right")
            return super().__getattribute__(name)

    assert cast("Any", Left(7.0)) + Right(3.0) is published
    assert events == [
        "class",
        "left",
        "right",
        "arithmetic",
        "del-left",
        "del-right",
        "construct",
        "del-result",
    ]
