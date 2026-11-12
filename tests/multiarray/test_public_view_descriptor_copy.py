"""固定 Rust 区域描述符的存储复制 / Storage copying from pinned Rust region descriptors."""

from __future__ import annotations

import gc
import itertools
import math
import weakref
from collections.abc import Iterator
from typing import Any, cast

import numpy as np
import pytest

from ospf_python.multiarray import (
    DynShape,
    MultiArray,
    MultiArrayView,
    MutableMultiArray,
    Shape2,
    StorageOrder,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


def source_indices(
    *, dims: tuple[int, ...], offsets: tuple[int, ...], order: StorageOrder
) -> list[int]:
    coordinates = list(itertools.product(*(range(dim) for dim in dims)))
    remaining: Iterator[tuple[int, ...]] = itertools.product(
        *(range(offset, dim) for offset, dim in zip(offsets, dims, strict=True))
    )
    if order is StorageOrder.COLUMN_MAJOR:
        coordinates.sort(key=lambda coordinate: coordinate[::-1])
        remaining = iter(sorted(remaining, key=lambda coordinate: coordinate[::-1]))
    locations = {coordinate: ordinal for ordinal, coordinate in enumerate(coordinates)}
    return [locations[coordinate] for coordinate in remaining]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize(
    "dims", [(), (5,), (3, 4), (2, 3, 4), (1, 3, 1, 4), (1,) * 80 + (2,)]
)
@pytest.mark.parametrize("tail", [(), (2,), (2, 3), (0,)])
@pytest.mark.parametrize(
    "domain",
    ["i2", ">i4", "object", "structured", "structured_object", "string", "void"],
)
@pytest.mark.parametrize("cropped", [False, True])
def test_descriptor_copy_preserves_all_storage_axes_and_dtype_ownership(
    *,
    storage: type[Any],
    order: StorageOrder,
    dims: tuple[int, ...],
    tail: tuple[int, ...],
    domain: str,
    cropped: bool,
) -> None:
    dtype: Any = {
        "structured": np.dtype([("i", "i2"), ("s", "U3")]),
        "structured_object": np.dtype([("payload", object), ("i", "i2")]),
        "string": np.dtypes.StringDType(na_object=None),
        "void": np.dtype("V0"),
    }.get(domain, domain)
    data = np.empty((math.prod(dims),) + tail, dtype=dtype)
    for index in range(data.size):
        if domain == "object":
            data.flat[index] = object()
        elif domain == "structured":
            data.flat[index] = (index, str(index))
        elif domain == "structured_object":
            data.flat[index] = (object(), index)
        elif domain == "string":
            data.flat[index] = (
                None if index % 3 == 0 else str(index) + "x" * 80 + chr(0x1F600)
            )
        elif domain != "void":
            data.flat[index] = index
    offsets = tuple(1 if cropped and dim > 1 else 0 for dim in dims)
    shape = DynShape(dims, order)
    source = storage(shape, data)
    view = MultiArrayView(source, offsets=offsets)
    actual = view.materialize().unwrap()
    expected = data.take(
        source_indices(dims=dims, offsets=offsets, order=order), axis=0
    )
    assert actual._data.tolist() == expected.tolist()
    assert actual._data.shape == expected.shape and actual._data.dtype == data.dtype
    assert actual._data.flags.owndata and actual._data.base is None
    assert not np.shares_memory(actual._data, data)
    assert actual.shape.dims == tuple(
        dim - offset for dim, offset in zip(dims, offsets, strict=True)
    )
    assert actual.shape.storage_order is order
    if not any(offsets):
        assert actual.shape is shape
    if domain == "object":
        assert all(
            a is b for a, b in zip(actual._data.flat, expected.flat, strict=True)
        )
    if domain == "structured_object":
        assert all(
            a is b
            for a, b in zip(
                actual._data["payload"].flat, expected["payload"].flat, strict=True
            )
        )
    assert vars(view) == {"_source": source, "_offsets": offsets}


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("mode", ["negative", "transpose", "broadcast", "readonly"])
def test_exact_copy_results_can_be_strided_and_are_not_retained(
    *, order: StorageOrder, mode: str
) -> None:
    data = np.arange(36, dtype=np.int16).reshape(12, 3)
    if mode == "negative":
        data = data[::-1, ::-1]
    elif mode == "transpose":
        data = np.arange(36, dtype=np.int16).reshape(3, 12).T
    elif mode == "broadcast":
        data = np.broadcast_to(np.arange(3, dtype=np.int16), (12, 3))
    else:
        data.flags.writeable = False

    class Data:
        def __init__(self, returned: Any) -> None:
            self.returned = returned

        def copy(self) -> Any:
            return self.returned

    buffer_ref = weakref.ref(data)
    source: MultiArray[int, Shape2] = MultiArray(
        Shape2(3, 4, order), cast("Any", Data(data))
    )
    view = MultiArrayView(source, offsets=(1, 1))
    expected = data.take(
        source_indices(dims=(3, 4), offsets=(1, 1), order=order), axis=0
    )
    actual = view.materialize().unwrap()
    np.testing.assert_array_equal(actual._data, expected)
    assert actual._data.flags.owndata and actual._data.base is None
    assert not np.shares_memory(actual._data, data)
    del source, view, data
    gc.collect()
    assert buffer_ref() is None


@pytest.mark.parametrize("order", list(StorageOrder))
def test_ndarray_subclasses_keep_the_actual_copy_take_protocol(
    order: StorageOrder,
) -> None:
    calls: list[tuple[list[int], int]] = []

    class Data(np.ndarray[Any, Any]):
        def take(self, *args: Any, **kwargs: Any) -> Any:
            assert len(args) == 1 and isinstance(args[0], list)
            assert kwargs == {"axis": 0}
            calls.append((args[0], kwargs["axis"]))
            return np.asarray(self).take(args[0], **kwargs)

    data = np.arange(12).view(Data)
    source: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4, order), data)
    actual = MultiArrayView(source, offsets=(1, 1)).materialize().unwrap()
    expected = source_indices(dims=(3, 4), offsets=(1, 1), order=order)
    assert calls == [(expected, 0)] and actual._data.tolist() == expected


def test_output_shape_factory_precedes_region_copy_and_runs_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ospf_python._binding.shared_view as bridge

    events: list[str] = []
    data = np.arange(12)

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            return data

    original = DynShape

    def make_shape(dims: Any, order: Any) -> Any:
        events.append("shape")
        data[5] = 999
        return original(dims, order)

    source: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4), cast("Any", Data()))
    monkeypatch.setattr(bridge, "DynShape", make_shape)
    result = MultiArrayView(source, offsets=(1, 1)).materialize().unwrap()
    assert result._data.tolist() == [999, 6, 7, 9, 10, 11]
    assert events == ["copy", "shape"]


def test_maximum_storage_rank_uses_checked_gather_without_repeating_shape_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ospf_python._binding.shared_view as bridge

    calls: list[tuple[int, ...]] = []

    def make_shape(dims: Any, order: Any) -> Any:
        calls.append(dims)
        return DynShape(dims, order)

    data = np.arange(12).reshape((12,) + (1,) * 63)
    source: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4), data)
    monkeypatch.setattr(bridge, "DynShape", make_shape)
    result = MultiArrayView(source, offsets=(1, 1)).materialize().unwrap()
    assert result._data.shape == (6,) + (1,) * 63
    assert result._data.ravel().tolist() == [5, 6, 7, 9, 10, 11]
    assert calls == [(2, 3)]


@pytest.mark.parametrize(
    "dims,code",
    [
        ((-1, 4), ErrorCode.ILLEGAL_ARGUMENT),
        ((np.int64(-1), 4), ErrorCode.ILLEGAL_ARGUMENT),
        ((np.uint64(2**64 - 1), 4), ErrorCode.OVERFLOW),
    ],
)
def test_fast_integer_protocol_keeps_signed_and_unsigned_failure_categories(
    *, dims: Any, code: ErrorCode
) -> None:
    shape = DynShape((3, 4))
    object.__setattr__(shape, "dims", dims)
    source: MultiArray[int, DynShape] = MultiArray(shape, np.arange(12))
    result = MultiArrayView(source, offsets=(1, 1)).materialize()
    assert isinstance(result, Failed) and result.error.code is code


def test_integer_validation_short_circuits_before_later_external_metadata() -> None:
    def dimensions() -> Any:
        yield 0
        pytest.fail(
            "无效首维后不能继续读取 / Must stop after the invalid first dimension"
        )

    shape = DynShape((3, 4))
    object.__setattr__(shape, "dims", dimensions())
    source: MultiArray[int, DynShape] = MultiArray(shape, np.arange(12))
    result = MultiArrayView(source, offsets=(1, 1)).materialize()
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("changed_shape", [(6,), (24,), (3, 4), ()])
def test_shape_factory_storage_invalidation_fails_before_descriptor_publication(
    *,
    storage: type[Any],
    order: StorageOrder,
    changed_shape: tuple[int, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ospf_python._binding.shared_view as bridge
    import ospf_python.multiarray.multi_array_view as module

    data = np.arange(12)
    events: list[str] = []

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            return data

    def make_shape(dims: Any, layout: Any) -> DynShape:
        events.append("shape")
        data.resize(changed_shape, refcheck=False)
        return DynShape(dims, layout)

    def construct(*args: Any) -> Any:
        pytest.fail("失效缓冲不得发布 / Must not publish invalidated storage")

    source = storage(Shape2(3, 4, order), cast("Any", Data()))
    view = MultiArrayView(source, offsets=(1, 1))
    monkeypatch.setattr(bridge, "DynShape", make_shape)
    monkeypatch.setattr(module, "MultiArray", construct)
    result = view.materialize()
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert events == ["copy", "shape"]
    assert vars(view) == {"_source": source, "_offsets": (1, 1)}


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("tail", [(1,), (2,), (0,)])
def test_shape_factory_keeps_valid_changes_to_actual_trailing_storage_axes(
    *,
    storage: type[Any],
    order: StorageOrder,
    tail: tuple[int, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ospf_python._binding.shared_view as bridge

    data = np.arange(12)
    calls: list[tuple[int, ...]] = []

    class Data:
        def copy(self) -> Any:
            return data

    def make_shape(dims: Any, layout: Any) -> DynShape:
        calls.append(dims)
        data.resize((12,) + tail, refcheck=False)
        return DynShape(dims, layout)

    source = storage(Shape2(3, 4, order), cast("Any", Data()))
    monkeypatch.setattr(bridge, "DynShape", make_shape)
    actual = MultiArrayView(source, offsets=(1, 1)).materialize().unwrap()
    expected = data.take(
        source_indices(dims=(3, 4), offsets=(1, 1), order=order), axis=0
    )
    np.testing.assert_array_equal(actual._data, expected)
    assert actual._data.shape == (6,) + tail
    assert actual._data.flags.owndata and actual._data.base is None
    assert calls == [(2, 3)]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("domain", ["string", "structured_object"])
def test_owned_dtype_payload_survives_source_and_temporary_copy_collection(
    *, storage: type[Any], order: StorageOrder, domain: str
) -> None:
    dtype = (
        np.dtypes.StringDType(na_object=None)
        if domain == "string"
        else np.dtype([("payload", object), ("i", "i2")])
    )
    data = np.empty(12, dtype=dtype)
    for index in range(12):
        data[index] = (
            (None if index % 3 == 0 else str(index) + "x" * 80 + chr(0x1F600))
            if domain == "string"
            else (object(), index)
        )
    expected = data.take(
        source_indices(dims=(3, 4), offsets=(1, 1), order=order), axis=0
    ).tolist()
    source = storage(Shape2(3, 4, order), data)
    view = MultiArrayView(source, offsets=(1, 1))
    actual = view.materialize().unwrap()
    source_ref = weakref.ref(data)
    del source, view, data
    gc.collect()
    assert source_ref() is None
    assert actual._data.tolist() == expected
    assert actual._data.flags.owndata and actual._data.base is None
    if domain == "structured_object":
        assert all(
            leaf is row[0]
            for leaf, row in zip(actual._data["payload"].flat, expected, strict=True)
        )
