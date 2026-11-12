"""整数二进制出口的符号和位模式合同。 / Sign and bit-pattern contracts for integer binary export."""

from __future__ import annotations

import operator
import random
import sys
from typing import Any

import pytest

from ospf_python import _native
from ospf_python.math.algebra.number.integer import Integer
from ospf_python.math.algebra.number.numeric_integer import NumericInteger
from ospf_python.math.algebra.number.numeric_u_integer import NumericUInteger
from ospf_python.math.algebra.number.uinteger import UInteger

_BITS = (
    0,
    1,
    7,
    8,
    15,
    16,
    29,
    30,
    31,
    32,
    33,
    60,
    61,
    62,
    63,
    64,
    65,
    66,
    127,
    128,
    129,
    255,
    256,
    257,
    1023,
    1024,
    16385,
    100000,
)
_OPERATIONS = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "floor-divide": operator.floordiv,
}


@pytest.mark.parametrize("bits", _BITS)
def test_signed_dense_sparse_and_carry_patterns_preserve_complete_results(
    bits: int,
) -> None:
    rng = random.Random(bits)
    base = 1 << bits
    values = (base - 1, base, base + 1, base | rng.getrandbits(bits))
    previous = sys.get_int_max_str_digits()
    outer = RuntimeError()
    try:
        sys.set_int_max_str_digits(640)
        try:
            raise outer
        except RuntimeError:
            for magnitude in values:
                for sign in (-1, 1):
                    left = sign * magnitude
                    for right in (-((1 << 65) + 3), -1, 3, (1 << 65) + 3):
                        for operation, expected in _OPERATIONS.items():
                            actual = _native._public_integer.binary(
                                left=left, right=right, operation=operation
                            )
                            assert type(actual) is int
                            assert actual == expected(left, right)
                            assert sys.exception() is outer
                    negated = _native._public_integer.negated(left)
                    assert type(negated) is int and negated == -left
                    assert sys.exception() is outer
    finally:
        sys.set_int_max_str_digits(previous)


@pytest.mark.parametrize("cls", (Integer, UInteger, NumericInteger, NumericUInteger))
def test_public_domains_keep_dense_multiword_results_and_constructor_policy(
    cls: Any,
) -> None:
    rng = random.Random(301)
    for bits in (63, 64, 65, 128, 1024, 16385, 100000):
        magnitude = (1 << bits) | rng.getrandbits(bits)
        for value in (-magnitude, magnitude):
            if cls is NumericUInteger and value < 0:
                continue
            left, right = cls(value), cls(3)
            for operation in ("add", "multiply"):
                expected = (
                    left.value + right.value
                    if operation == "add"
                    else left.value * right.value
                )
                if cls is NumericInteger:
                    expected = max(cls.MIN_VALUE, min(cls.MAX_VALUE, expected))
                    result = (
                        left.safe_add(right)
                        if operation == "add"
                        else left.safe_mul(right)
                    )
                else:
                    result = left + right if operation == "add" else left * right
                assert type(result) is cls and result.value == expected
