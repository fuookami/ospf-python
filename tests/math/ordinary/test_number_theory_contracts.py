"""数论有效整数域的迁移合同，尚非原生切换。 / Valid integer-domain migration contracts, not a native cutover."""

from __future__ import annotations

import gc
import math
import random
import weakref
from typing import Any

import numpy as np
import pytest

from ospf_python.math.ordinary.factorization import prime_factors
from ospf_python.math.ordinary.gcd import extended_gcd, gcd
from ospf_python.math.ordinary.lcm import lcm

_INTEGERS = (-(2**127), -(2**63), -15, -1, 0, 1, 7, 2**63, 2**127, 2**1024 + 13)
_NONNEGATIVE = (0, 1, 3, 15, 2**63, 2**127, 2**1024, 2**2048 + 1)


def _pairs() -> list[tuple[int, int]]:
    randomizer = random.Random(20261027)
    return [
        (randomizer.getrandbits(bits), -randomizer.getrandbits(bits))
        for bits in (8, 64, 128, 1024)
        for _ in range(8)
    ]


@pytest.mark.parametrize("operation", ("gcd", "lcm"))
@pytest.mark.parametrize("a", _INTEGERS)
@pytest.mark.parametrize("b", _INTEGERS)
def test_signed_zero_and_arbitrary_precision_integer_domain(
    *, operation: str, a: int, b: int
) -> None:
    function = gcd if operation == "gcd" else lcm
    expected = math.gcd(a, b) if operation == "gcd" else math.lcm(a, b)
    output = function(a, b)
    assert type(output) is int and output == expected and output >= 0


@pytest.mark.parametrize("operation", ("gcd", "lcm"))
@pytest.mark.parametrize(("a", "b"), _pairs())
def test_seeded_integer_pairs_keep_full_precision(
    *, operation: str, a: int, b: int
) -> None:
    function = gcd if operation == "gcd" else lcm
    expected = math.gcd(a, b) if operation == "gcd" else math.lcm(a, b)
    assert function(a, b) == expected


@pytest.mark.parametrize("a", _NONNEGATIVE)
@pytest.mark.parametrize("b", _NONNEGATIVE)
def test_nonnegative_bezout_identity_without_machine_width_narrowing(
    *, a: int, b: int
) -> None:
    divisor, x, y = extended_gcd(a, b)
    assert all(type(value) is int for value in (divisor, x, y))
    assert divisor == math.gcd(a, b)
    assert a * x + b * y == divisor


_FACTORS = [
    (1, []),
    (2, [2]),
    (3, [3]),
    (7, [7]),
    (12, [2, 2, 3]),
    (49, [7, 7]),
    (60, [2, 2, 3, 5]),
    (7919, [7919]),
    *[(2**bits, [2] * bits) for bits in (8, 63, 64, 127, 256, 1024, 4096)],
    (3**500, [3] * 500),
    (5**256, [5] * 256),
    (7**100, [7] * 100),
    (2**64 * 3**33 * 5**11, [2] * 64 + [3] * 33 + [5] * 11),
]


@pytest.mark.parametrize(
    ("number", "expected"),
    _FACTORS,
    ids=[f"factor-{index}" for index in range(len(_FACTORS))],
)
def test_full_positive_integer_factorization_including_large_smooth_values(
    *, number: int, expected: list[int]
) -> None:
    output = prime_factors(number)
    assert output == expected
    assert all(type(value) is int for value in output)
    assert math.prod(output) == number


@pytest.mark.parametrize("operation", ("gcd", "lcm"))
@pytest.mark.parametrize("a", (0, 7, 2**127, -(2**256)))
@pytest.mark.parametrize("b", (0, 3, 2**63, -(2**128)))
def test_index_protocol_is_consumed_once_in_left_to_right_order(
    *, operation: str, a: int, b: int
) -> None:
    events: list[str] = []

    class Index:
        def __init__(self, *, name: str, value: int) -> None:
            self.name, self.value = name, value

        def __index__(self) -> int:
            events.append(self.name)
            return self.value

    # 旧注解未表达__index__；此合同检查实际开放调用边界。 / Legacy annotations omit the actual open __index__ boundary.
    function: Any = gcd if operation == "gcd" else lcm
    expected = math.gcd(a, b) if operation == "gcd" else math.lcm(a, b)
    assert (
        function(Index(name="left", value=a), Index(name="right", value=b)) == expected
    )
    assert events == ["left", "right"]


@pytest.mark.parametrize("operation", ("gcd", "lcm"))
@pytest.mark.parametrize("value", (True, False, np.int64(-17), np.uint64(2**64 - 1)))
def test_bool_and_real_numpy_integer_inputs_are_integer_protocols(
    *, operation: str, value: Any
) -> None:
    function = gcd if operation == "gcd" else lcm
    expected = math.gcd(value, 3) if operation == "gcd" else math.lcm(value, 3)
    output = function(value, 3)
    assert type(output) is int and output == expected


@pytest.mark.parametrize("operation", ("gcd", "lcm"))
def test_int_subclass_cannot_replace_its_stored_integer_by_index_override(
    operation: str,
) -> None:
    class Integer(int):
        def __index__(self) -> int:
            pytest.fail(
                "真实整数子类不读取覆盖 / Do not read an override for a real int subclass"
            )

    function = gcd if operation == "gcd" else lcm
    assert function(Integer(12), Integer(8)) == (4 if operation == "gcd" else 24)


@pytest.mark.parametrize("operation", ("gcd", "lcm"))
def test_completed_calls_do_not_retain_index_input_owners(operation: str) -> None:
    class Index:
        def __index__(self) -> int:
            return 12

    function: Any = gcd if operation == "gcd" else lcm
    value = Index()
    reference = weakref.ref(value)
    assert function(value, 8) == (4 if operation == "gcd" else 24)
    del value
    gc.collect()
    assert reference() is None
