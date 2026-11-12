"""原生规范结果的构造作用域合同 / Scoped construction contracts for canonical native results."""

from __future__ import annotations

import gc
import weakref
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Self, cast

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.math.algebra.number.rational import Rational


def test_tuple_return_without_constructor_and_unreduced_negation() -> None:
    assert _native._public_rational_binary(
        left=(6, 8), right=(2, 8), operation="add"
    ) == (1, 1)
    assert _native._public_rational_negated((6, 8)) == (-3, 4)
    restored = Rational.__new__(Rational)
    restored.__dict__.update(numerator=6, denominator=8)
    assert -restored == Rational(-3, 4)
    assert restored + Rational(1, 4) == Rational(1)


def test_only_identical_canonical_arguments_reuse_constructor_evidence() -> None:
    n = (1 << 2048) + 3
    captured: list[tuple[int, int]] = []

    def construct(num: int, den: int) -> Rational:
        captured.append((num, den))
        normalized = _native._public_rational_normalize(num, den)
        assert normalized[0] is num and normalized[1] is den
        return Rational(num, den * 2)

    value = _native._public_rational_binary(
        left=(n, 17), right=(n, 17), operation="add", constructor=construct
    )
    assert value == Rational(n, 17)
    num, den = captured[0]
    outside = _native._public_rational_normalize(num, den)
    assert outside == (num, den) and outside[0] is not num


def test_nested_construction_restores_outer_evidence_without_holding_a_borrow() -> None:
    n = (1 << 1024) + 1

    def outer(num: int, den: int) -> Rational:
        def inner(inner_num: int, inner_den: int) -> Rational:
            assert (
                _native._public_rational_normalize(inner_num, inner_den)[0] is inner_num
            )
            assert _native._public_rational_normalize(num, den)[0] is not num
            return Rational(inner_num, inner_den)

        result = _native._public_rational_binary(
            left=(num, den),
            right=(num, den),
            operation="add",
            constructor=inner,
        )
        assert _native._public_rational_normalize(num, den)[0] is num
        assert result == Rational(num * 2, den)
        return Rational(num, den)

    assert _native._public_rational_negated((n, 17), constructor=outer) == Rational(
        -n, 17
    )


@pytest.mark.parametrize("error", [ValueError("constructor"), KeyboardInterrupt()])
def test_constructor_failure_identity_and_evidence_cleanup(
    error: BaseException,
) -> None:
    captured: list[tuple[int, int]] = []

    def broken(num: int, den: int) -> Rational:
        captured.append((num, den))
        assert _native._public_rational_normalize(num, den)[0] is num
        raise error

    with pytest.raises(type(error)) as raised:
        _native._public_rational_negated(((1 << 512) + 1, 17), constructor=broken)
    assert raised.value is error
    num, den = captured[0]
    assert _native._public_rational_normalize(num, den)[0] is not num
    assert Rational(1, 3) + Rational(2, 3) == Rational(1)


def test_proof_does_not_cross_threads_or_keep_the_constructor_alive() -> None:
    class Construct:
        def __call__(self, num: int, den: int) -> Rational:
            with ThreadPoolExecutor(max_workers=1) as executor:
                normalized = executor.submit(
                    _native._public_rational_normalize, num, den
                ).result(timeout=10)
                result = executor.submit(
                    lambda: Rational(1, 3) + Rational(2, 3)
                ).result(timeout=10)
            assert normalized == (num, den) and normalized[0] is not num
            assert result == Rational(1)
            assert _native._public_rational_normalize(num, den)[0] is num
            return Rational(num, den)

    constructor = Construct()
    reference = weakref.ref(constructor)
    value = _native._public_rational_negated(
        ((1 << 512) + 1, 17), constructor=constructor
    )
    del constructor
    gc.collect()
    assert reference() is None
    assert set(vars(value)) == {"numerator", "denominator"}


@pytest.mark.parametrize("mode", ["negative", "zero", "numpy"])
def test_modified_constructor_inputs_are_validated_normally(mode: str) -> None:
    def construct(num: int, den: int) -> Rational:
        if mode == "negative":
            return Rational(num * 3, -den * 3)
        if mode == "zero":
            return Rational(num, 0)
        return Rational(cast("int", np.int64(num)), cast("int", np.int64(den)))

    value = _native._public_rational_binary(
        left=(1, 3), right=(1, 3), operation="add", constructor=construct
    )
    expected = {
        "negative": Rational(-2, 3),
        "zero": Rational(0),
        "numpy": Rational(2, 3),
    }
    assert value == expected[mode]
    if mode == "numpy":
        assert type(cast("object", value.numerator)) is np.int64
        assert type(cast("object", value.denominator)) is np.int64


def test_subclass_post_init_and_result_constructor_are_not_bypassed() -> None:
    events: list[str] = []

    class Derived(Rational):
        def __init__(self, numerator: int, denominator: int = 1) -> None:
            events.append("init")
            super().__init__(numerator, denominator)

        def __post_init__(self) -> None:
            events.append("post_init")
            super().__post_init__()

        def __neg__(self) -> Self:
            events.append("neg")
            return super().__neg__()

    value = Derived(1, 3)
    operations: tuple[Callable[[], Derived], ...] = (
        lambda: value + value,
        lambda: value * value,
        lambda: value / value,
    )
    for operation in operations:
        events.clear()
        assert type(operation()) is Derived
        assert events == ["init", "post_init"]
    events.clear()
    assert type(-value) is Derived
    assert events == ["neg", "init", "post_init"]


def test_subclass_post_init_can_change_a_field_before_normalization() -> None:
    class Halved(Rational):
        def __post_init__(self) -> None:
            object.__setattr__(self, "denominator", self.denominator * 2)
            super().__post_init__()

    value = Halved(2, 3)
    assert value == Rational(1, 3)
    assert value + value == Rational(1, 3)
    assert value * value == Rational(1, 18)
    assert -value == Rational(-1, 6)


def test_nested_python_failure_restores_the_outer_scope() -> None:
    error = ValueError("nested constructor")

    def outer(num: int, den: int) -> Rational:
        def broken(inner_num: int, inner_den: int) -> Rational:
            assert (
                _native._public_rational_normalize(inner_num, inner_den)[0] is inner_num
            )
            raise error

        with pytest.raises(ValueError) as raised:
            _native._public_rational_negated((num, den), constructor=broken)
        assert raised.value is error
        assert _native._public_rational_normalize(num, den)[0] is num
        return Rational(num, den)

    result = _native._public_rational_negated(((1 << 512) + 1, 17), constructor=outer)
    assert result == Rational(-((1 << 512) + 1), 17)


@pytest.mark.parametrize("operation", ["add", "multiply", "divide", "negate"])
def test_result_constructor_is_captured_before_operand_field_getters(
    operation: str,
) -> None:
    events: list[str] = []
    watched: object = None

    class Recording(Rational):
        def __getattribute__(self, name: str) -> object:
            if self is watched and name in {"__class__", "numerator", "denominator"}:
                events.append(name)
            return super().__getattribute__(name)

    value = Recording(1, 3)
    other = Recording(1, 5)
    watched = value
    operations: dict[str, Callable[[], Recording]] = {
        "add": lambda: value + other,
        "multiply": lambda: value * other,
        "divide": lambda: value / other,
        "negate": lambda: -value,
    }
    result = operations[operation]()
    assert events == ["__class__", "numerator", "denominator"]
    assert type(result) is Recording
