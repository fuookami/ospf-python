"""真实精确域的差分与精度合同 / Real exact-domain differential and precision contracts."""

from __future__ import annotations

import gc
import json
import math
import random
import struct
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.numeric import Rational
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


def fraction(value: Rational) -> Fraction:
    return Fraction(*value.as_integer_ratio())


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [(6, -8, (-3, 4)), (0, -9, (0, 1)), (14, 7, (2, 1)), (-2, -4, (1, 2))],
)
def test_rust_normalization(
    *, numerator: int, denominator: int, expected: tuple[int, int]
) -> None:
    value = Rational.create(numerator=numerator, denominator=denominator).unwrap()
    assert value.as_integer_ratio() == expected
    assert isinstance(value._handle, _native.Rational)
    assert not hasattr(value, "__dict__")
    with pytest.raises(FrozenInstanceError):
        value._handle = None  # type: ignore[misc,assignment]
    with pytest.raises(TypeError):
        _native.Rational()


@pytest.mark.parametrize("bad", [True, 1.0, "2", None])
def test_components_require_integer_domain(bad: Any) -> None:
    for result in (
        Rational.create(numerator=bad),
        Rational.create(numerator=1, denominator=bad),
    ):
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_zero_denominator_and_divisor_are_results_without_mutation() -> None:
    assert Rational.create(numerator=1, denominator=0).is_failed()
    value = Rational.create(numerator=2, denominator=3).unwrap()
    zero = Rational.create(numerator=0).unwrap()
    assert value.divide(zero).is_failed()
    assert zero.reciprocal().is_failed()
    assert value.as_integer_ratio() == (2, 3)
    assert value.reciprocal().unwrap().as_integer_ratio() == (3, 2)
    assert value.negated().as_integer_ratio() == (-2, 3)


def test_integer_transport_exceeds_python_decimal_digit_limit() -> None:
    big = (1 << 20000) + 1
    value = Rational.create(numerator=big, denominator=1 << 17000).unwrap()
    assert value.as_integer_ratio() == (big, 1 << 17000)
    text = value.to_json()
    assert len(json.loads(text)["numerator"]) > 4300
    assert (
        Rational.from_json(text).unwrap().as_integer_ratio() == value.as_integer_ratio()
    )
    assert value.add(value).unwrap().as_integer_ratio() == (big, 1 << 16999)


@pytest.mark.parametrize(
    "value", [-(1 << 256), Fraction(-21, 17), Decimal("1.234567890123456789e-90")]
)
def test_exact_python_values_are_not_routed_through_float(value: Any) -> None:
    with localcontext() as context:
        context.prec = 3
        result = Rational.from_value(value).unwrap()
        assert fraction(result) == Fraction(value)


@pytest.mark.parametrize(
    "value", [True, 0.1, "0.1", Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")]
)
def test_implicit_float_or_nonfinite_decimal_is_rejected(value: Any) -> None:
    assert Rational.from_value(value).is_failed()


@pytest.mark.parametrize("value", [0.1, -0.0, 5e-324, 1.7976931348623157e308])
def test_explicit_float_import_preserves_exact_binary_value(value: float) -> None:
    exact = Rational.from_float(value).unwrap()
    assert fraction(exact) == Fraction.from_float(value)
    assert exact.to_float().unwrap() == value


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan, 1, True])
def test_invalid_explicit_float_is_failed(value: Any) -> None:
    assert Rational.from_float(value).is_failed()


def test_random_ieee_values_roundtrip_and_rounded_rationals_match_oracle() -> None:
    randomizer = random.Random(20261026)
    for _ in range(300):
        number = struct.unpack(">d", randomizer.getrandbits(64).to_bytes(8, "big"))[0]
        if math.isfinite(number):
            rational = Rational.from_float(number).unwrap()
            assert fraction(rational) == Fraction.from_float(number)
            assert rational.to_float().unwrap() == number
        value = Fraction(
            randomizer.getrandbits(130) - (1 << 129),
            randomizer.getrandbits(100) + 1,
        )
        assert Rational.from_value(value).unwrap().to_float(
            exact=False
        ).unwrap() == float(value)


@pytest.mark.parametrize(
    ("numerator", "denominator"), [(1, 10), ((1 << 53) + 1, 1), (1, 1 << 2000)]
)
def test_lossy_float_conversion_requires_explicit_policy(
    numerator: int, denominator: int
) -> None:
    value = Rational.create(numerator=numerator, denominator=denominator).unwrap()
    exact = value.to_float()
    assert isinstance(exact, Failed)
    assert exact.error.code is ErrorCode.DATA_LOSS
    assert value.to_float(exact=False).unwrap() == float(
        Fraction(numerator, denominator)
    )
    assert value.to_float(exact=1).is_failed()  # type: ignore[arg-type]


def test_overflow_is_not_returned_as_infinity_even_when_rounding_allowed() -> None:
    value = Rational.create(numerator=1 << 2000).unwrap()
    for exact in (True, False):
        result = value.to_float(exact=exact)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.OVERFLOW


def test_randomized_exact_arithmetic_against_independent_fraction_oracle() -> None:
    randomizer = random.Random(20261025)
    for _ in range(120):
        left = Fraction(
            randomizer.getrandbits(256) - (1 << 255), randomizer.getrandbits(160) + 1
        )
        right = Fraction(
            randomizer.getrandbits(240) - (1 << 239), randomizer.getrandbits(180) + 1
        )
        a, b = Rational.from_value(left).unwrap(), Rational.from_value(right).unwrap()
        assert fraction(a.add(b).unwrap()) == left + right
        assert fraction(a.subtract(b).unwrap()) == left - right
        assert fraction(a.multiply(b).unwrap()) == left * right
        assert fraction(a.divide(b).unwrap()) == left / right
        assert a.compare(b).unwrap() == (left > right) - (left < right)
        assert fraction(a) == left
        assert fraction(b) == right


def test_field_laws_and_value_equality() -> None:
    a = Rational.from_value(Fraction(2, 3)).unwrap()
    b = Rational.from_value(Fraction(5, 7)).unwrap()
    c = Rational.from_value(Fraction(11, 13)).unwrap()
    assert a.add(b).unwrap() == b.add(a).unwrap()
    assert a.add(b).unwrap().add(c).unwrap() == a.add(b.add(c).unwrap()).unwrap()
    assert (
        a.multiply(b.add(c).unwrap()).unwrap()
        == a.multiply(b).unwrap().add(a.multiply(c).unwrap()).unwrap()
    )
    equal = Rational.create(numerator=4, denominator=6).unwrap()
    assert a == equal
    assert hash(a) == hash(equal)
    assert len({a, equal}) == 1
    assert a != 1


@pytest.mark.parametrize(
    "operation", ["add", "subtract", "multiply", "divide", "compare"]
)
def test_invalid_operand_is_a_failed_result(operation: str) -> None:
    value = Rational.from_value(1).unwrap()
    assert getattr(value, operation)(1).is_failed()


@pytest.mark.parametrize(
    "patch",
    [
        {"version": 2},
        {"version": True},
        {"version": 1.0},
        {"schema": "other"},
        {"numerator": 1},
        {"denominator": "0"},
        {"numerator": "01"},
        {"numerator": "+1"},
        {"denominator": " 1"},
        {"extra": "not-accepted"},
    ],
)
def test_snapshot_schema_is_strict(patch: dict[str, Any]) -> None:
    wire = {
        "schema": "ospf.rational",
        "version": 1,
        "numerator": "1",
        "denominator": "2",
    }
    assert Rational.from_json(json.dumps(wire | patch)).is_failed()


@pytest.mark.parametrize("text", ["", "[]", "null", "{}", "NaN", 123])
def test_malformed_snapshot_is_result(text: Any) -> None:
    assert Rational.from_json(text).is_failed()


def test_snapshot_rejects_duplicate_fields() -> None:
    text = '{"schema":"ospf.rational","version":1,"numerator":"1","denominator":"2","numerator":"3"}'
    assert Rational.from_json(text).is_failed()


def test_shared_immutable_rust_value_is_safe_across_threads_and_gc() -> None:
    value = Rational.from_value(Fraction((1 << 300) + 1, 17)).unwrap()
    expected = fraction(value) * 2

    def twice(_: int, captured: Rational = value) -> Fraction:
        return fraction(captured.add(captured).unwrap())

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(result == expected for result in pool.map(twice, range(100)))
    del twice
    child = value.multiply(value).unwrap()
    original = fraction(value)
    del value
    gc.collect()
    assert fraction(child) == original * original
