"""公共分形入口的固定 Rust 合同。 / Pinned-Rust contracts for the public fractal entry points."""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from ospf_python import _native
from ospf_python.math.fractal.julia_set import JuliaSet
from ospf_python.math.fractal.mandelbrot_set import MandelbrotSet
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Warn


def _reference_escape(z: complex, c: complex, max_iterations: int) -> int:
    """测试专用冻结算法，不是生产 fallback。 / Test-only frozen algorithm, not a production fallback."""
    current = z
    for iteration in range(max_iterations):
        if current.real * current.real + current.imag * current.imag > 4.0:
            return iteration
        current = current * current + c
    return max_iterations


def _grid() -> Iterator[complex]:
    for real in (-2.0, -1.5, -0.75, 0.0, 0.25, 1.0, 2.0):
        for imag in (-1.5, -0.25, 0.0, 0.25, 1.5):
            yield complex(real, imag)


@pytest.mark.parametrize("c", tuple(_grid()))
def test_mandelbrot_iterate_matches_frozen_algorithm(c: complex) -> None:
    assert MandelbrotSet.iterate(c, 37).unwrap() == _reference_escape(
        complex(0.0, 0.0), c, 37
    )


@pytest.mark.parametrize("z", tuple(_grid()))
def test_julia_iterate_matches_frozen_algorithm(z: complex) -> None:
    c = complex(-0.7, 0.27015)
    assert JuliaSet.iterate(z, c, 53).unwrap() == _reference_escape(z, c, 53)


@pytest.mark.parametrize(
    "value",
    [
        complex(0.0, 0.0),
        complex(math.nan, 0.0),
        complex(math.inf, 0.0),
        complex(-math.inf, math.nan),
    ],
)
def test_nonfinite_inputs_follow_pinned_escape_comparisons(value: complex) -> None:
    expected = _reference_escape(complex(0.0, 0.0), value, 19)
    assert MandelbrotSet.iterate(value, 19).unwrap() == expected


def test_private_native_boundary_exposes_structured_transport() -> None:
    value, error = _native._fractal_escape_time(
        z=0j,
        c=0j,
        max_iterations=32,
    )
    assert (value, error) == (32, None)

    value, error = _native._fractal_escape_time(
        z=0j,
        c=0j,
        max_iterations=0,
    )
    assert value is None
    assert error is not None
    assert error.category == "ILLEGAL_ARGUMENT"


@pytest.mark.parametrize(
    ("limit", "expected"),
    [
        (0, 0),
        (-1, -1),
        (-(1 << 100), -(1 << 100)),
        (False, 0),
    ],
)
def test_nonpositive_limits_preserve_historical_values(
    limit: int,
    expected: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_call(*_: Any, **__: Any) -> tuple[int | None, Any]:
        raise AssertionError("nonpositive limit must not enter native iteration")

    monkeypatch.setattr(_native, "_fractal_escape_time", unexpected_call)
    assert MandelbrotSet.iterate(complex(0.0, 0.0), limit).unwrap() == expected
    assert MandelbrotSet(max_iter=limit).contains(complex(0.0, 0.0)).unwrap() == (
        expected == limit
    )


def test_true_limit_runs_one_native_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def native_call(*arguments: Any, **_: Any) -> tuple[int | None, Any]:
        calls.append(arguments[2])
        return 1, None

    monkeypatch.setattr(_native, "_fractal_escape_time", native_call)
    assert MandelbrotSet.iterate(complex(0.0, 0.0), True).unwrap() == 1
    assert calls == [1]


def test_positive_limit_beyond_u64_is_resource_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_call(*_: Any, **__: Any) -> tuple[int | None, Any]:
        raise AssertionError("out-of-range limit must not reach native iteration")

    monkeypatch.setattr(_native, "_fractal_escape_time", unexpected_call)
    result = MandelbrotSet.iterate(complex(0.0, 0.0), 1 << 64)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.RESOURCE_EXHAUSTED


def test_index_and_complex_are_read_once_in_historical_order() -> None:
    events: list[str] = []

    class Indexed:
        def __index__(self) -> int:
            events.append("index")
            return 7

    class ComplexValue:
        def __complex__(self) -> complex:
            events.append("complex")
            return complex(-1.0, 0.0)

    assert MandelbrotSet.iterate(ComplexValue(), Indexed()).unwrap() == 7
    assert events == ["index", "complex"]


@pytest.mark.parametrize("method", ["index", "complex"])
def test_input_exception_instance_is_retained(
    method: str,
) -> None:
    failure = ValueError("input failed")

    class BrokenIndex:
        def __index__(self) -> int:
            raise failure

    class BrokenComplex:
        def __complex__(self) -> complex:
            raise failure

    result = (
        MandelbrotSet.iterate(complex(0.0, 0.0), BrokenIndex())
        if method == "index"
        else MandelbrotSet.iterate(BrokenComplex(), 8)
    )
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is failure
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize("method", ["index", "complex"])
def test_base_exception_propagates_unchanged(method: str) -> None:
    failure = KeyboardInterrupt("stop")

    class BrokenIndex:
        def __index__(self) -> int:
            raise failure

    class BrokenComplex:
        def __complex__(self) -> complex:
            raise failure

    with pytest.raises(KeyboardInterrupt) as caught:
        if method == "index":
            MandelbrotSet.iterate(complex(0.0, 0.0), BrokenIndex())
        else:
            MandelbrotSet.iterate(BrokenComplex(), 8)
    assert caught.value is failure


def test_contains_reuses_public_result_relation() -> None:
    mandelbrot = MandelbrotSet(max_iter=50)
    julia = JuliaSet(c_real=-0.7, c_imag=0.27015, max_iter=500)
    assert mandelbrot.contains(complex(-0.5, 0.0)).unwrap() is True
    assert mandelbrot.contains(complex(2.0, 0.0)).unwrap() is False
    assert julia.contains(0.1, 0.1).unwrap() is True
    assert julia.contains(10.0, 10.0).unwrap() is False


def test_contains_publishes_the_existing_frozen_ok() -> None:
    success = MandelbrotSet(max_iter=50).contains(complex(0.0, 0.0))
    assert type(success) is Ok
    assert success.value is success.unwrap()
    assert success.unwrap() is True
    with pytest.raises(FrozenInstanceError):
        success._value = False  # type: ignore[misc]


@pytest.mark.parametrize("method", ["mandelbrot", "julia"])
@pytest.mark.parametrize("variant", ["failed", "fatal", "warn"])
def test_contains_preserves_public_iteration_result_mapping(
    *, method: str, variant: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    failure = MandelbrotSet.iterate(complex(0.0, 0.0), 1 << 64)
    assert isinstance(failure, Failed)
    result: Any = {
        "failed": failure,
        "fatal": Fatal((failure.error,)),
        "warn": Warn(50, failure.error),
    }[variant]
    owner: Any = MandelbrotSet if method == "mandelbrot" else JuliaSet
    monkeypatch.setattr(owner, "iterate", staticmethod(lambda *args: result))
    actual = (
        owner(max_iter=50).contains(0j)
        if method == "mandelbrot"
        else owner(max_iter=50).contains(0.0, 0.0)
    )
    if variant == "warn":
        assert isinstance(actual, Warn)
        assert actual.unwrap() is True
        assert actual.warning is failure.error
    else:
        assert actual is result


def test_iteration_uses_the_current_ok_constructor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = Ok.__init__
    payloads: list[Any] = []

    def record(self: Any, value: Any) -> None:
        payloads.append(value)
        original(self, value)

    monkeypatch.setattr(Ok, "__init__", record)
    assert MandelbrotSet.iterate(0j, 3).unwrap() == 3
    assert JuliaSet.iterate(0j, 0j, 0).unwrap() == 0
    assert payloads == [3, 0]


def test_julia_resolves_public_iteration_after_complex_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def replacement(*args: Any) -> Any:
        events.append("replacement")
        return Ok(50)

    class Real:
        def __float__(self) -> float:
            events.append("complex")
            monkeypatch.setattr(JuliaSet, "iterate", staticmethod(replacement))
            return 0.0

    value: Any = Real()
    assert JuliaSet(c_real=value, max_iter=50).contains(0.0, 0.0).unwrap() is True
    assert events == ["complex", "replacement"]


@pytest.mark.parametrize("method", ["mandelbrot", "julia"])
def test_contains_keeps_the_iteration_failure_classification(method: str) -> None:
    limit = 1 << 64
    if method == "mandelbrot":
        actual = MandelbrotSet(max_iter=limit).contains(complex(0.0, 0.0))
    else:
        actual = JuliaSet(max_iter=limit).contains(0.0, 0.0)
    assert isinstance(actual, Failed)
    assert actual.error.code is ErrorCode.RESOURCE_EXHAUSTED
    assert actual.error.value.error_class == "BOUNDARY"


def test_escape_radius_remains_stored_but_ignored() -> None:
    baseline = JuliaSet(max_iter=40).contains(2.1, 0.0).unwrap()
    changed = JuliaSet(max_iter=40, escape_radius=1e300).contains(2.1, 0.0).unwrap()
    assert changed is baseline


def test_dataclass_identity_and_frozen_fields_are_preserved() -> None:
    julia = JuliaSet()
    mandelbrot = MandelbrotSet()
    assert (julia.c_real, julia.c_imag, julia.max_iter, julia.escape_radius) == (
        -0.7,
        0.27015,
        100,
        2.0,
    )
    assert mandelbrot.max_iter == 100
    with pytest.raises(FrozenInstanceError):
        mandelbrot.max_iter = 101  # type: ignore[misc]
