"""归约末尾错误合并的自然入口合同。 / Natural contracts for reduction-end floating error aggregation."""

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


class _Poison(ValueError):
    def __str__(self) -> str:
        raise AssertionError("不能格式化原异常 / Never format the original error")


@pytest.mark.parametrize("dtype", _DTYPES)
@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "log", "print"])
def test_multiple_groups_merge_error_flags_at_one_reduction_boundary(
    *, dtype: str, mode: Any, capfd: pytest.CaptureFixture[str]
) -> None:
    maximum = np.finfo(dtype).max
    data = np.array([maximum, maximum, np.inf, -np.inf], dtype=dtype)
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2, 2)), data)
    records: list[tuple[list[object], list[str], str, str | None]] = []
    previous = np.geterrcall()

    def observe(reference: bool) -> tuple[list[object], list[str], str, str | None]:
        events: list[object] = []

        def callback(name: str, flags: int) -> None:
            assert np.geterr()["over"] == mode
            assert np.geterrcall() is handler
            events.append((name, flags))

        class Logger:
            def write(self, message: str) -> None:
                assert np.geterr()["over"] == mode
                assert np.geterrcall() is handler
                events.append(message)

        handler = Logger() if mode == "log" else callback
        np.seterrcall(handler)
        error_message = None
        with warnings.catch_warnings(record=True) as caught, np.errstate(all=mode):
            warnings.simplefilter("always")
            try:
                if reference:
                    np.sum(data.reshape((2, 2)), axis=1)
                else:
                    fast_sum(source, axis=1)
            except FloatingPointError as error:
                assert mode == "raise"
                error_message = str(error)
            else:
                assert mode != "raise"
        return (
            events,
            [str(item.message) for item in caught],
            capfd.readouterr().err,
            error_message,
        )

    try:
        records.extend((observe(True), observe(False)))
        assert records[0] == records[1]
        if mode == "call":
            assert records[1][0] == [("overflow", 10), ("invalid value", 10)]
        if mode == "warn":
            assert len(records[1][1]) == 2
            assert all("encountered in reduce" in text for text in records[1][1])
    finally:
        np.seterrcall(previous)


@pytest.mark.parametrize("dtype", _DTYPES)
@pytest.mark.parametrize("behavior", ["change_policy", "reenter"])
def test_handler_mutation_and_reentry_do_not_change_the_captured_publisher(
    *, dtype: str, behavior: str
) -> None:
    maximum = np.finfo(dtype).max
    source: MultiArray[Any, DynShape] = MultiArray(
        DynShape((2, 2)), np.array([maximum, maximum, np.inf, -np.inf], dtype=dtype)
    )
    events: list[tuple[str, int]] = []
    later: list[tuple[str, int]] = []

    def replacement(name: str, flags: int) -> None:
        later.append((name, flags))

    def callback(name: str, flags: int) -> None:
        events.append((name, flags))
        if name == "overflow":
            if behavior == "change_policy":
                np.seterr(all="ignore")
                np.seterrcall(replacement)
            else:
                nested: MultiArray[Any, DynShape] = MultiArray(
                    DynShape((2,)), np.array([1, 2])
                )
                assert fast_sum(nested) == 3

    previous = np.geterrcall()
    np.seterrcall(callback)
    try:
        with np.errstate(all="call"):
            fast_sum(source, axis=1)
            assert events == [("overflow", 10), ("invalid value", 10)]
            assert later == []
            if behavior == "change_policy":
                assert np.geterr()["over"] == "ignore"
                assert np.geterrcall() is replacement
    finally:
        np.seterrcall(previous)


@pytest.mark.parametrize("dtype", ["float16", "longdouble", "clongdouble"])
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
def test_half_and_extended_handlers_keep_original_exceptions_and_context(
    *, dtype: str, mode: Any, error_type: type[BaseException]
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    maximum = np.finfo(dtype).max
    source: MultiArray[Any, DynShape] = MultiArray(
        DynShape((2, 2)), np.array([maximum] * 4, dtype=dtype)
    )
    events: list[str] = []
    outer = RuntimeError("外层 / Outer")

    def callback(name: str, flags: int) -> None:
        assert sys.exception() is outer
        assert np.geterr()["over"] == mode and np.geterrcall() is handler
        events.append(name)
        raise error

    class Logger:
        def write(self, message: str) -> None:
            callback(message, 2)

    handler = Logger() if mode == "log" else callback
    previous = np.geterrcall()
    np.seterrcall(handler)
    try:
        with np.errstate(all=mode):
            try:
                raise outer
            except RuntimeError:
                with pytest.raises(error_type) as caught:
                    fast_sum(source, axis=1)
                assert caught.value is error and error.__context__ is outer
                assert sys.exception() is outer and len(events) == 1
        nodes = []
        node = error.__traceback__
        while node is not None:
            nodes.append(node)
            node = node.tb_next
        assert any(node is original for node in nodes)
        assert any(node.tb_frame.f_code is callback.__code__ for node in nodes)
    finally:
        np.seterrcall(previous)
