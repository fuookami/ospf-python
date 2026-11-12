"""公共有理数切换前必须保留/审查的合同 / Public rational contracts requiring preservation or review."""

from __future__ import annotations

import copy
import inspect
import json
import pickle
import random
from dataclasses import (
    FrozenInstanceError,
    asdict,
    astuple,
    fields,
    is_dataclass,
    replace,
)
from fractions import Fraction

import pytest

from ospf_python.math.algebra.concept.numbers import RealNumber
from ospf_python.math.algebra.number import Rational
from ospf_python.math.algebra.number.rational import Rational as DeepRational
from ospf_python.utils.functional.ord import Order


class DerivedRational(Rational):
    """验证公开继承与 Self 返回 / Verify public subclassing and Self returns."""


def test_import_identity_signature_dataclass_and_pattern_matching() -> None:
    assert Rational is DeepRational
    assert (
        str(inspect.signature(Rational))
        == "(numerator: 'int', denominator: 'int' = 1) -> None"
    )
    assert is_dataclass(Rational)
    assert [field.name for field in fields(Rational)] == ["numerator", "denominator"]
    assert Rational.__match_args__ == ("numerator", "denominator")
    value = Rational(numerator=6, denominator=-8)
    assert asdict(value) == {"numerator": -3, "denominator": 4}
    assert astuple(value) == (-3, 4)
    assert json.loads(json.dumps(asdict(value))) == {"numerator": -3, "denominator": 4}
    assert replace(value, denominator=8) == Rational(-3, 8)
    match value:
        case Rational(-3, 4):
            pass
        case _:
            pytest.fail("Positional dataclass pattern changed")
    with pytest.raises(FrozenInstanceError):
        value.numerator = 4  # type: ignore[misc]


def test_self_return_protocol_hash_and_representation() -> None:
    value = DerivedRational(6, 8)
    assert isinstance(value, RealNumber)
    for result in (
        value.zero,
        value.one,
        value.copy(),
        -value,
        value + value,
        value - value,
        value * value,
        value / value,
    ):
        assert type(result) is DerivedRational
    assert value == Rational(3, 4)
    assert hash(value) == hash((3, 4))
    assert repr(value) == "Rational(3/4)"
    assert repr(Rational(3)) == "Rational(3)"
    assert value.cmp(Rational(3, 4)) is Order.EQ
    assert value.partial_cmp(Rational(4, 5)) is Order.LT
    assert value.__eq__(1) is NotImplemented
    assert value.__ne__(1) is NotImplemented


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_roundtrip_and_python_copy(protocol: int) -> None:
    value = Rational((1 << 256) + 1, 17)
    for restored in (
        pickle.loads(pickle.dumps(value, protocol=protocol)),
        copy.copy(value),
        copy.deepcopy(value),
    ):
        assert restored == value
        assert type(restored) is Rational
        assert restored + Rational(1) == Rational(value.numerator + 17, 17)


def test_legacy_pickle_with_only_public_fields_remains_loadable() -> None:
    # 迁移前 protocol 0 的固定合同，不接受外部 pickle。 / Fixed pre-migration protocol-0 contract, never external pickle input.
    payload = b"ccopy_reg\n_reconstructor\np0\n(cospf_python.math.algebra.number.rational\nRational\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nVnumerator\np6\nI3\nsVdenominator\np7\nI7\nsb."
    value = pickle.loads(payload)
    assert type(value) is Rational
    assert value == Rational(3, 7)
    assert value + Rational(4, 7) == Rational(1)


def test_existing_zero_behavior_is_not_silently_changed_by_private_result_api() -> None:
    assert Rational(5, 0) == Rational(0, 1)
    assert Rational(5, 7) / Rational(0) == Rational(0)


def test_public_arithmetic_comparison_and_float_against_fraction() -> None:
    rng = random.Random(20261028)
    for _ in range(100):
        a = Fraction(rng.randrange(-(1 << 200), 1 << 200), rng.randrange(1, 1 << 100))
        b = Fraction(rng.randrange(1, 1 << 100), rng.randrange(1, 1 << 100))
        left, right = (
            Rational(a.numerator, a.denominator),
            Rational(b.numerator, b.denominator),
        )
        for actual, expected in (
            (left + right, a + b),
            (left - right, a - b),
            (left * right, a * b),
            (left / right, a / b),
        ):
            assert (actual.numerator, actual.denominator) == (
                expected.numerator,
                expected.denominator,
            )
        assert (left < right) == (a < b)
        assert (left > right) == (a > b)
        assert (left <= right) == (a <= b)
        assert (left >= right) == (a >= b)
        assert left.float_value == float(a)
