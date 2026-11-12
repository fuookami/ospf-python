"""原生整数快速域的溢出与任意精度合同。 / Overflow and arbitrary-precision contracts for native integer fast paths."""

from __future__ import annotations

import operator
import sys
from typing import Any

import pytest

from ospf_python import _native
from ospf_python.math.algebra.number.integer import Integer
from ospf_python.math.algebra.number.numeric_integer import NumericInteger
from ospf_python.math.algebra.number.numeric_u_integer import NumericUInteger
from ospf_python.math.algebra.number.uinteger import UInteger

_VALUES = (
    -(1 << 100000),
    -(1 << 128) - 1,
    -(1 << 64) - 1,
    -(1 << 63) - 1,
    -(1 << 63),
    -(1 << 63) + 1,
    -7,
    -3,
    -1,
    0,
    1,
    3,
    7,
    (1 << 63) - 1,
    1 << 63,
    (1 << 63) + 1,
    (1 << 64) + 1,
    (1 << 128) + 1,
    1 << 100000,
)
_TYPES = (Integer, UInteger, NumericInteger, NumericUInteger)
_RELATIONS = {
    "eq": operator.eq,
    "ne": operator.ne,
    "lt": operator.lt,
    "le": operator.le,
    "gt": operator.gt,
    "ge": operator.ge,
}


@pytest.mark.parametrize("operation", ("add", "subtract", "multiply", "floor-divide"))
def test_exact_arithmetic_crosses_every_word_boundary_without_wrapping(
    operation: str,
) -> None:
    expected = {
        "add": operator.add,
        "subtract": operator.sub,
        "multiply": operator.mul,
        "floor-divide": operator.floordiv,
    }[operation]
    for left in _VALUES:
        for right in _VALUES:
            if operation == "floor-divide" and right == 0:
                with pytest.raises(ZeroDivisionError):
                    _native._public_integer.binary(
                        left=left, right=right, operation=operation
                    )
            else:
                actual = _native._public_integer.binary(
                    left=left, right=right, operation=operation
                )
                assert type(actual) is int and actual == expected(left, right)


@pytest.mark.parametrize("operation", tuple(_RELATIONS))
def test_range_classification_and_same_sign_large_fallback_keep_total_order(
    operation: str,
) -> None:
    expected = _RELATIONS[operation]
    for left in _VALUES:
        for right in _VALUES:
            assert _native._public_integer.relation(
                left=left, right=right, operation=operation
            ) is expected(left, right)


def test_negation_handles_minimum_word_and_arbitrary_precision() -> None:
    for value in _VALUES:
        assert _native._public_integer.negated(value) == -value


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("operation", ("add", "multiply"))
def test_public_result_construction_keeps_every_domain_after_word_overflow(
    *, cls: Any, operation: str
) -> None:
    for left in _VALUES:
        for right in (-7, 0, 1, 7, (1 << 63) + 1):
            if cls is NumericUInteger and (left < 0 or right < 0):
                continue
            a, b = cls(left), cls(right)
            expected = a.value + b.value if operation == "add" else a.value * b.value
            if cls is NumericInteger:
                expected = max(cls.MIN_VALUE, min(cls.MAX_VALUE, expected))
                result = a.safe_add(b) if operation == "add" else a.safe_mul(b)
            else:
                result = a + b if operation == "add" else a * b
            assert type(result) is cls and result.value == expected


@pytest.mark.parametrize("cls", _TYPES)
def test_range_classification_does_not_extract_int_subclass_or_truthify_comparison(
    cls: Any,
) -> None:
    marker = object()
    calls: list[str] = []

    class External(int):
        def __index__(self) -> int:
            pytest.fail(
                "不能抽取外部整数载荷 / External integer payload must not be extracted"
            )

        def __lt__(self, other: Any) -> Any:
            calls.append("lt")
            return marker

    left, right = cls(7), cls(3)
    field = "_value" if cls in (NumericInteger, NumericUInteger) else "value"
    object.__setattr__(left, field, External(1 << 100000))
    assert cls.__lt__(left, right) is marker and calls == ["lt"]


def test_overflow_markers_do_not_replace_handled_exception_state_or_decimal_policy() -> (
    None
):
    outer = RuntimeError()
    previous = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        try:
            raise outer
        except RuntimeError:
            for left in _VALUES:
                assert _native._public_integer.relation(
                    left=left, right=-1, operation="lt"
                ) is (left < -1)
                assert (
                    _native._public_integer.binary(left=left, right=-1, operation="add")
                    == left - 1
                )
                assert sys.exception() is outer
    finally:
        sys.set_int_max_str_digits(previous)


@pytest.mark.parametrize(
    "bounds",
    ((-(1 << 63), (1 << 63) - 1), (9, 2), (-(1 << 100000), 1 << 100000)),
    ids=("signed64", "reversed", "wide"),
)
def test_clamp_selection_keeps_both_large_bounds_and_first_object_ties(
    bounds: tuple[int, int],
) -> None:
    lower, upper = bounds
    for value in _VALUES:
        expected = max(lower, min(upper, value))
        actual = _native._public_integer.clamp(
            maximum=max, lower=lower, minimum=min, upper=upper, value=value
        )
        assert actual is expected
