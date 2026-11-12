"""公共整数对到固定 Rust 数值域的合同 / Contracts for public pairs and the pinned Rust domain."""

from __future__ import annotations

import copy
import pickle
import random
import sys
import weakref
from collections.abc import Callable
from dataclasses import asdict, fields, replace
from fractions import Fraction
from typing import ClassVar, Self

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.numeric import Rational as StrictRational
from ospf_python.math.algebra.number.rational import Rational


class TaggedRational(Rational):
    """额外状态及自引用仍由 Python 对象图协议管理 / Python graph protocols retain extra and cyclic state."""

    def __init__(self, numerator: int, denominator: int = 1) -> None:
        super().__init__(numerator, denominator)
        self.tag: list[object] = []


class RecordingRational(Rational):
    """记录实际子类构造，不用 __new__ 绕过 / Record actual subclass construction, without bypassing it via __new__."""

    calls: ClassVar[list[tuple[int, int]]] = []

    def __init__(self, numerator: int, denominator: int = 1) -> None:
        self.calls.append((numerator, denominator))
        super().__init__(numerator, denominator)


@pytest.mark.parametrize("bits", [8, 64, 257, 2048, 16000])
def test_all_exact_operations_and_order_against_fraction(bits: int) -> None:
    rng = random.Random(20261025 + bits)
    for _ in range(12):
        a = Fraction(
            rng.getrandbits(bits) - (1 << (bits - 1)), rng.getrandbits(bits) + 1
        )
        b = Fraction(rng.getrandbits(bits) + 1, -(rng.getrandbits(bits) + 1))
        left = Rational(a.numerator, a.denominator)
        right = Rational(b.numerator, b.denominator)
        for result, expected in (
            (left + right, a + b),
            (left - right, a - b),
            (left * right, a * b),
            (left / right, a / b),
            (-left, -a),
        ):
            assert (result.numerator, result.denominator) == expected.as_integer_ratio()
            assert set(vars(result)) == {"numerator", "denominator"}
        assert (left < right, left <= right, left > right, left >= right) == (
            a < b,
            a <= b,
            a > b,
            a >= b,
        )


def test_default_public_routes_invoke_native_without_a_python_numeric_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    normalize = _native._public_rational_normalize
    binary = _native._public_rational_binary
    less = _native._public_rational_less
    negated = _native._public_rational_negated

    def trace_normalize(n: object, d: object) -> tuple[int, int]:
        calls.append("normalize")
        return normalize(n, d)

    def trace_binary[R](
        *,
        left: tuple[int, int],
        right: tuple[int, int],
        operation: str,
        constructor: Callable[[int, int], R],
    ) -> R:
        calls.append(operation)
        return binary(
            left=left, right=right, operation=operation, constructor=constructor
        )

    def trace_less(left: tuple[int, int], right: tuple[int, int]) -> bool:
        calls.append("less")
        return less(left, right)

    def trace_negated[R](
        value: tuple[int, int], *, constructor: Callable[[int, int], R]
    ) -> R:
        calls.append("negated")
        return negated(value, constructor=constructor)

    monkeypatch.setattr(_native, "_public_rational_normalize", trace_normalize)
    monkeypatch.setattr(_native, "_public_rational_binary", trace_binary)
    monkeypatch.setattr(_native, "_public_rational_less", trace_less)
    monkeypatch.setattr(_native, "_public_rational_negated", trace_negated)
    a, b = Rational(1, 2), Rational(1, 3)
    assert a + b == Rational(5, 6)
    assert a - b == Rational(1, 6)
    assert a * b == Rational(1, 6)
    assert a / b == Rational(3, 2)
    assert -a == Rational(-1, 2)
    assert b < a
    assert {"normalize", "add", "multiply", "divide", "negated", "less"} <= set(calls)


def test_subclass_constructor_gets_canonical_native_results() -> None:
    value = RecordingRational(1, 2)
    RecordingRational.calls.clear()
    assert value + value == Rational(1)
    assert RecordingRational.calls == [(1, 1)]
    RecordingRational.calls.clear()
    base: Rational = value
    assert base / Rational(0) == Rational(0)
    assert RecordingRational.calls == [(0, 1)]


def test_composed_subtraction_and_reflected_order_still_dispatch_hooks() -> None:
    events: list[str] = []

    class CustomRational(Rational):
        def __neg__(self) -> Self:
            events.append("neg")
            return super().__neg__()

        def __add__(self, other: Self) -> Self:
            events.append("add")
            return super().__add__(other)

        def __lt__(self, other: Self) -> bool:
            events.append("lt")
            return super().__lt__(other)

    a, b = CustomRational(1, 2), CustomRational(1, 3)
    assert a - b == Rational(1, 6)
    assert events == ["neg", "add"]
    events.clear()
    assert a >= b and a > b and a <= a
    assert events == ["lt", "lt", "lt"]


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_copy_and_deepcopy_retain_subclass_graphs(protocol: int) -> None:
    value = TaggedRational((1 << 1000) + 3, 17)
    value.tag.append(value)
    graph = [value, value, value.tag]
    restored = pickle.loads(pickle.dumps(graph, protocol=protocol))
    assert restored[0] is restored[1]
    assert restored[2] is restored[0].tag
    assert restored[0].tag[0] is restored[0]
    assert type(restored[0]) is TaggedRational
    assert restored[0] + TaggedRational(1) == value + TaggedRational(1)
    cloned = copy.deepcopy(value)
    assert type(cloned) is TaggedRational and cloned.tag[0] is cloned
    shallow = copy.copy(value)
    assert type(shallow) is TaggedRational and shallow.tag is value.tag


def test_public_fields_are_the_only_persistent_value_and_legacy_state_is_operable() -> (
    None
):
    value = Rational.__new__(Rational)
    value.__dict__.update(numerator=3, denominator=7)
    assert value + Rational(4, 7) == Rational(1)
    assert vars(value) == {"numerator": 3, "denominator": 7}
    assert [field.name for field in fields(value)] == ["numerator", "denominator"]
    assert asdict(replace(value, numerator=6)) == {"numerator": 6, "denominator": 7}
    ref = weakref.ref(value)
    del value
    assert ref() is None


@pytest.mark.parametrize(
    "n,d", [(True, True), (False, -7), (np.int64(6), np.int64(-8))]
)
def test_integer_protocol_normalization(n: int, d: int) -> None:
    value = Rational(n, d)
    expected = Fraction(int(n), int(d))
    assert asdict(value) == dict(
        zip(("numerator", "denominator"), expected.as_integer_ratio(), strict=True)
    )
    scalar_type = np.int64 if isinstance(n, np.integer) else int
    assert type(value.numerator) is type(value.denominator) is scalar_type


def test_external_integer_normalization_keeps_index_floor_and_sign_hooks() -> None:
    events: list[str] = []

    class ExternalInteger:
        def __init__(self, value: int) -> None:
            self.value = value

        def __index__(self) -> int:
            events.append(f"index:{self.value}")
            return self.value

        def __floordiv__(self, other: int) -> int:
            events.append(f"floor:{self.value}:{other}")
            return self.value // other

        def __eq__(self, other: object) -> bool:
            events.append(f"eq:{self.value}")
            return self.value == other

    value = Rational(ExternalInteger(6), ExternalInteger(-8))  # type: ignore[arg-type]
    assert value == Rational(-3, 4)
    assert events == ["eq:-8", "index:6", "index:-8", "floor:6:2", "floor:-8:2"]


def test_constructor_exception_identity_and_zero_short_circuit() -> None:
    error = ValueError("external index failure")

    class BrokenInteger:
        def __index__(self) -> int:
            raise error

    assert Rational(BrokenInteger(), 0) == Rational(0)  # type: ignore[arg-type]
    with pytest.raises(ValueError) as raised:
        Rational(BrokenInteger(), 1)  # type: ignore[arg-type]
    assert raised.value is error
    assert StrictRational.create(numerator=3, denominator=0).is_failed()
    assert (
        StrictRational.create(numerator=1)
        .unwrap()
        .divide(StrictRational.create(numerator=0).unwrap())
        .is_failed()
    )


@pytest.mark.parametrize(
    "n,d",
    [
        (1, 3),
        (1, 1 << 1075),
        (-1, 1 << 1075),
        ((1 << 1024) - (1 << 970), 1),
        (1 << 4000, 1 << 3999),
    ],
)
def test_float_export_remains_the_cpython_ratio_conversion(n: int, d: int) -> None:
    value = Rational(n, d)
    try:
        expected = n / d
    except OverflowError:
        with pytest.raises(OverflowError):
            _ = value.float_value
    else:
        assert value.float_value.hex() == expected.hex()


def test_large_integer_bridge_does_not_use_decimal_strings() -> None:
    old_limit = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        value = Rational((1 << 20000) + 1, -17)
        assert value + (-value) == Rational(0)
        assert value / value == Rational(1)
    finally:
        sys.set_int_max_str_digits(old_limit)
