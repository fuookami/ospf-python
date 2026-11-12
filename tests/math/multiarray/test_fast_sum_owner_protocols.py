"""自然求和入口的捕获与发布合同。 / Natural summation capture and publication contracts.

当前默认尚未切换 Result；本文件保护有效协议，不批准旧浮点包装或列布局缺陷。
The default is not Result-based; these protect protocols, not float narrowing or layout defects.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

import numpy as np
import pytest

from ospf_python.math.multiarray.fast_sum import fast_sum
from ospf_python.multiarray import MultiArray, Shape2


class _Poison(ValueError):
    def __str__(self) -> str:
        raise AssertionError("不得格式化原异常 / Never format the original exception")


_ERRORS = (
    ValueError,
    TypeError,
    AttributeError,
    RuntimeError,
    StopIteration,
    _Poison,
    KeyboardInterrupt,
    SystemExit,
    GeneratorExit,
)


@pytest.mark.parametrize(
    "stage", ["data", "lookup_reshape", "shape", "dims", "reshape"]
)
@pytest.mark.parametrize("error_type", _ERRORS)
def test_capture_failure_preserves_original_error_and_stops_later_protocols(
    *, stage: str, error_type: type[BaseException]
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    outer = RuntimeError("外层处理中异常 / Outer handled exception")
    events: list[str] = []

    def event(name: str) -> None:
        assert sys.exception() is outer
        events.append(name)
        if name == stage:
            raise error

    class Data:
        @property
        def reshape(self) -> Any:
            event("lookup_reshape")

            def reshape(dims: Any) -> Any:
                event("reshape")
                pytest.fail("首错后不得继续 / Must stop at the first failure")

            return reshape

    class Shape:
        @property
        def dims(self) -> tuple[int, ...]:
            event("dims")
            return (2, 3)

    class Owner:
        @property
        def _data(self) -> Any:
            event("data")
            return Data()

        @property
        def shape(self) -> Any:
            event("shape")
            return Shape()

    owner: Any = Owner()
    try:
        raise outer
    except RuntimeError:
        with pytest.raises(error_type) as caught:
            fast_sum(owner)
        assert caught.value is error and error.__context__ is outer
        assert sys.exception() is outer
    expected = ["data", "lookup_reshape", "shape", "dims", "reshape"]
    assert events == expected[: expected.index(stage) + 1]
    nodes = []
    node = error.__traceback__
    while node is not None:
        nodes.append(node)
        node = node.tb_next
    assert any(node is original for node in nodes)
    assert any(node.tb_frame.f_code is event.__code__ for node in nodes)


@pytest.mark.parametrize("mutation", ["none", "data", "callable", "shape"])
def test_rebinding_does_not_redirect_captured_reshape_or_shape(mutation: str) -> None:
    events: list[str] = []
    dims = object()
    axis: Any = object()
    flat = np.array([13, 17])

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("不能重新查找已捕获对象 / Do not re-resolve captured objects")

    class Output:
        shape = (2,)

        def flatten(self) -> Any:
            events.append("flatten")
            return flat

    class Reshaped:
        def sum(self, **kwargs: Any) -> Any:
            events.append("sum")
            assert kwargs == {"axis": axis, "out": None}
            return Output()

    def captured_reshape(value: Any) -> Any:
        assert value is dims
        events.append("reshape")
        return Reshaped()

    class Data:
        current: Any = staticmethod(captured_reshape)

        @property
        def reshape(self) -> Any:
            events.append("lookup_reshape")
            return self.current

    data = Data()

    class Shape:
        @property
        def dims(self) -> Any:
            events.append("dims")
            if mutation == "shape":
                owner.current = object()
            return dims

    class Owner:
        def __init__(self) -> None:
            self.current: Any = Shape()
            self.data: Any = data

        @property
        def _data(self) -> Any:
            events.append("data")
            return self.data

        @property
        def shape(self) -> Any:
            events.append("shape")
            if mutation == "data":
                self.data = object()
            elif mutation == "callable":
                data.current = forbidden
            return self.current

    owner: Any = Owner()
    result = fast_sum(owner, axis=axis)
    assert result._data is flat
    assert events == [
        "data",
        "lookup_reshape",
        "shape",
        "dims",
        "reshape",
        "sum",
        "flatten",
    ]


@pytest.mark.parametrize("raw", [0, -1, 1, (0,), (-1,), (0, 1), (-1, 0)])
@pytest.mark.parametrize("dtype", ["int16", "object"])
def test_same_rank_captured_header_extents_are_observed_after_one_axis_conversion(
    *, raw: Any, dtype: str
) -> None:
    captures: list[Any] = []

    class Hook(np.ndarray[Any, Any]):
        def reshape(self, *args: Any, **kwargs: Any) -> Any:
            result = super().reshape(*args, **kwargs)
            captures.append(result)
            return result

    data = np.arange(6).astype(dtype)
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), data.view(Hook))
    calls: list[int] = []

    class Axis:
        def __init__(self, value: int) -> None:
            self.value = value

        def __index__(self) -> int:
            calls.append(self.value)
            captures[0].shape = (3, 2)
            return self.value

    axis: Any = (
        tuple(Axis(value) for value in raw) if isinstance(raw, tuple) else Axis(raw)
    )
    result = fast_sum(source, axis=axis)
    expected = np.asarray(np.sum(data.reshape(3, 2), axis=raw))
    assert result.shape.dims == expected.shape
    assert result._data.dtype == (
        np.dtype(object) if dtype == "object" else expected.dtype
    )
    np.testing.assert_array_equal(result._data, expected.reshape(-1))
    assert calls == (list(raw) if isinstance(raw, tuple) else [raw])
    assert len(captures) == 1 and captures[0].shape == (3, 2)


@pytest.mark.parametrize("stage", ["shape", "flatten", "array"])
@pytest.mark.parametrize("error_type", _ERRORS)
def test_output_protocol_failure_preserves_exception_and_never_publishes_partial_array(
    *, stage: str, error_type: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module("ospf_python.math.multiarray.fast_sum")
    original_shape = module.DynShape
    original_array = module.MultiArray
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    outer = RuntimeError("外层处理中异常 / Outer handled exception")
    events: list[str] = []

    def event(name: str) -> None:
        assert sys.exception() is outer
        events.append(name)
        if name == stage:
            raise error

    class Output:
        @property
        def shape(self) -> tuple[int, ...]:
            event("shape")
            return (2,)

        def flatten(self) -> Any:
            event("flatten")
            return np.array([13, 17])

    class Hook(np.ndarray[Any, Any]):
        def __array_function__(self, *args: Any, **kwargs: Any) -> Any:
            return Output()

    def shape_factory(*, dims: Any) -> Any:
        event("shape_factory")
        return original_shape(dims=dims)

    def array_factory(shape: Any, values: Any) -> Any:
        event("array")
        return original_array(shape, values)

    monkeypatch.setattr(module, "DynShape", shape_factory)
    monkeypatch.setattr(module, "MultiArray", array_factory)
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6).view(Hook))
    axis: Any = object()
    try:
        raise outer
    except RuntimeError:
        with pytest.raises(error_type) as caught:
            fast_sum(source, axis=axis)
        assert caught.value is error and error.__context__ is outer
        assert sys.exception() is outer
    expected = ["shape", "shape_factory", "flatten", "array"]
    assert events == expected[: expected.index(stage) + 1]
    nodes = []
    node = error.__traceback__
    while node is not None:
        nodes.append(node)
        node = node.tb_next
    assert any(node is original for node in nodes)
    assert any(node.tb_frame.f_code is event.__code__ for node in nodes)


def test_unknown_shape_mapping_is_not_inferred_from_storage_order() -> None:
    class Shape:
        dims = (2, 3)

        @property
        def storage_order(self) -> Any:
            pytest.fail("不能猜测自定义映射 / Do not infer a custom mapping")

    class Owner:
        _data = np.arange(6)
        shape = Shape()

    owner: Any = Owner()
    result = fast_sum(owner, axis=0)
    np.testing.assert_array_equal(result._data, [3, 5, 7])
