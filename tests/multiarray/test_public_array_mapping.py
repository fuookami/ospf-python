"""公共 live 映射与 NumPy/iterable 边界合同 / Public live mapping and NumPy/iterable boundary contracts."""

from __future__ import annotations

import gc
import inspect
import weakref
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from typing import Any, get_type_hints

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape, Shape1, Shape2, StorageOrder
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok

_TYPES = (MultiArray, MutableMultiArray)
_METHODS = ("map", "flat_map")


def _objects(values: list[Any]) -> np.ndarray[Any, Any]:
    data = np.empty(len(values), dtype=object)
    for position, value in enumerate(values):
        data[position] = value
    return data


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize("order", list(StorageOrder))
def test_physical_order_fixed_count_and_late_shape(
    *, cls: type[Any], method: str, order: StorageOrder
) -> None:
    source = cls(Shape2(2, 3, order), np.arange(6))
    calls = []
    final_shape = Shape1(1)

    def callback(value: int) -> Any:
        calls.append(value)
        source._shape = final_shape
        return [value * 2] if method == "flat_map" else value * 2

    mapped = getattr(source, method)(callback).unwrap()
    assert calls == list(range(6))
    assert type(mapped) is MultiArray
    assert mapped.shape is final_shape
    assert mapped._data.tolist() == [0, 2, 4, 6, 8, 10]
    assert not np.shares_memory(mapped._data, source._data)
    assert "for " not in inspect.getsource(getattr(cls, method))
    assert get_type_hints(getattr(cls, method))["return"] is not MultiArray


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("method", _METHODS)
def test_single_native_delegation_without_iterator_override(
    *, cls: type[Any], method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    native = _native._map_shared_array
    calls = []

    def record(**kwargs: Any) -> Any:
        calls.append(kwargs)
        return native(**kwargs)

    class Derived(cls):  # type: ignore[misc]
        def __iter__(self) -> Any:
            raise AssertionError("不调用覆盖迭代器 / Must not call overridden iterator")

    monkeypatch.setattr(_native, "_map_shared_array", record)
    source = Derived(Shape1(2), np.array([1, 2]))
    callback = lambda value: [value] if method == "flat_map" else value
    result = getattr(source, method)(callback).unwrap()
    assert result._data.tolist() == [1, 2]
    assert len(calls) == 1
    assert calls[0]["owner"] is source and calls[0]["callback"] is callback
    assert calls[0]["flat"] == (method == "flat_map")


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize("stride", [1, -1, 2, 0])
def test_live_aliases_strides_and_storage_replacement(
    *, cls: type[Any], method: str, stride: int
) -> None:
    backing = np.arange(10)
    data = (
        np.lib.stride_tricks.as_strided(backing, shape=(4,), strides=(0,))
        if stride == 0
        else backing[::stride][:4]
    )
    source = cls(Shape1(4), data)
    first = int(data[0])
    seen = []

    def callback(value: int) -> Any:
        assert type(value) is int
        seen.append(value)
        if len(seen) == 1:
            data[1] = 23
        if len(seen) == 2:
            source._data = np.array([10, 11, 12, 101])
        return [value] if method == "flat_map" else value

    assert getattr(source, method)(callback).unwrap()._data.tolist() == [
        first,
        23,
        12,
        101,
    ]
    assert seen == [first, 23, 12, 101]


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize(
    "values",
    [
        [1 << 300, -(1 << 301)],
        [Fraction(1, 7), Fraction(2, 9)],
        [Decimal("0.123"), Decimal("0.456")],
        [Quantity(Fraction(1, 7), METER), Quantity(Fraction(2, 9), METER)],
        [None, Ok(None), Failed(Err(ErrorCode.APPLICATION_ERROR, "数据 / Data"))],
    ],
)
def test_generic_object_leaves_and_result_as_data(
    *, cls: type[Any], method: str, values: list[Any]
) -> None:
    source = cls(Shape1(len(values)), _objects(values))
    callback = lambda value: [value] if method == "flat_map" else value
    result = getattr(source, method)(callback).unwrap()
    assert result._data.dtype == object
    assert all(result._data[i] is value for i, value in enumerate(values))
    result._data[0] = "independent"
    assert source._data[0] is values[0]


@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize("count", [0, -3, -(1 << 100), 2])
def test_count_index_once_before_first_leaf(method: str, count: int) -> None:
    events = []

    class Count:
        def __index__(self) -> int:
            events.append("index")
            return count

    class Source(MultiArray[Any, Shape1]):
        @property
        def size(self) -> Any:
            events.append("size")
            return Count()

    class Scalar(np.float64):
        def item(self, *args: Any) -> Any:
            events.append("item")
            source._shape = Shape1(1)
            return 7

    source = Source(Shape1(2), _objects([Scalar(1), Scalar(2)]))
    callback = lambda value: [value] if method == "flat_map" else value
    result = getattr(source, method)(callback).unwrap()
    assert events == ["size", "index"] + ["item"] * max(0, count)
    assert result._data.tolist() == [7] * max(0, count)
    if count <= 0:
        assert result._data.dtype == np.float64


@pytest.mark.parametrize("method", _METHODS)
def test_count_overflow_never_reads_source_or_calls_callback(method: str) -> None:
    class Source(MultiArray[Any, Shape1]):
        @property
        def size(self) -> int:
            return 1 << 100

    source = Source(Shape1(1), np.array([1]))
    result = getattr(source, method)(None)
    assert isinstance(result, Failed)
    assert result.error.value.category == "OVERFLOW"
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize("cls", _TYPES)
def test_flat_map_consumes_whole_iterable_before_next_live_read(cls: type[Any]) -> None:
    source = cls(Shape1(2), np.array([1, 2]))
    events = []

    class Output:
        def __init__(self, value: int) -> None:
            self.value = value

        def __iter__(self) -> Any:
            events.append(("iter", self.value))
            return self

        def __length_hint__(self) -> int:
            events.append(("hint", self.value))
            return 0

        def __next__(self) -> int:
            events.append(("next", self.value))
            if self.value < 0:
                raise StopIteration
            value, self.value = self.value, -1
            source._data[1] = 19
            return value

    def callback(value: int) -> Output:
        events.append(("callback", value))
        return Output(value)

    assert source.flat_map(callback).unwrap()._data.tolist() == [1, 19]
    assert events == [
        ("callback", 1),
        ("iter", 1),
        ("hint", 1),
        ("next", 1),
        ("next", -1),
        ("callback", 19),
        ("iter", 19),
        ("hint", 19),
        ("next", 19),
        ("next", -1),
    ]
    assert source.flat_map(lambda _: "ab").unwrap()._data.tolist() == list("abab")
    assert source.flat_map(lambda _: iter(())).unwrap()._data.dtype == np.float64


@pytest.mark.parametrize("method", _METHODS)
def test_numpy_callable_and_shape_resolution_order(
    method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = np.array
    source: MultiArray[int, Shape1] = MultiArray(Shape1(2), original([1, 2]))
    events: list[Any] = []
    final_shape = Shape1(4)

    def changed(values: Any) -> Any:
        events.append("changed-array")
        return original(values)

    def callback(value: int) -> Any:
        events.append(value)
        monkeypatch.setattr(np, "array", changed)
        source._shape = final_shape
        return [value] if method == "flat_map" else value

    result = getattr(source, method)(callback).unwrap()
    assert events == [1, 2] + (["changed-array"] if method == "flat_map" else [])
    assert result.shape is final_shape


@pytest.mark.parametrize("method", _METHODS)
def test_numpy_conversion_can_change_shape_and_preserves_nested_output(
    method: str,
) -> None:
    source: MultiArray[int, Shape1] = MultiArray(Shape1(2), np.array([1, 2]))
    final_shape = Shape1(7)

    class ArrayLike:
        def __array__(self, dtype: Any = None, copy: Any = None) -> Any:
            source._shape = final_shape
            return np.array([3, 4], dtype=dtype)

    callback = lambda _: [ArrayLike()] if method == "flat_map" else ArrayLike()
    result = getattr(source, method)(callback).unwrap()
    assert result.shape is final_shape
    assert result._data.tolist() == [[3, 4], [3, 4]]
    assert result._data.shape == (2, 2)


@pytest.mark.parametrize("method", _METHODS)
def test_resolved_numpy_callable_released_before_constructing_result(
    method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = np.array
    source: MultiArray[int, Shape1] = MultiArray(Shape1(1), original([1]))
    final_shape = Shape1(3)
    events = []

    class Convert:
        def __call__(self, values: Any) -> Any:
            np.array = original
            events.append("array")
            return original(values)

        def __del__(self) -> None:
            events.append("release-callable")
            source._shape = final_shape

    monkeypatch.setattr(np, "array", Convert())
    callback = lambda value: [value] if method == "flat_map" else value
    result = getattr(source, method)(callback).unwrap()
    assert result.shape is final_shape
    assert events == ["array", "release-callable"]


@pytest.mark.parametrize("method", _METHODS)
def test_temporary_list_release_relative_to_constructor(
    method: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = np.array
    events = []

    class Source(MultiArray[Any, Shape1]):
        def __getattribute__(self, name: str) -> Any:
            if name == "_shape":
                events.append("shape")
            return super().__getattribute__(name)

    class Leaf:
        def __del__(self) -> None:
            events.append("delete-leaf")

    source = Source(Shape1(1), original([1]))

    def convert(values: Any) -> Any:
        events.append("array")
        assert len(values) == 1
        return original([9])

    monkeypatch.setattr(np, "array", convert)
    callback = lambda _: [Leaf()] if method == "flat_map" else Leaf()
    assert getattr(source, method)(callback).unwrap()._data.tolist() == [9]
    assert events == (
        ["shape", "array", "delete-leaf", "shape"]
        if method == "map"
        else ["shape", "array", "shape", "delete-leaf"]
    )


@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize(
    "stage", ["size", "read", "item", "callback", "array", "construct", "extend"]
)
def test_original_external_exception_is_not_formatted(
    *, method: str, stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    if stage == "extend" and method == "map":
        return

    class External(ValueError):
        def __str__(self) -> str:
            raise AssertionError("禁止格式化 / Must not format")

    error = External()

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise error

    class Data:
        def __getitem__(self, index: int) -> Any:
            return fail()

    class Scalar(np.float64):
        def item(self, *args: Any) -> Any:
            return fail()

    class Source(MultiArray[Any, Shape1]):
        @property
        def size(self) -> int:
            return fail() if stage == "size" else 2

    class Iterable:
        def __iter__(self) -> Any:
            return fail()

    source = Source(
        Shape1(2),
        _objects([Scalar(1), Scalar(2)]) if stage == "item" else np.array([1, 2]),
    )
    if stage == "read":
        source._data = Data()  # type: ignore[assignment]
    if stage == "array":
        monkeypatch.setattr(np, "array", fail)
    if stage == "construct":
        import ospf_python.multiarray.multi_array as module

        monkeypatch.setattr(module, "MultiArray", fail)

    def callback(value: Any) -> Any:
        if stage == "callback":
            return fail()
        if stage == "extend":
            return Iterable()
        return [value] if method == "flat_map" else value

    result = getattr(source, method)(callback)
    assert isinstance(result, Failed)
    assert result.error.code == ErrorCode.APPLICATION_ERROR
    context = result.error.value
    assert context.error_class == "EXTERNAL_MAPPING"
    assert context.callback_exception is error and error.__traceback__ is not None


@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_baseexception_propagates(method: str, error_type: type[BaseException]) -> None:
    source: MultiArray[int, Shape1] = MultiArray(Shape1(1), np.array([1]))
    error = error_type()

    def callback(value: int) -> Any:
        raise error

    with pytest.raises(error_type) as caught:
        getattr(source, method)(callback)
    assert caught.value is error


@pytest.mark.parametrize("method", _METHODS)
def test_reentrancy_threads_and_no_persistent_source_owner(method: str) -> None:
    sources: list[MultiArray[int, Shape1]] = [MultiArray(Shape1(2), np.array([1, 2]))]
    reference = weakref.ref(sources[0])

    def identity(value: int) -> Any:
        return [value] if method == "flat_map" else value

    def callback(value: int) -> Any:
        with ThreadPoolExecutor(max_workers=1) as executor:
            nested = executor.submit(
                lambda: getattr(sources[0], method)(identity).unwrap()
            )
            assert nested.result(timeout=5)._data.tolist() == [1, 2]
        return identity(value)

    result = getattr(sources[0], method)(callback).unwrap()
    assert result._data.tolist() == [1, 2]
    sources.clear()
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("method", _METHODS)
def test_rank_zero_and_noncallable_empty_or_singleton(method: str) -> None:
    source: MultiArray[int, DynShape] = MultiArray(DynShape(()), np.array([7]))
    assert isinstance(getattr(source, method)(None), Failed)
    callback = lambda value: [value] if method == "flat_map" else value
    assert getattr(source, method)(callback).unwrap()._data.tolist() == [7]


@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize(
    "dtype",
    [
        "int16",
        "uint64",
        "float32",
        "longdouble",
        "clongdouble",
        "datetime64[D]",
        "timedelta64[h]",
        "S3",
        "U3",
    ],
)
def test_numpy_item_and_output_dtype_follow_numpy(method: str, dtype: str) -> None:
    data = np.array([1, 2], dtype=dtype)
    source: MultiArray[Any, Shape1] = MultiArray(Shape1(2), data)
    seen = []

    def callback(value: Any) -> Any:
        seen.append(value)
        return [value] if method == "flat_map" else value

    result = getattr(source, method)(callback).unwrap()
    expected = np.array([data[i].item() for i in range(2)])
    assert result._data.dtype == expected.dtype
    np.testing.assert_array_equal(result._data, expected)
    assert [type(value) for value in seen] == [type(data[i].item()) for i in range(2)]


@pytest.mark.parametrize("method", _METHODS)
def test_output_scalars_not_item_converted_and_no_fake_class_probe(method: str) -> None:
    class Leaf:
        @property
        def __class__(self) -> Any:
            raise AssertionError("不可探测伪装类型 / Must not probe spoofed class")

        @__class__.setter
        def __class__(self, value: Any) -> None:
            raise AssertionError("不可写伪装类型 / Must not write spoofed class")

    # 回调用基本整数隔离 NumPy 自己的对象探测。 / Return basic integers to isolate NumPy's own object probing.
    source: MultiArray[Any, Shape1] = MultiArray(Shape1(1), _objects([Leaf()]))

    def callback(value: Any) -> Any:
        assert type(value) is Leaf
        return [np.int16(7)] if method == "flat_map" else np.int16(7)

    assert getattr(source, method)(callback).unwrap()._data.dtype == np.int16


@pytest.mark.parametrize("method", _METHODS)
def test_temporary_storage_is_released_before_scalar_conversion(method: str) -> None:
    events = []

    class Scalar(np.float64):
        def item(self, *args: Any) -> Any:
            events.append("item")
            return 3

    class Data:
        def __getitem__(self, position: int) -> Scalar:
            events.append("read")
            return Scalar(7)

        def __del__(self) -> None:
            events.append("release-data")

    class Source(MultiArray[Any, Shape1]):
        @property
        def _data(self) -> Any:
            return Data()

        @_data.setter
        def _data(self, value: Any) -> None:
            pass

    source = Source(Shape1(1), np.empty(0))
    callback = lambda value: [value] if method == "flat_map" else value
    assert getattr(source, method)(callback).unwrap()._data.tolist() == [3]
    assert events == ["read", "release-data", "item"]


@pytest.mark.parametrize("stage", ["hint", "next"])
def test_flat_extend_failure_preserves_original_error_and_partial_effects(
    stage: str,
) -> None:
    error = OverflowError("外部 iterable 失败 / External iterable failure")
    seen = []

    class Output:
        def __iter__(self) -> Any:
            return self

        def __length_hint__(self) -> int:
            if stage == "hint":
                raise error
            return 0

        def __next__(self) -> int:
            seen.append("next")
            if len(seen) == 1:
                return 7
            raise error

    source: MultiArray[int, Shape1] = MultiArray(Shape1(2), np.array([1, 2]))
    result = source.flat_map(lambda _: Output())  # type: ignore[arg-type,return-value]
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error
    assert seen == ([] if stage == "hint" else ["next", "next"])
    assert source.flat_map(lambda value: [value]).unwrap()._data.tolist() == [1, 2]
