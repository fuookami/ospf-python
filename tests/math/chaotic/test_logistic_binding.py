"""Logistic 的受限 Rust 候选与现有协议。 / Restricted Rust candidate and existing Logistic protocols."""

from __future__ import annotations

import math
import random
import struct
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.math.chaotic.logistic_map import LogisticMap


def _bits(value: float) -> bytes:
    return struct.pack("!d", value)


def _native_step(*, rate: float, value: float) -> float:
    result, error = _native._logistic_float64_step(rate=rate, value=value)
    assert error is None
    assert type(result) is float
    assert result is not None
    return result


def test_public_step_does_not_silently_dispatch_to_restricted_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(*, rate: object, value: object) -> Any:
        raise AssertionError("the public API has not switched to the candidate")

    monkeypatch.setattr(_native, "_logistic_float64_step", unexpected)
    assert LogisticMap()(0.25) == 3.9 * 0.25 * (1.0 - 0.25)


def test_exact_float_random_bits_match_existing_expression() -> None:
    rng = random.Random(20261029)
    for _ in range(10_000):
        r = struct.unpack("!d", rng.getrandbits(64).to_bytes(8, "big"))[0]
        x = struct.unpack("!d", rng.getrandbits(64).to_bytes(8, "big"))[0]
        expected = r * x * (1.0 - x)
        actual = _native_step(rate=r, value=x)
        if math.isnan(expected):
            assert math.isnan(actual)
        else:
            assert _bits(actual) == _bits(expected)


@pytest.mark.parametrize("rate", [-5.0, 0.0, 1.0, 3.9, 4.0, math.inf])
@pytest.mark.parametrize("initial", [-0.0, 0.1, 0.25, 1.0, math.inf, math.nan])
def test_native_float_multi_step_matches_public_baseline(
    *, rate: float, initial: float
) -> None:
    expected = initial
    actual = initial
    for _ in range(100):
        expected = LogisticMap(r=rate)(expected)
        actual = _native_step(rate=rate, value=actual)
        if math.isnan(expected):
            assert math.isnan(actual)
        else:
            assert _bits(actual) == _bits(expected)


class _FloatSubclass(float):
    def __float__(self) -> float:
        raise AssertionError("must not coerce float subclasses")


class _SpoofedFloat:
    def __getattribute__(self, name: str) -> Any:
        if name == "__class__":
            raise AssertionError("must inspect the real type")
        return super().__getattribute__(name)

    def __float__(self) -> float:
        raise AssertionError("must not coerce numeric objects")


@pytest.mark.parametrize("position", ["rate", "value"])
@pytest.mark.parametrize(
    "factory",
    [
        lambda: 0,
        lambda: True,
        lambda: np.float64(0.25),
        lambda: _FloatSubclass(0.25),
        lambda: _SpoofedFloat(),
    ],
    ids=["integer", "bool", "numpy", "float-subclass", "spoofed"],
)
def test_native_candidate_rejects_other_domains_without_coercion(
    *, position: str, factory: Callable[[], object]
) -> None:
    unsupported = factory()
    rate = unsupported if position == "rate" else 3.9
    value = unsupported if position == "value" else 0.25
    result, error = _native._logistic_float64_step(rate=rate, value=value)
    assert result is None
    assert error is not None
    assert error.category == "ILLEGAL_ARGUMENT"
    assert error.source == "ospf-python-native"
    assert error.rust_code is not None


@pytest.mark.parametrize("r", [0, 3, 3.9, True, 1 << 100])
@pytest.mark.parametrize("x", [0, -2, 0.25, True, 1 << 100])
def test_builtin_numeric_operands_preserve_expression(*, r: Any, x: Any) -> None:
    expected = r * x * (1.0 - x)
    actual = LogisticMap(r=r)(x)
    assert type(actual) is type(expected)
    assert _bits(actual) == _bits(expected)


def test_float_subclasses_keep_numeric_hooks() -> None:
    events: list[str] = []

    class Input(float):
        def __rmul__(self, other: Any) -> Any:
            events.append("multiply")
            return 2.0

        def __rsub__(self, other: Any) -> Any:
            events.append("subtract")
            return 4.0

        def __float__(self) -> float:
            raise AssertionError("must not coerce float subclasses")

    value: Any = Input(0.25)
    assert LogisticMap()(value) == 8.0
    assert events == ["multiply", "subtract"]


def test_numpy_array_and_complex_operands_keep_protocols() -> None:
    values: Any = np.array([0.25, 0.75])
    actual: Any = LogisticMap()(values)
    np.testing.assert_array_equal(actual, 3.9 * values * (1.0 - values))
    value: Any = 0.25 + 0.5j
    assert LogisticMap()(value) == 3.9 * value * (1.0 - value)


def test_open_protocol_releases_temporaries_after_subtraction() -> None:
    events: list[str] = []
    marker = object()

    class Difference:
        def __del__(self) -> None:
            events.append("difference released")

    class Product:
        def __mul__(self, other: object) -> object:
            events.append("second multiply")
            return marker

        def __del__(self) -> None:
            events.append("product released")

    class Rate:
        def __mul__(self, other: object) -> Product:
            events.append("first multiply")
            return Product()

        def __del__(self) -> None:
            events.append("rate released")

    class Input:
        def __rsub__(self, other: object) -> Difference:
            events.append("subtract")
            return Difference()

    class Model(LogisticMap):
        def __getattribute__(self, name: str) -> Any:
            if name == "r":
                events.append("rate read")
                return Rate()
            return super().__getattribute__(name)

    value: Any = Input()
    assert Model()(value) is marker
    # product 与 difference 的相对释放次序随解释器版本变化（CPython 3.15 先释放 difference），
    # 那是临时对象销毁的实现细节；保留「求值顺序固定、两个临时对象都被释放」这两点。
    # The relative release order of product/difference varies by interpreter version; keep the
    # fixed evaluation order and the fact that both temporaries are released.
    assert events[:5] == [
        "rate read",
        "first multiply",
        "rate released",
        "subtract",
        "second multiply",
    ]
    assert sorted(events[5:]) == ["difference released", "product released"]


@pytest.mark.parametrize("stage", ["first", "subtract", "second"])
@pytest.mark.parametrize("exception_type", [ValueError, KeyboardInterrupt])
def test_open_protocol_preserves_exception_instance(
    *, stage: str, exception_type: type[BaseException]
) -> None:
    failure = exception_type(stage)

    class Product:
        def __mul__(self, other: object) -> object:
            if stage == "second":
                raise failure
            return other

    class Rate:
        def __mul__(self, other: object) -> Product:
            if stage == "first":
                raise failure
            return Product()

    class Input:
        def __rsub__(self, other: object) -> object:
            if stage == "subtract":
                raise failure
            return object()

    rate: Any = Rate()
    value: Any = Input()
    with pytest.raises(exception_type) as caught:
        LogisticMap(r=rate)(value)
    assert caught.value is failure


def test_dataclass_and_overridden_iteration_remain_public() -> None:
    class Custom(LogisticMap):
        def __call__(self, value: float) -> float:
            return value + 1.0

    assert Custom().iterate(2.0, n=3) == 5.0
    model = LogisticMap(r=4.0)
    assert repr(model) == "LogisticMap(r=4.0)"
    with pytest.raises(FrozenInstanceError):
        model.r = 3.0  # type: ignore[misc]
