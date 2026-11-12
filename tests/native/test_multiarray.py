"""Rust 形状、布局与精确数组所有权合同 / Rust shape, layout and exact-array ownership contracts."""

from __future__ import annotations

import gc
import itertools
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.multiarray import RationalMultiArray, Shape
from ospf_python._binding.numeric import RationalArray
from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (7,), (2, 3), (2, 3, 4), (2, 1, 3, 2, 1)])
def test_shape_and_roundtrips_against_numpy(
    dims: tuple[int, ...], order: StorageOrder
) -> None:
    shape = Shape.create(dims=dims, storage_order=order).unwrap()
    assert isinstance(shape._handle, _native.Shape)
    assert shape.dims == dims
    assert shape.ndim == len(dims)
    assert shape.storage_order is order
    numpy_order = "C" if order is StorageOrder.ROW_MAJOR else "F"
    oracle = np.empty(dims, dtype=np.int64, order=numpy_order)
    assert shape.size == oracle.size
    # NumPy 对单元素轴可能给出不同但等效的步长。 / Singleton strides may be equivalent rather than identical in NumPy.
    if all(dim > 1 for dim in dims):
        assert shape.strides() == tuple(stride // 8 for stride in oracle.strides)
    vectors = list(itertools.product(*(range(dim) for dim in dims)))
    expected = [
        int(np.ravel_multi_index(vector, dims, order=numpy_order)) for vector in vectors
    ]
    assert shape.indices_of(vectors).unwrap() == expected
    assert shape.indices_of([]).unwrap() == []
    for vector, index in zip(vectors, expected, strict=True):
        assert shape.index_of(vector).unwrap() == index
        assert shape.vector_of(index).unwrap() == vector


@pytest.mark.parametrize("dims", [None, [], (True,), (1.0,), ("2",), (0,), (-1,)])
def test_invalid_shape_is_a_result(dims: Any) -> None:
    result = Shape.create(dims=dims)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize("order", [None, 1, "C", "F", True])
def test_invalid_shape_order_is_failed(order: Any) -> None:
    assert Shape.create(dims=(2, 3), storage_order=order).is_failed()


@pytest.mark.parametrize("order", _ORDERS)
def test_size_limits_checked_before_upstream_products(order: StorageOrder) -> None:
    largest = Shape.create(dims=(sys.maxsize,), storage_order=order).unwrap()
    assert largest.size == sys.maxsize
    assert largest.strides() == (1,)
    assert largest.vector_of(sys.maxsize - 1).unwrap() == (sys.maxsize - 1,)
    assert largest.index_of((sys.maxsize - 1,)).unwrap() == sys.maxsize - 1
    for dims in ((sys.maxsize, 2), (2, sys.maxsize), (sys.maxsize + 1,)):
        result = Shape.create(dims=dims, storage_order=order)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.OVERFLOW
    assert Shape.create(dims=(1 << 20000,), storage_order=order).is_failed()


@pytest.mark.parametrize(
    ("indices", "code"),
    [
        ((), ErrorCode.ILLEGAL_ARGUMENT),
        ((0,), ErrorCode.ILLEGAL_ARGUMENT),
        ((0, 0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((2, 0), ErrorCode.OUT_OF_RANGE),
        ((0, 3), ErrorCode.OUT_OF_RANGE),
        ((-1, 0), ErrorCode.OUT_OF_RANGE),
        (((1 << 20000), 0), ErrorCode.OUT_OF_RANGE),
        ((True, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((0.0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ([0, 0], ErrorCode.ILLEGAL_ARGUMENT),
    ],
)
def test_index_rejects_truncation_and_aliasing(indices: Any, code: ErrorCode) -> None:
    shape = Shape.create(dims=(2, 3)).unwrap()
    result = shape.index_of(indices)
    assert isinstance(result, Failed)
    assert result.error.code is code
    assert shape.dims == (2, 3)


def test_rust_index_errors_preserve_structural_provenance() -> None:
    shape = Shape.create(dims=(2, 3)).unwrap()
    result = shape.index_of((2, 0))
    assert isinstance(result, Failed)
    assert result.error.value.source == "ospf-rust-multiarray"
    assert result.error.value.error_class == "INPUT"
    assert result.error.value.rust_code is not None


@pytest.mark.parametrize(
    "index",
    [-1, 6, 1 << 20000, -(1 << 20000)],
    ids=["negative", "upper", "huge-positive", "huge-negative"],
)
def test_linear_bounds_are_checked_before_upstream_vector_of(index: int) -> None:
    result = Shape.create(dims=(2, 3)).unwrap().vector_of(index)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.OUT_OF_RANGE


@pytest.mark.parametrize("index", [None, True, "0", 0.0])
def test_linear_type_errors_are_results(index: Any) -> None:
    assert Shape.create(dims=()).unwrap().vector_of(index).is_failed()


@pytest.mark.parametrize(
    "vectors", [None, (), [(0, 0), (2, 0)], [(0, 0), (0,)], [(0, 0), [0, 0]]]
)
def test_bad_late_coordinate_batch_never_returns_partial_output(vectors: Any) -> None:
    result = Shape.create(dims=(2, 3)).unwrap().indices_of(vectors)
    assert isinstance(result, Failed)


@pytest.mark.parametrize("storage_order", _ORDERS)
@pytest.mark.parametrize("access_order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (2, 3), (2, 1, 3), (2, 3, 4)])
def test_exact_array_input_storage_access_and_conversion(
    *, storage_order: StorageOrder, access_order: StorageOrder, dims: tuple[int, ...]
) -> None:
    shape = Shape.create(dims=dims, storage_order=storage_order).unwrap()
    pairs = [((1 << 300) + index, 17) for index in range(shape.size)]
    source = RationalArray.create(pairs).unwrap()
    array = RationalMultiArray.create(
        values=source, shape=shape, access_order=access_order
    ).unwrap()
    assert isinstance(array._handle, _native.RationalMultiArray)
    assert len(array) == shape.size
    assert array.shape.dims == dims
    assert array.shape.storage_order is storage_order
    input_order = "C" if access_order is StorageOrder.ROW_MAJOR else "F"
    oracle = np.array([Fraction(*pair) for pair in pairs], dtype=object).reshape(
        dims, order=input_order
    )
    for vector in itertools.product(*(range(dim) for dim in dims)):
        assert Fraction(*array.at(vector).unwrap().as_integer_ratio()) == oracle[vector]
    for order in _ORDERS:
        flat = array.flatten(access_order=order).unwrap()
        expected = list(oracle.flatten(order="C" if order is _ORDERS[0] else "F"))
        assert [Fraction(*ratio) for ratio in flat.as_integer_ratios()] == expected
        assert Fraction(*flat.sum().as_integer_ratio()) == sum(expected)
        converted = array.to_storage_order(order).unwrap()
        assert converted.shape.storage_order is order
        assert (
            converted.flatten().unwrap().as_integer_ratios()
            == array.flatten().unwrap().as_integer_ratios()
        )
    assert source.as_integer_ratios() == [
        Fraction(*pair).as_integer_ratio() for pair in pairs
    ]


@pytest.mark.parametrize("order", _ORDERS)
def test_reshape_preserves_storage_sequence_and_rejects_padding(
    order: StorageOrder,
) -> None:
    source = RationalArray.create([(i, 7) for i in range(6)]).unwrap()
    array = RationalMultiArray.create(
        values=source, shape=Shape.create(dims=(2, 3), storage_order=order).unwrap()
    ).unwrap()
    target = Shape.create(dims=(3, 2), storage_order=order).unwrap()
    reshaped = array.reshape(target).unwrap()
    assert reshaped.shape.dims == (3, 2)
    assert (
        reshaped.flatten(access_order=order).unwrap().as_integer_ratios()
        == array.flatten(access_order=order).unwrap().as_integer_ratios()
    )
    for dims in ((5,), (7,)):
        assert array.reshape(
            Shape.create(dims=dims, storage_order=order).unwrap()
        ).is_failed()
    opposite = _ORDERS[1] if order is _ORDERS[0] else _ORDERS[0]
    assert array.reshape(
        Shape.create(dims=(6,), storage_order=opposite).unwrap()
    ).is_failed()
    assert array.shape.dims == (2, 3)


def test_array_ownership_is_detached_and_survives_source_destruction() -> None:
    source = RationalArray.create([(1, 2), (3, 4)]).unwrap()
    shape = Shape.create(dims=(1, 2)).unwrap()
    array = RationalMultiArray.create(values=source, shape=shape).unwrap()
    value = array.at((0, 1)).unwrap()
    flat = array.flatten().unwrap()
    snapshot = array.shape
    native_dims = snapshot._handle.dims
    native_dims.clear()
    assert snapshot.dims == (1, 2)
    del source, shape
    gc.collect()
    assert flat.as_integer_ratios() == [(1, 2), (3, 4)]
    assert array.at((0, 1)).unwrap() == value
    del array
    gc.collect()
    assert snapshot.dims == (1, 2)
    assert value.as_integer_ratio() == (3, 4)
    assert flat.sum().as_integer_ratio() == (5, 4)
    assert not hasattr(snapshot, "__dict__")
    with pytest.raises(FrozenInstanceError):
        snapshot._handle = None  # type: ignore[misc,assignment]
    for cls in (_native.Shape, _native.RationalMultiArray):
        with pytest.raises(TypeError):
            cls()


def test_array_invalid_inputs_and_failed_operations_are_nonmutating() -> None:
    source = RationalArray.create([(1, 2)]).unwrap()
    shape = Shape.create(dims=()).unwrap()
    array = RationalMultiArray.create(values=source, shape=shape).unwrap()
    assert RationalMultiArray.create(
        values=RationalArray.create([]).unwrap(), shape=shape
    ).is_failed()
    assert RationalMultiArray.create(
        values=source, shape=Shape.create(dims=(2,)).unwrap()
    ).is_failed()
    for bad in (None, True, "C", 1):
        assert RationalMultiArray.create(values=bad, shape=shape).is_failed()  # type: ignore[arg-type]
        assert RationalMultiArray.create(values=source, shape=bad).is_failed()  # type: ignore[arg-type]
        assert RationalMultiArray.create(
            values=source, shape=shape, access_order=bad
        ).is_failed()  # type: ignore[arg-type]
        assert array.flatten(access_order=bad).is_failed()  # type: ignore[arg-type]
        assert array.to_storage_order(bad).is_failed()  # type: ignore[arg-type]
        assert array.reshape(bad).is_failed()  # type: ignore[arg-type]
        assert array.at(bad).is_failed()  # type: ignore[arg-type]
    assert array.at((0,)).is_failed()
    assert array.at(()).unwrap().as_integer_ratio() == (1, 2)


def test_shared_frozen_array_supports_concurrent_readers() -> None:
    source = RationalArray.create([(i, 17) for i in range(120)]).unwrap()
    shape = Shape.create(dims=(4, 5, 6)).unwrap()
    array = RationalMultiArray.create(values=source, shape=shape).unwrap()

    def read(index: int) -> tuple[int, int]:
        vector = shape.vector_of(index).unwrap()
        assert shape.index_of(vector).unwrap() == index
        return array.at(vector).unwrap().as_integer_ratio()

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(read, range(120))) == source.as_integer_ratios()
    assert array.flatten().unwrap().dot(source).unwrap() == source.dot(source).unwrap()


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("shape_type", [Shape1, Shape2, Shape3, Shape4, DynShape])
def test_public_shapes_are_accepted_as_checked_native_array_snapshots(
    order: StorageOrder, shape_type: type[Any]
) -> None:
    dims = (2, 3, 2, 3)
    rank = [Shape1, Shape2, Shape3, Shape4, DynShape].index(shape_type) + 1
    dims = dims[:rank]
    source = (
        shape_type(dims, order) if shape_type is DynShape else shape_type(*dims, order)
    )
    before = source.__dict__.copy()
    snapshot = Shape.from_shape(source).unwrap()
    assert isinstance(snapshot._handle, _native.Shape)
    assert snapshot.dims == source.dims
    assert snapshot.storage_order is order
    assert snapshot.size == source.size
    assert snapshot.strides() == source.strides()
    values = RationalArray.create([(i, 17) for i in range(source.size)]).unwrap()
    array = RationalMultiArray.create(values=values, shape=source).unwrap()
    assert array.shape.dims == source.dims
    assert array.shape.storage_order is order
    assert array.flatten().unwrap().as_integer_ratios() == values.as_integer_ratios()
    assert source.__dict__ == before
    reshaped = array.reshape(Shape1(source.size, order)).unwrap()
    assert reshaped.shape.dims == (source.size,)
    assert (
        reshaped.flatten().unwrap().as_integer_ratios()
        == array.flatten(access_order=order).unwrap().as_integer_ratios()
    )
    assert array.reshape(Shape1(source.size + 1, order)).is_failed()


def test_public_scalar_snapshot_and_native_subclass_factories() -> None:
    class DerivedNativeShape(Shape):
        pass

    source = DynShape(())
    snapshot = DerivedNativeShape.from_shape(source).unwrap()
    assert type(snapshot) is DerivedNativeShape
    assert isinstance(snapshot._handle, _native.Shape)
    assert snapshot.size == 1
    array = RationalMultiArray.create(
        values=RationalArray.create([(1, 2)]).unwrap(), shape=source
    ).unwrap()
    assert array.at(()).unwrap().as_integer_ratio() == (1, 2)
    assert array.reshape(Shape1(1)).unwrap().at((0,)).unwrap().as_integer_ratio() == (
        1,
        2,
    )


def test_unbounded_public_shapes_fail_only_at_the_native_boundary() -> None:
    source = DynShape((sys.maxsize, 2))
    assert source.size == sys.maxsize * 2
    snapshot = Shape.from_shape(source)
    assert isinstance(snapshot, Failed)
    assert snapshot.error.code is ErrorCode.OVERFLOW
    result = RationalMultiArray.create(
        values=RationalArray.create([]).unwrap(), shape=source
    )
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.OVERFLOW
    assert source.size == sys.maxsize * 2


class ExternalShape:
    """协议属性作为外部代码执行 / Protocol properties execute external user code."""

    def __init__(self) -> None:
        self.axes = (2, 3)
        self.order = StorageOrder.COLUMN_MAJOR
        self.reads: list[str] = []

    @property
    def dims(self) -> tuple[int, ...]:
        self.reads.append("dims")
        return self.axes

    @property
    def storage_order(self) -> StorageOrder:
        self.reads.append("order")
        return self.order

    @property
    def ndim(self) -> int:
        raise AssertionError("User ndim must not be evaluated")

    @property
    def size(self) -> int:
        raise AssertionError("User size must not be evaluated")

    def strides(self) -> tuple[int, ...]:
        raise AssertionError("User strides must not be evaluated")

    def flat_index(self, *indices: int) -> int:
        raise AssertionError("User index algorithm must not be evaluated")


def test_custom_protocol_requires_explicit_standard_layout_confirmation() -> None:
    source = ExternalShape()
    assert Shape.from_shape(source).is_failed()
    assert source.reads == []
    values = RationalArray.create([(i, 17) for i in range(6)]).unwrap()
    assert RationalMultiArray.create(values=values, shape=source).is_failed()
    native = Shape.from_shape(source, standard_layout=True).unwrap()
    assert source.reads == ["dims", "order"]
    assert native.dims == (2, 3)
    assert native.strides() == (1, 2)
    source.axes = (7,)
    source.order = StorageOrder.ROW_MAJOR
    assert native.dims == (2, 3)
    assert native.storage_order is StorageOrder.COLUMN_MAJOR
    array = RationalMultiArray.create(values=values, shape=native).unwrap()
    assert array.at((1, 2)).unwrap().as_integer_ratio() == (5, 17)
    reference = weakref.ref(source)
    del source
    gc.collect()
    assert reference() is None
    assert array.shape.dims == (2, 3)


def test_subclasses_cannot_silently_lose_custom_layout_mapping() -> None:
    class ReverseShape(Shape1):
        def flat_index(self, *indices: int) -> int:
            return self.d0 - 1 - indices[0]

    source = ReverseShape(3)
    assert source.flat_index(0) == 2
    assert Shape.from_shape(source).is_failed()
    snapshot = Shape.from_shape(source, standard_layout=True).unwrap()
    assert snapshot.index_of((0,)).unwrap() == 0


def test_foreign_shape_property_failure_is_a_result_not_a_business_exception() -> None:
    class BrokenShape(ExternalShape):
        @property
        def dims(self) -> tuple[int, ...]:
            raise LookupError("custom-dimension-failure")

    result = Shape.from_shape(BrokenShape(), standard_layout=True)
    assert isinstance(result, Failed)
    assert "custom-dimension-failure" in result.error.message
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_shape_snapshot_does_not_swallow_process_interrupts() -> None:
    class InterruptingShape(ExternalShape):
        @property
        def dims(self) -> tuple[int, ...]:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        Shape.from_shape(InterruptingShape(), standard_layout=True)


@pytest.mark.parametrize("source", [None, 1, [], object()])
def test_unrelated_objects_cannot_masquerade_as_shapes(source: Any) -> None:
    assert Shape.from_shape(source).is_failed()
    assert Shape.from_shape(source, standard_layout=True).is_failed()


@pytest.mark.parametrize("flag", [None, 1, "yes"])
def test_custom_shape_confirmation_is_a_strict_bool(flag: Any) -> None:
    assert Shape.from_shape(ExternalShape(), standard_layout=flag).is_failed()
