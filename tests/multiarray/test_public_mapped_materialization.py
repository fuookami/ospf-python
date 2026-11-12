"""公共 mapped view 完整物化合同 / Full materialization contracts for public mapped views."""

from __future__ import annotations

import gc
import itertools
import weakref
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from typing import Any, cast

import numpy as np
import pytest

from ospf_python.multiarray import (
    DynShape,
    MultiArray,
    MultiArrayView,
    MutableMultiArray,
    Shape1,
    Shape2,
    StorageOrder,
)
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok


def _objects(values: list[Any]) -> np.ndarray[Any, Any]:
    data = np.empty(len(values), dtype=object)
    for index, value in enumerate(values):
        data[index] = value
    return data


@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("dims", [(), (4,), (2, 3), (2, 1, 3)])
def test_complete_coordinate_correspondence_and_shape_identity(
    *, cls: type[Any], order: StorageOrder, dims: tuple[int, ...]
) -> None:
    shape = DynShape(dims, order)
    data = np.arange(shape.size, dtype=np.float32)
    source = cls(shape, data)
    calls = []

    def callback(value: float) -> float:
        calls.append(value)
        return value * 2

    mapped = MultiArrayView(source).map(callback)
    result = mapped.materialize().unwrap()
    logical = data.reshape(dims, order="C" if order is StorageOrder.ROW_MAJOR else "F")
    assert calls == logical.ravel(order="C").tolist()
    assert result.shape is shape and type(result) is MultiArray
    assert result._data.dtype == np.float64
    for coords in itertools.product(*(range(dim) for dim in dims)):
        assert result.get(*coords) == logical[coords] * 2
    assert not np.shares_memory(result._data, data)
    result._data[0] = 99
    assert data[0] == 0


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("stride", [1, -1, 2, 0])
def test_live_alias_and_whole_storage_replacement(
    order: StorageOrder, stride: int
) -> None:
    backing = np.arange(12)
    data = (
        np.lib.stride_tricks.as_strided(backing, shape=(6,), strides=(0,))
        if stride == 0
        else backing[::stride][:6]
    )
    source: MultiArray[int, Shape2] = MultiArray(Shape2(2, 3, order), data)
    shape = source.shape
    calls = []

    def callback(value: int) -> int:
        calls.append(value)
        if len(calls) == 1:
            data[...] = 7
        if len(calls) == 2:
            source._data = np.arange(10, 16)
        return value

    first = int(data[0])
    expected = (
        [first, 7, 12, 13, 14, 15]
        if order is StorageOrder.ROW_MAJOR
        else [first, 7, 14, 11, 13, 15]
    )
    result = MultiArrayView(source).map(callback).materialize().unwrap()
    assert calls == expected
    assert [
        result.get(*coords) for coords in itertools.product(range(2), range(3))
    ] == expected
    assert result.shape is shape


@pytest.mark.parametrize("order", list(StorageOrder))
def test_captured_shape_and_dynamic_get_override(order: StorageOrder) -> None:
    source: MultiArray[int, Shape2] = MultiArray(Shape2(2, 3, order), np.arange(6))
    shape = source.shape

    def callback(value: int) -> int:
        source._shape = Shape2(3, 2)
        cast("Any", mapped).get = lambda *indices: 100 + indices[0] * 3 + indices[1]
        return value

    mapped = MultiArrayView(source).map(callback)
    result = mapped.materialize().unwrap()
    assert result.shape is shape
    assert [
        result.get(*coords) for coords in itertools.product(range(2), range(3))
    ] == [0, 101, 102, 103, 104, 105]


@pytest.mark.parametrize("order", list(StorageOrder))
def test_opaque_results_exact_quantities_and_nested_output(order: StorageOrder) -> None:
    leaves: list[Any] = [
        None,
        Ok(None),
        Failed(Err(ErrorCode.APPLICATION_ERROR, "数据 / Data")),
        Fraction(1, 7),
        Quantity(Fraction(2, 9), METER),
        1 << 300,
    ]
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3, order), _objects(leaves))
    result = MultiArrayView(source).map(lambda value: value).materialize().unwrap()
    assert all(result._data[index] is leaf for index, leaf in enumerate(leaves))
    arrays = (
        MultiArrayView(source).map(lambda _: np.array([3, 4])).materialize().unwrap()
    )
    assert arrays._data.shape == (6, 2)
    np.testing.assert_array_equal(arrays.get(1, 2), [3, 4])


@pytest.mark.parametrize(
    "dtype",
    [
        ">i2",
        "uint64",
        "longdouble",
        "clongdouble",
        "datetime64[D]",
        "timedelta64[h]",
        "S3",
        "U3",
    ],
)
def test_input_item_and_numpy_output_dtype_domains(dtype: str) -> None:
    data = np.array([1, 2, 3, 4, 5, 6], dtype=dtype)
    source: MultiArray[Any, Shape2] = MultiArray(
        Shape2(2, 3, StorageOrder.COLUMN_MAJOR), data
    )
    actual = MultiArrayView(source).map(lambda value: value).materialize().unwrap()
    expected = np.array([data[index].item() for index in range(6)])
    assert actual._data.dtype == expected.dtype
    np.testing.assert_array_equal(actual._data, expected)


def test_callback_stopiteration_is_failure_not_normal_exhaustion() -> None:
    source: MultiArray[int, Shape1] = MultiArray(Shape1(2), np.array([1, 2]))
    error = StopIteration("外部回调 / External callback")

    def callback(value: int) -> int:
        raise error

    result = MultiArrayView(source).map(callback).materialize()
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error


def test_numpy_array_protocols_run_in_c_order_before_layout_gather(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[Any] = []
    source: MultiArray[int, Shape2] = MultiArray(
        Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6)
    )
    take = np.take

    class Output:
        def __init__(self, value: int) -> None:
            self.value = value

        def __array__(self, dtype: Any = None, copy: Any = None) -> Any:
            events.append(("array", self.value))
            return np.array([self.value], dtype=dtype)

    def callback(value: Any) -> Any:
        events.append(("callback", value))
        return Output(value)

    def gather(*args: Any, **kwargs: Any) -> Any:
        events.append(("take",))
        return take(*args, **kwargs)

    monkeypatch.setattr(np, "take", gather)
    result = MultiArrayView(source).map(callback).materialize().unwrap()
    expected = [0, 2, 4, 1, 3, 5]
    assert events == [("callback", value) for value in expected] + [
        ("array", value) for value in expected
    ] + [("take",)]
    assert result._data.tolist() == [[index] for index in range(6)]


@pytest.mark.parametrize("negative", [False, True])
def test_custom_dense_layout_and_negative_indices_are_supported(negative: bool) -> None:
    class Custom:
        dims = (2, 3)
        ndim = 2
        size = 6
        storage_order = StorageOrder.ROW_MAJOR

        def flat_index(self, *indices: int) -> int:
            ordinal = indices[0] * 3 + indices[1]
            return -1 - ordinal if negative else 5 - ordinal

    source: Any = MultiArray(Custom(), np.arange(6))
    result = MultiArrayView(source).map(lambda value: value * 2).materialize().unwrap()
    assert result.shape is source.shape
    assert result._data.tolist() == [0, 2, 4, 6, 8, 10]
    for i, j in itertools.product(range(2), range(3)):
        assert result.get(i, j) == source.get(i, j) * 2


@pytest.mark.parametrize("kind", ["duplicate", "out-of-range", "external"])
def test_custom_layout_failure_after_all_sampling_and_numpy(kind: str) -> None:
    error = ValueError("自定义布局 / Custom layout")
    index_calls = 0
    callbacks = []

    class Custom:
        dims = (3,)
        ndim = 1
        size = 3
        storage_order = StorageOrder.ROW_MAJOR

        def flat_index(self, *indices: int) -> int:
            nonlocal index_calls
            index_calls += 1
            if index_calls <= 3:
                return indices[0]
            if kind == "external":
                raise error
            return 0 if kind == "duplicate" else 99

    source: Any = MultiArray(Custom(), np.arange(3))

    def callback(value: int) -> int:
        callbacks.append(value)
        return value

    result = MultiArrayView(source).map(callback).materialize()
    assert isinstance(result, Failed) and callbacks == [0, 1, 2]
    if kind == "external":
        assert result.error.value.callback_exception is error
    else:
        assert result.error.code == ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize("stage", ["get", "array", "take", "construct"])
def test_external_exception_identity_and_traceback_without_formatting(
    stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    class External(ValueError):
        def __str__(self) -> str:
            raise AssertionError("禁止格式化 / Must not format")

    error = External()
    source: MultiArray[int, Shape2] = MultiArray(
        Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6)
    )
    mapped = MultiArrayView(source).map(lambda value: value)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise error

    if stage == "get":
        cast("Any", mapped).get = fail
    elif stage in {"array", "take"}:
        monkeypatch.setattr(np, stage, fail)
    else:
        import ospf_python.multiarray.multi_array_view as module

        monkeypatch.setattr(module, "MultiArray", fail)
    result = mapped.materialize()
    assert isinstance(result, Failed)
    assert result.error.value.error_class == "EXTERNAL_MATERIALIZATION"
    assert result.error.value.callback_exception is error
    assert error.__traceback__ is not None


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_baseexception_propagates(error_type: type[BaseException]) -> None:
    source: MultiArray[int, Shape1] = MultiArray(Shape1(1), np.array([1]))
    error = error_type()

    def callback(value: int) -> int:
        raise error

    with pytest.raises(error_type) as caught:
        MultiArrayView(source).map(callback).materialize()
    assert caught.value is error


@pytest.mark.parametrize("dims", [(0, 3), (-1, 2), (1 << 100, 0)])
def test_nonpositive_dimensions_remain_empty(dims: tuple[int, ...]) -> None:
    class Custom:
        storage_order = StorageOrder.COLUMN_MAJOR
        ndim = 2

        def flat_index(self, *indices: int) -> int:
            raise AssertionError(
                "空输出不调用布局函数 / Empty output must not call layout function"
            )

    shape: Any = Custom()
    shape.dims = dims
    source: Any = MultiArray(shape, np.empty(0))
    mapped = MultiArrayView(source).map(
        lambda _: pytest.fail("不得调用 / Must not call")
    )
    result = mapped.materialize().unwrap()
    assert result.shape is shape and result._data.size == 0
    assert result._data.dtype == np.float64


def test_capacity_overflow_is_structured_before_get() -> None:
    class Custom:
        dims = (1 << 100, 2)
        ndim = 2

    source: Any = MultiArray(Custom(), np.empty(0))
    result = (
        MultiArrayView(source)
        .map(lambda _: pytest.fail("不得读取 / Must not read"))
        .materialize()
    )
    assert isinstance(result, Failed)
    assert result.error.value.category == "OVERFLOW"


def test_reentrancy_threads_and_no_persistent_source_owner() -> None:
    sources: list[MultiArray[int, Shape1]] = [MultiArray(Shape1(2), np.array([1, 2]))]
    reference = weakref.ref(sources[0])

    def callback(value: int) -> int:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                lambda: (
                    MultiArrayView(sources[0])
                    .map(lambda leaf: leaf)
                    .materialize()
                    .unwrap()
                )
            )
            assert future.result(timeout=5)._data.tolist() == [1, 2]
        return value

    mapped = MultiArrayView(sources[0]).map(callback)
    result = mapped.materialize().unwrap()
    assert result._data.tolist() == [1, 2]
    del mapped
    sources.clear()
    gc.collect()
    assert reference() is None
