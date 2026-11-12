"""公共求和的轴及外部分派基线 / Pre-cutover axis and external-dispatch baselines.

当前命名入口尚未升级 Result；这些测试不授权保留 NumPy 默认数学内核。
The named entry is not yet Result-based; these tests do not authorize a NumPy math fallback.
"""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pytest

from ospf_python.math.multiarray.fast_sum import fast_sum
from ospf_python.multiarray import DynShape, MultiArray, Shape2, StorageOrder


class _UnformattableError(ValueError):
    def __str__(self) -> str:
        raise AssertionError("不得格式化异常 / Must not format exceptions")


@pytest.mark.parametrize(
    "axis", [(), (0, 1), (2, 0), (-1, -3), np.int64(1), np.array(1), (0, 1, 2)]
)
def test_tuple_and_numpy_integer_axes_keep_logical_shape_and_promotion(
    axis: Any,
) -> None:
    data = np.arange(24, dtype=np.int16)
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2, 3, 4)), data)
    result = fast_sum(source, axis=axis)
    expected = np.asarray(np.sum(data.reshape((2, 3, 4)), axis=axis))
    assert result.shape.dims == expected.shape
    assert result.shape.storage_order is StorageOrder.ROW_MAJOR
    assert result._data.dtype == expected.dtype
    np.testing.assert_array_equal(result._data, expected.reshape(-1))
    assert not np.shares_memory(result._data, data)


@pytest.mark.parametrize("axis", [0, -1, ()])
def test_scalar_integer_axis_is_distinct_from_empty_axis_tuple(axis: Any) -> None:
    source: MultiArray[Any, DynShape] = MultiArray(
        DynShape(()), np.array([7], dtype=np.int16)
    )
    result = fast_sum(source, axis=axis)
    assert result.shape.dims == ()
    assert result._data.dtype == np.dtype(np.intp)
    np.testing.assert_array_equal(result._data, [7])


@pytest.mark.parametrize(
    ("values", "consumed", "error_type"),
    [
        ((0, 0, 9), [0, 0, 9], np.exceptions.AxisError),
        ((0, -2, 9), [0, -2, 9], np.exceptions.AxisError),
        ((0, 9, 1), [0, 9], np.exceptions.AxisError),
        ((0, 0, 1), [0, 0, 1], ValueError),
    ],
)
def test_tuple_axes_finish_conversion_before_duplicate_detection(
    *, values: tuple[int, ...], consumed: list[int], error_type: type[Exception]
) -> None:
    calls: list[int] = []

    class Axis:
        def __init__(self, value: int) -> None:
            self.value = value

        def __index__(self) -> int:
            calls.append(self.value)
            return self.value

    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6))
    axis: Any = tuple(Axis(value) for value in values)
    with pytest.raises(error_type):
        fast_sum(source, axis=axis)
    assert calls == consumed


@pytest.mark.parametrize("fail_at", [0, 1, 2])
@pytest.mark.parametrize(
    "error_type",
    [
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        StopIteration,
        _UnformattableError,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ],
)
def test_axis_index_first_failure_preserves_original_exception_and_handled_state(
    *, fail_at: int, error_type: type[BaseException]
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    calls: list[int] = []
    outer: BaseException | None = None

    class Axis:
        def __init__(self, position: int) -> None:
            self.position = position

        def __index__(self) -> int:
            assert sys.exception() is outer
            calls.append(self.position)
            if self.position == fail_at:
                raise error
            return 0

    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6))
    axis: Any = tuple(Axis(position) for position in range(3))
    try:
        raise RuntimeError("先前处理中的异常 / Previously handled exception")
    except RuntimeError as handled:
        outer = handled
        with pytest.raises(error_type) as caught:
            fast_sum(source, axis=axis)
        assert caught.value is error and error.__context__ is outer
        assert sys.exception() is outer
    assert calls == list(range(fail_at + 1))
    chain = []
    traceback = error.__traceback__
    while traceback is not None:
        chain.append(traceback)
        traceback = traceback.tb_next
    assert any(node is original for node in chain)
    assert any(node.tb_frame.f_code is Axis.__index__.__code__ for node in chain)


@pytest.mark.parametrize("mode", ["all", "axis", "oversized"])
def test_array_function_override_receives_original_axis_before_any_parsing(
    mode: str,
) -> None:
    events: list[Any] = []
    flat = np.array([13, 17])

    class Axis:
        def __index__(self) -> int:
            pytest.fail(
                "外部分派前不能解析轴 / Must not parse axes before external dispatch"
            )

    axis: Any = Axis() if mode == "axis" else tuple(Axis() for _ in range(65))

    class Payload:
        @property
        def shape(self) -> tuple[int, ...]:
            events.append("result_shape")
            return (2,)

        def flatten(self) -> np.ndarray[Any, Any]:
            events.append("flatten")
            return flat

        def __float__(self) -> float:
            events.append("float")
            return 29.0

    class Hook(np.ndarray[Any, Any]):
        def reshape(self, *args: Any, **kwargs: Any) -> Any:
            events.append("reshape")
            assert args == ((2, 3),) and kwargs == {}
            return super().reshape(*args, **kwargs)

        def __array_function__(
            self, function: Any, types: Any, args: Any, kwargs: Any
        ) -> Any:
            events.append("array_function")
            assert function is np.sum and args == (self,)
            assert types == (Hook,)
            assert kwargs == {} if mode == "all" else kwargs == {"axis": axis}
            return Payload()

    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6).view(Hook))
    result = fast_sum(source) if mode == "all" else fast_sum(source, axis=axis)
    if mode == "all":
        assert result == 29.0 and events == ["reshape", "array_function", "float"]
    else:
        assert result._data is flat
        assert events == ["reshape", "array_function", "result_shape", "flatten"]


@pytest.mark.parametrize("kind", ["method", "ufunc"])
def test_reduction_method_and_ufunc_overrides_own_the_axis_protocol(kind: str) -> None:
    events: list[str] = []

    class Axis:
        def __index__(self) -> int:
            pytest.fail(
                "自定义归约可自行解释轴 / Custom reductions own axis interpretation"
            )

    axis: Any = Axis()
    marker = np.array([5, 7, 9])

    class Method(np.ndarray[Any, Any]):
        def sum(self, *args: Any, **kwargs: Any) -> Any:
            events.append("method")
            assert args == () and kwargs["axis"] is axis
            assert kwargs.get("dtype") is None and kwargs.get("out") is None
            return marker

    class Ufunc(np.ndarray[Any, Any]):
        def __array_ufunc__(
            self, ufunc: Any, method: Any, *inputs: Any, **kwargs: Any
        ) -> Any:
            events.append("ufunc")
            assert ufunc is np.add and method == "reduce"
            assert len(inputs) == 1 and inputs[0] is self
            assert kwargs["axis"] is axis
            return marker

    hook = Method if kind == "method" else Ufunc
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6).view(hook))
    result = fast_sum(source, axis=axis)
    assert events == [kind]
    np.testing.assert_array_equal(result._data, marker)


@pytest.mark.parametrize("kind", ["function", "method", "ufunc"])
@pytest.mark.parametrize(
    "error_type",
    [
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        StopIteration,
        _UnformattableError,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ],
)
def test_external_dispatch_failure_precedes_axis_parsing_and_keeps_exception_state(
    *, kind: str, error_type: type[BaseException]
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    calls: list[str] = []
    outer: BaseException | None = None

    class Axis:
        def __index__(self) -> int:
            pytest.fail(
                "失败分派后不能解析轴 / Must not parse axes after failed dispatch"
            )

    def fail() -> Any:
        assert sys.exception() is outer
        calls.append(kind)
        raise error

    class Function(np.ndarray[Any, Any]):
        def __array_function__(self, *args: Any, **kwargs: Any) -> Any:
            return fail()

    class Method(np.ndarray[Any, Any]):
        def sum(self, *args: Any, **kwargs: Any) -> Any:
            return fail()

    class Ufunc(np.ndarray[Any, Any]):
        def __array_ufunc__(self, *args: Any, **kwargs: Any) -> Any:
            return fail()

    hook = {"function": Function, "method": Method, "ufunc": Ufunc}[kind]
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6).view(hook))
    axis: Any = Axis()
    try:
        raise RuntimeError("先前处理中的异常 / Previously handled exception")
    except RuntimeError as handled:
        outer = handled
        with pytest.raises(error_type) as caught:
            fast_sum(source, axis=axis)
        assert caught.value is error and error.__context__ is outer
        assert sys.exception() is outer
    assert calls == [kind]
    chain = []
    traceback = error.__traceback__
    while traceback is not None:
        chain.append(traceback)
        traceback = traceback.tb_next
    assert any(node is original for node in chain)
    assert any(node.tb_frame.f_code is fail.__code__ for node in chain)


def test_reshape_lookup_precedes_shape_and_output_factories_are_resolved_late(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    module = importlib.import_module("ospf_python.math.multiarray.fast_sum")
    events: list[str] = []
    flat = np.array([1, 2])
    axis: Any = object()
    original_shape = module.DynShape
    original_array = module.MultiArray

    class Output:
        @property
        def shape(self) -> tuple[int, ...]:
            events.append("result_shape")
            return (2,)

        def flatten(self) -> Any:
            events.append("flatten")
            return flat

    class Reshaped:
        @property
        def sum(self) -> Any:
            events.append("lookup_sum")

            def reduce(**kwargs: Any) -> Any:
                events.append("sum")
                assert kwargs["axis"] is axis
                return Output()

            return reduce

    class Data:
        @property
        def reshape(self) -> Any:
            events.append("lookup_reshape")

            def reshape(dims: Any) -> Any:
                events.append("reshape")
                assert dims == (2, 3)
                return Reshaped()

            return reshape

    class Shape:
        @property
        def dims(self) -> tuple[int, ...]:
            events.append("dims")
            return (2, 3)

    class Owner:
        @property
        def _data(self) -> Any:
            events.append("data")
            return Data()

        @property
        def shape(self) -> Any:
            events.append("shape")
            return Shape()

    def shape_factory(*, dims: Any) -> Any:
        events.append("shape_factory")
        return original_shape(dims=dims)

    def array_factory(shape: Any, data: Any) -> Any:
        events.append("array_factory")
        return original_array(shape, data)

    monkeypatch.setattr(module, "DynShape", shape_factory)
    monkeypatch.setattr(module, "MultiArray", array_factory)
    owner: Any = Owner()
    result = fast_sum(owner, axis=axis)
    assert result._data is flat
    assert events == [
        "data",
        "lookup_reshape",
        "shape",
        "dims",
        "reshape",
        "lookup_sum",
        "sum",
        "result_shape",
        "shape_factory",
        "flatten",
        "array_factory",
    ]


@pytest.mark.parametrize("count", [64, 65, 128])
def test_numpy_two_axis_capacity_is_checked_before_consuming_excess_values(
    count: int,
) -> None:
    calls: list[int] = []

    class Axis:
        def __index__(self) -> int:
            calls.append(0)
            return 0

    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6))
    axis: Any = tuple(Axis() for _ in range(count))
    with pytest.raises(ValueError):
        fast_sum(source, axis=axis)
    assert len(calls) == (64 if count == 64 else 0)


def test_tuple_subclass_axis_uses_tuple_contents_without_sequence_overrides() -> None:
    class Tuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            pytest.fail(
                "不调用 tuple 迭代覆盖 / Must not invoke tuple iteration override"
            )

        def __len__(self) -> int:
            pytest.fail("不调用 tuple 长度覆盖 / Must not invoke tuple length override")

        def __getitem__(self, key: Any) -> Any:
            pytest.fail(
                "不调用 tuple 下标覆盖 / Must not invoke tuple subscription override"
            )

    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6))
    axis: Any = Tuple((0, -1))
    result = fast_sum(source, axis=axis)
    assert result.shape.dims == ()
    np.testing.assert_array_equal(result._data, [15])
