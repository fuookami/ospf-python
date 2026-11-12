"""轴回调合法改变 rank 的自然合同。 / Natural contracts for valid axis-driven rank changes.

只比较 NumPy 安全确定的轴；失效最终轴的 FS-006 不能用未初始化 flags 当 oracle。
Only safe NumPy axes are compared; FS-006 cannot use uninitialized flags as an oracle.
"""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pytest

from ospf_python import multiarray
from ospf_python.math.multiarray.fast_sum import fast_sum

_VALID = (
    ((6,), (2, 3), 0),
    ((6,), (2, 3), -1),
    ((6,), (2, 3), (-1,)),
    ((2, 3), (1, 2, 3), 0),
    ((2, 3), (1, 2, 3), -1),
    ((2, 3), (1, 2, 3), (0, 1)),
    ((1, 2, 3), (2, 3), 0),
    ((1, 2, 3), (2, 3), -3),
    ((), (1,), 0),
    ((), (1, 1, 1), -1),
)


@pytest.mark.parametrize("initial,final,raw", _VALID)
@pytest.mark.parametrize("dtype", ["int16", "float16", "complex128", object])
def test_valid_rank_change_keeps_initial_axis_and_uses_final_extents(
    *, initial: tuple[int, ...], final: tuple[int, ...], raw: Any, dtype: Any
) -> None:
    captures: list[Any] = []
    calls: list[int] = []

    class Hook(np.ndarray[Any, Any]):
        def reshape(self, *args: Any, **kwargs: Any) -> Any:
            value = super().reshape(*args, **kwargs)
            captures.append(value)
            return value

    data = np.arange(int(np.prod(initial))).astype(dtype)
    owner: multiarray.MultiArray[Any, multiarray.DynShape] = multiarray.MultiArray(
        multiarray.DynShape(initial), data.view(Hook)
    )

    class Axis:
        def __init__(self, value: int) -> None:
            self.value = value

        def __index__(self) -> int:
            calls.append(self.value)
            captures[0].shape = final
            return self.value

    inputs = raw if isinstance(raw, tuple) else (raw,)
    axis: Any = tuple(Axis(i) for i in raw) if isinstance(raw, tuple) else Axis(raw)
    normalized = tuple(i % len(initial) for i in inputs) if initial else ()
    expected = np.asarray(np.sum(data.reshape(final), axis=normalized))
    result = fast_sum(owner, axis=axis)
    assert isinstance(result, multiarray.MultiArray)
    actual = np.asarray(result._data).reshape(result.shape.dims)
    np.testing.assert_array_equal(actual, expected)
    assert actual.shape == expected.shape and actual.dtype == expected.dtype
    assert calls == list(inputs) and len(captures) == 1
    assert not np.shares_memory(result._data, data)


@pytest.mark.parametrize("raw", [1, -2])
def test_initial_bounds_are_not_reinterpreted_after_rank_growth(raw: int) -> None:
    captures: list[Any] = []
    calls: list[int] = []

    class Hook(np.ndarray[Any, Any]):
        def reshape(self, *args: Any, **kwargs: Any) -> Any:
            value = super().reshape(*args, **kwargs)
            captures.append(value)
            return value

    owner: multiarray.MultiArray[Any, multiarray.DynShape] = multiarray.MultiArray(
        multiarray.DynShape((6,)), np.arange(6).view(Hook)
    )

    class Axis:
        def __index__(self) -> int:
            calls.append(raw)
            captures[0].shape = (2, 3)
            return raw

    axis: Any = Axis()
    with pytest.raises(np.exceptions.AxisError):
        fast_sum(owner, axis=axis)
    assert calls == [raw]


@pytest.mark.parametrize(
    "error_type",
    [
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        StopIteration,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ],
)
def test_late_axis_failure_survives_rank_change_and_stops_later_protocols(
    error_type: type[BaseException],
) -> None:
    captures: list[Any] = []
    events: list[str] = []
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    outer = RuntimeError("外层处理中异常 / Outer handled exception")

    class Hook(np.ndarray[Any, Any]):
        def reshape(self, *args: Any, **kwargs: Any) -> Any:
            value = super().reshape(*args, **kwargs)
            captures.append(value)
            return value

    owner: multiarray.MultiArray[Any, multiarray.DynShape] = multiarray.MultiArray(
        multiarray.DynShape((1, 1, 1)), np.ones(1).view(Hook)
    )

    class First:
        def __index__(self) -> int:
            assert sys.exception() is outer
            events.append("first")
            captures[0].shape = ()
            return 2

    class Second:
        def __index__(self) -> int:
            assert sys.exception() is outer
            events.append("second")
            raise error

    class Third:
        def __index__(self) -> int:
            pytest.fail("首错后停止 / Stop after the first error")

    axis: Any = (First(), Second(), Third())
    try:
        raise outer
    except RuntimeError:
        with pytest.raises(error_type) as caught:
            fast_sum(owner, axis=axis)
        assert caught.value is error and error.__context__ is outer
        assert sys.exception() is outer
    nodes = []
    node = error.__traceback__
    while node is not None:
        nodes.append(node)
        node = node.tb_next
    assert any(node is original for node in nodes)
    assert events == ["first", "second"]
