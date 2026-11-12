"""浮点原生边界的名称身份与精确除法。 / Attribute-name identity and exact division at the floating boundary."""

from __future__ import annotations

import operator
import struct
import sys
from typing import Any

import pytest

from ospf_python.math.algebra.number.floating import Floating

_DIVISION_PAIRS = (
    (0, 3),
    (1, 3),
    ((1 << 31) + 1, 3),
    ((1 << 53) + 1, 3),
    ((1 << 53) + 3, 7),
    ((1 << 62) + 3, (1 << 61) + 7),
    (-(1 << 63), -1),
    ((1 << 63) - 1, -(1 << 63)),
    (1 << 63, 3),
    ((1 << 64) + 3, 7),
    ((1 << 1024) + 7, 3),
    (1, 1 << 1074),
    (1, 1 << 1075),
    (3, 1 << 1075),
    (1, 1 << 10000),
    ((1 << 10000) + 7, 3),
)


@pytest.mark.parametrize(("left", "right"), _DIVISION_PAIRS)
@pytest.mark.parametrize("left_sign", (-1, 1))
@pytest.mark.parametrize("right_sign", (-1, 1))
def test_integer_true_division_matches_python_rounding_and_original_errors(
    *, left: int, right: int, left_sign: int, right_sign: int
) -> None:
    left *= left_sign
    right *= right_sign
    try:
        expected = left / right
    except OverflowError as reference:
        with pytest.raises(OverflowError) as caught:
            Floating(left) / Floating(right)
        assert caught.value.args == reference.args
    else:
        actual = (Floating(left) / Floating(right)).value
        assert type(actual) is float
        assert struct.pack("!d", actual) == struct.pack("!d", expected)


@pytest.mark.parametrize(
    "operation",
    (operator.add, operator.sub, operator.mul, operator.truediv, operator.neg),
)
@pytest.mark.parametrize("integral_payload", (False, True))
def test_dynamic_attribute_access_receives_original_interned_name_identities(
    *, operation: Any, integral_payload: bool
) -> None:
    names = {name: sys.intern(name) for name in ("value", "__class__")}
    events: list[tuple[str, bool]] = []

    class Observed(Floating):
        def __getattribute__(self, name: str) -> Any:
            if name in names:
                events.append((name, name is names[name]))
            return super().__getattribute__(name)

    left = Observed(7 if integral_payload else 7.0)
    right = Observed(3 if integral_payload else 3.0)
    if operation is operator.neg:
        result = operation(left)
        expected_names = ["__class__", "value"]
    else:
        result = operation(left, right)
        expected_names = ["__class__", "value", "value"]
        if operation is operator.truediv:
            expected_names.insert(0, "value")
    assert events == [(name, True) for name in expected_names]
    assert type(result) is Observed
