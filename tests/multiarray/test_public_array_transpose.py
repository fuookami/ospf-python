"""公共原生转置的外部协议与失败合同 / External protocols and failure contracts for public native transpose."""

from __future__ import annotations

import gc
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast

import numpy as np
import pytest

from ospf_python.multiarray import (
    DynShape,
    MultiArray,
    MutableMultiArray,
    Shape1,
    StorageOrder,
)
from ospf_python.utils.functional.result import Failed


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
def test_dynamic_shape_lookup_and_c_order_calls(storage: type[Any]) -> None:
    events: list[Any] = []

    class Custom:
        dims = (2, 3)
        size = 6
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> tuple[int, int]:
            return (3, 1)

        def flat_index(self, *indices: int) -> int:
            events.append(indices)
            return indices[0] * 3 + indices[1]

    source = storage(Custom(), np.arange(6))
    result = source.transpose().unwrap()
    assert events == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
    assert result._data.tolist() == list(range(6))
    assert result.shape == DynShape((3, 2), StorageOrder.COLUMN_MAJOR)


@pytest.mark.parametrize("stride_count", [0, 1, 2, 3])
def test_external_stride_products_and_sums_are_ordered_and_truncated(
    stride_count: int,
) -> None:
    events: list[Any] = []

    class Product:
        def __init__(self, value: int) -> None:
            self.value = value

        def __radd__(self, other: int) -> int:
            events.append(("add", other, self.value))
            return other + self.value

    class Stride:
        def __init__(self, value: int) -> None:
            self.value = value

        def __mul__(self, other: int) -> Product:
            events.append(("mul", self.value, other))
            return Product(self.value * other)

    class Custom:
        dims = (1, 1)
        size = 1
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> Any:
            return tuple(Stride(value) for value in range(stride_count))

        def flat_index(self, *indices: int) -> int:
            return 0

    source: Any = MultiArray(Custom(), np.array([7]))
    actual = source.transpose().unwrap()
    assert actual._data.tolist() == [7]
    expected: list[Any] = []
    for value in reversed(range(stride_count)):
        if len(expected) == 4:
            break
        expected.extend([("mul", value, 0), ("add", 0, 0)])
    assert events == expected


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize(
    "stage", ["copy", "strides", "index", "read", "allocate", "construct"]
)
def test_original_exceptions_never_formatted(
    *, storage: type[Any], stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    class External(TypeError):
        def __str__(self) -> str:
            raise AssertionError("不得格式化 / Must not format")

    error = External()

    class Custom:
        dims = (2,)
        size = 2
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> tuple[int]:
            if stage == "strides":
                raise error
            return (1,)

        def flat_index(self, *indices: int) -> int:
            if stage == "index":
                raise error
            return indices[0]

    class Data:
        dtype = np.dtype("int64")

        def copy(self) -> Data:
            if stage == "copy":
                raise error
            return self

        def __getitem__(self, key: Any) -> int:
            if stage == "read":
                raise error
            return cast("int", key)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise error

    source: Any = storage(Custom(), Data())
    if stage == "copy" and storage is MultiArray:
        assert source.transpose().unwrap()._data.tolist() == [0, 1]
        return
    if stage == "allocate":
        monkeypatch.setattr(np, "empty", fail)
    if stage == "construct":
        import ospf_python.multiarray.multi_array as module

        monkeypatch.setattr(module, "MultiArray", fail)
    result = source.transpose()
    assert isinstance(result, Failed)
    assert result.error.value.error_class == "EXTERNAL_TRANSPOSE"
    assert result.error.value.callback_exception is error
    assert error.__traceback__ is not None


@pytest.mark.parametrize(
    "error_type", [KeyboardInterrupt, SystemExit, GeneratorExit, StopIteration]
)
def test_baseexception_and_direct_stopiteration(
    error_type: type[BaseException],
) -> None:
    error = error_type()

    class Custom:
        dims = (1,)
        size = 1
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> tuple[int]:
            return (1,)

        def flat_index(self, *indices: int) -> int:
            raise error

    source: Any = MultiArray(Custom(), np.array([1]))
    if error_type is StopIteration:
        result = source.transpose()
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
    else:
        with pytest.raises(error_type) as caught:
            source.transpose()
        assert caught.value is error


def test_last_external_key_lives_until_result_constructor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ospf_python.multiarray.multi_array as module

    events: list[str] = []
    references: list[weakref.ReferenceType[Any]] = []

    class Key:
        def __index__(self) -> int:
            return 0

        def __del__(self) -> None:
            events.append("drop-key")

    class Custom:
        dims = (1,)
        size = 1
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> tuple[int]:
            return (1,)

        def flat_index(self, *indices: int) -> Key:
            key = Key()
            references.append(weakref.ref(key))
            return key

    source: Any = MultiArray(Custom(), np.array([7]))
    constructor = module.MultiArray

    def finish(shape: Any, data: Any) -> Any:
        assert references[0]() is not None
        events.append("construct")
        return constructor(shape, data)

    monkeypatch.setattr(module, "MultiArray", finish)
    actual = source.transpose().unwrap()
    assert actual._data.tolist() == [7]
    assert references[0]() is None and events == ["construct", "drop-key"]


def test_reentrant_thread_and_no_persistent_native_owner() -> None:
    sources: list[Any] = []

    class Custom:
        dims = (2,)
        size = 2
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> tuple[int]:
            return (1,)

        def flat_index(self, *indices: int) -> int:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future: Any = pool.submit(
                    lambda: MultiArray(Shape1(1), np.array([7])).transpose().unwrap()
                )
                assert future.result(timeout=5)._data.tolist() == [7]
            return indices[0]

    sources.append(MultiArray(Custom(), np.array([1, 2])))
    reference = weakref.ref(sources[0])
    actual = sources[0].transpose().unwrap()
    sources.clear()
    gc.collect()
    assert reference() is None and actual._data.tolist() == [1, 2]


def test_empty_and_overflow_plan_do_not_read_leaves() -> None:
    class Custom:
        size = 0
        storage_order = StorageOrder.ROW_MAJOR
        dims = (0, 3)

        def strides(self) -> tuple[int, int]:
            return (3, 1)

        def flat_index(self, *indices: int) -> int:
            pytest.fail("不得读取 / Must not read")

    source: Any = MultiArray(Custom(), np.empty(0))
    # 旧输出DynShape拒绝零维轴；显式Result保留此构造失败。 / Legacy output DynShape rejects zero axes; preserve this construction failure in Result.
    assert isinstance(source.transpose(), Failed)
    source._shape.dims = (1 << 100, 2)
    result = source.transpose()
    assert isinstance(result, Failed)
    assert result.error.value.category == "OVERFLOW"


def test_source_key_protocol_can_replace_storage_before_read() -> None:
    class Key:
        def __index__(self) -> int:
            return 0

    class Custom:
        dims = (1,)
        size = 1
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> tuple[int]:
            return (1,)

        def flat_index(self, *indices: int) -> Key:
            source._data = np.array([9])
            return Key()

    source: Any = MultiArray(Custom(), np.array([1]))
    assert source.transpose().unwrap()._data.tolist() == [9]


def test_shape_replacement_changes_later_index_lookup_and_final_layout() -> None:
    events: list[Any] = []

    class Later:
        storage_order = StorageOrder.COLUMN_MAJOR

        def flat_index(self, *indices: int) -> int:
            events.append(("later", indices))
            return 4 - (indices[0] * 2 + indices[1])

    class Initial:
        dims = (2, 2)
        size = 4

        def strides(self) -> tuple[int, int]:
            return (2, 1)

        def flat_index(self, *indices: int) -> int:
            events.append(("initial", indices))
            source._shape = Later()
            return 0

    source: Any = MultiArray(Initial(), np.arange(4))
    actual = source.transpose().unwrap()
    assert events == [
        ("initial", (0, 0)),
        ("later", (0, 1)),
        ("later", (1, 0)),
        ("later", (1, 1)),
    ]
    assert actual._data.tolist() == [0, 3, 2, 1]
    assert actual.shape == DynShape((2, 2), StorageOrder.ROW_MAJOR)
