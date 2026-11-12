"""数值错误状态的自然入口合同，不表示已切换。 / Natural numeric error-state contracts, not cutover acceptance."""

from __future__ import annotations

import sys
import warnings
from typing import Any

import numpy as np
import pytest

from ospf_python.math.multiarray.fast_sum import fast_sum
from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape

_DTYPES = (
    "float16",
    "float32",
    "float64",
    "longdouble",
    "complex64",
    "complex128",
    "clongdouble",
)
_DTYPE_AXES = [
    (dtype, axis)
    for dtype in _DTYPES
    for axis in ((0,) if "complex" in dtype or dtype == "clongdouble" else (None, 0))
]


class _Poison(ValueError):
    def __str__(self) -> str:
        raise AssertionError("不得格式化原异常 / Never format the original error")


@pytest.mark.parametrize(("dtype", "axis"), _DTYPE_AXES)
@pytest.mark.parametrize("case", ["over", "invalid"])
@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "log", "print"])
def test_floating_error_modes_apply_at_the_natural_reduction_boundary(
    *,
    dtype: str,
    axis: Any,
    case: str,
    mode: Any,
    capfd: pytest.CaptureFixture[str],
) -> None:
    values = [np.finfo(dtype).max] * 2 if case == "over" else [np.inf, -np.inf]
    data = np.array(values, dtype=dtype)
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2,)), data)
    events: list[tuple[str, int] | str] = []

    def callback(name: str, flags: int) -> None:
        events.append((name, flags))

    class Logger:
        def write(self, message: str) -> None:
            events.append(message)

    previous = np.geterrcall()
    np.seterrcall(Logger() if mode == "log" else callback)
    try:
        with warnings.catch_warnings(record=True) as caught, np.errstate(all=mode):
            warnings.simplefilter("always")
            if mode == "raise":
                with pytest.raises(FloatingPointError, match="encountered in reduce"):
                    fast_sum(source, axis=axis)
            else:
                fast_sum(source, axis=axis)
        assert len(caught) == int(mode == "warn")
        if caught:
            assert "encountered in reduce" in str(caught[0].message)
        assert len(events) == int(mode in ("call", "log"))
        if events and mode == "call":
            assert events == [
                (
                    "overflow" if case == "over" else "invalid value",
                    2 if case == "over" else 8,
                )
            ]
        if events and mode == "log":
            assert "encountered in reduce" in str(events[0])
        stderr = capfd.readouterr().err
        assert ("encountered in reduce" in stderr) is (mode == "print")
    finally:
        np.seterrcall(previous)


@pytest.mark.parametrize("mode", ["call", "log"])
@pytest.mark.parametrize(
    "error_type",
    [
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        StopIteration,
        _Poison,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ],
)
def test_floating_error_handlers_preserve_original_exception_and_handled_state(
    *, mode: Any, error_type: type[BaseException]
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    events: list[BaseException | None] = []
    source: MultiArray[Any, DynShape] = MultiArray(
        DynShape((2,)), np.array([1e308, 1e308])
    )

    def callback(name: str, flags: int) -> None:
        events.append(sys.exception())
        raise error

    class Logger:
        def write(self, message: str) -> None:
            callback(message, 2)

    previous = np.geterrcall()
    np.seterrcall(Logger() if mode == "log" else callback)
    try:
        with np.errstate(all=mode):
            try:
                raise RuntimeError("外层 / Outer")
            except RuntimeError as outer:
                with pytest.raises(error_type) as caught:
                    fast_sum(source, axis=0)
                assert caught.value is error
                assert sys.exception() is outer
                assert error.__context__ is outer
                assert events == [outer]
        chain = []
        node = error.__traceback__
        while node is not None:
            chain.append(node)
            node = node.tb_next
        assert any(node is original for node in chain)
        assert any(node.tb_frame.f_code is callback.__code__ for node in chain)
    finally:
        np.seterrcall(previous)


@pytest.mark.parametrize("change", ["dtype", "errstate", "slots"])
def test_axis_protocol_changes_precede_numeric_dtype_and_error_policy_selection(
    change: str,
) -> None:
    data = (
        np.array([1e308, 1e308])
        if change == "errstate"
        else np.array([-1, 2], dtype=np.int8)
    )
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2,)), data)

    class Axis:
        def __index__(self) -> int:
            if change == "dtype":
                mutable_storage: Any = data
                mutable_storage.dtype = np.dtype(np.uint8)
            elif change == "errstate":
                np.seterr(over="raise")
            else:
                data[0] = 10
            return 0

    axis: Any = Axis()
    previous = np.seterr(all="ignore")
    try:
        if change == "errstate":
            with pytest.raises(FloatingPointError):
                fast_sum(source, axis=axis)
            assert np.geterr()["over"] == "raise"
        else:
            result = fast_sum(source, axis=axis)
            assert result._data.dtype == np.dtype("int64")
            assert result._data[0] == (1 if change == "dtype" else 12)
    finally:
        np.seterr(**previous)


def test_dtype_change_on_the_captured_reshape_result_is_observed() -> None:
    data = np.array([-1, 2], dtype=np.int8)
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2,)), data)
    captured: list[np.ndarray[Any, Any]] = []

    class Storage:
        def reshape(self, dims: tuple[int, ...]) -> np.ndarray[Any, Any]:
            view = data.reshape(dims)
            captured.append(view)
            return view

    class Axis:
        def __index__(self) -> int:
            mutable_storage: Any = captured[0]
            mutable_storage.dtype = np.dtype(np.uint8)
            return 0

    raw_source: Any = source
    raw_source._data = Storage()
    axis: Any = Axis()
    result = fast_sum(source, axis=axis)
    assert result._data.dtype == np.dtype("uint64")
    assert result._data[0] == 257
    assert data.dtype == np.dtype("int8")


@pytest.mark.parametrize("dtype", _DTYPES)
@pytest.mark.parametrize("dims", [(), (1,)])
@pytest.mark.parametrize("axis", [(), 0, -1])
def test_numeric_empty_axes_and_scalar_axes_are_not_object_leaf_identity(
    *, dtype: str, dims: tuple[int, ...], axis: Any
) -> None:
    data = np.zeros(1, dtype=dtype)
    data.real[:] = -0.0
    if data.dtype.kind == "c":
        data.imag[:] = -0.0
    source: MultiArray[Any, DynShape] = MultiArray(DynShape(dims), data)
    result = fast_sum(source, axis=axis)
    expected = np.asarray(np.sum(data.reshape(dims), axis=axis))
    actual = result._data.reshape(result.shape.dims)
    assert actual.dtype == expected.dtype
    np.testing.assert_array_equal(np.signbit(actual.real), np.signbit(expected.real))
    if actual.dtype.kind == "c":
        np.testing.assert_array_equal(
            np.signbit(actual.imag), np.signbit(expected.imag)
        )
