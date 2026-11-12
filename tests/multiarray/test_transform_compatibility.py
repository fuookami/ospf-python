"""公开变换切换前合同，不把旧缺陷算验收 / Pre-cutover transform contracts, never accepting legacy defects."""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Any

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

_TYPES = (MultiArray, MutableMultiArray)
_METHODS = ("transpose", "reshape", "flatten")


def _objects(values: list[Any]) -> np.ndarray[Any, Any]:
    data = np.empty(len(values), dtype=object)
    for index, value in enumerate(values):
        data[index] = value
    return data


def _transform(*, source: Any, method: str, target: Any = None) -> Any:
    result = (
        source.reshape(target) if method == "reshape" else getattr(source, method)()
    )
    return result.unwrap()


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("dims", [(), (5,), (2, 3), (2, 1, 3), (1, 2, 1, 3)])
@pytest.mark.parametrize("method", _METHODS)
def test_standard_transforms_preserve_physical_storage_and_copy(
    *, cls: type[Any], order: StorageOrder, dims: tuple[int, ...], method: str
) -> None:
    shape = DynShape(dims, order)
    data = np.arange(shape.size, dtype=np.int16)
    source = cls(shape, data)
    target = DynShape((shape.size,), order)
    result = _transform(source=source, method=method, target=target)
    assert type(result) is MultiArray
    assert result._data.dtype == data.dtype
    np.testing.assert_array_equal(result._data, data)
    assert not np.shares_memory(result._data, data)
    if method == "transpose":
        assert result.shape.dims == tuple(reversed(dims))
        assert result.shape.storage_order is (
            StorageOrder.COLUMN_MAJOR
            if order is StorageOrder.ROW_MAJOR
            else StorageOrder.ROW_MAJOR
        )
        for coords in itertools.product(*(range(dim) for dim in dims)):
            assert result.get(*reversed(coords)) == source.get(*coords)
    elif method == "reshape":
        assert result.shape is target
    else:
        assert result.shape.dims == (shape.size,)
        assert result.shape.storage_order is StorageOrder.ROW_MAJOR
    result._data[0] = 127
    assert data[0] == 0


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize("stride", [1, -1, 2, 0])
@pytest.mark.parametrize(
    "dtype",
    [
        ">i2",
        "<u8",
        "float32",
        "longdouble",
        "clongdouble",
        "datetime64[D]",
        "timedelta64[h]",
        "S4",
        "U4",
    ],
)
def test_strides_endian_and_scalar_domains_are_copied_without_item(
    *, cls: type[Any], method: str, stride: int, dtype: str
) -> None:
    backing = np.array(list(range(12)), dtype=dtype)
    data = (
        np.lib.stride_tricks.as_strided(backing, shape=(6,), strides=(0,))
        if stride == 0
        else backing[::stride][:6]
    )
    source = cls(Shape2(2, 3), data)
    result = _transform(source=source, method=method, target=DynShape((3, 2)))
    assert result._data.dtype == data.dtype
    np.testing.assert_array_equal(result._data, data)
    assert not np.shares_memory(result._data, data)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("method", _METHODS)
def test_structured_fields_and_object_edges_survive_without_leaf_conversion(
    cls: type[Any], method: str
) -> None:
    class Leaf:
        def item(self) -> Any:
            raise AssertionError("不转换不透明叶 / Must not convert opaque leaves")

        def __float__(self) -> float:
            raise AssertionError("不转Float64 / Must not coerce to Float64")

    leaf = Leaf()
    data = np.empty(2, dtype=[("value", ">i2"), ("payload", object)])
    data[0], data[1] = (3, leaf), (7, leaf)
    source = cls(Shape1(2), data)
    result = _transform(source=source, method=method, target=DynShape((1, 2)))
    assert result._data.dtype == data.dtype
    assert result._data[0]["payload"] is result._data[1]["payload"] is leaf
    assert result._data["value"].tolist() == [3, 7]
    assert not np.shares_memory(result._data, data)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("method", _METHODS)
def test_generic_units_results_none_and_nested_arrays_remain_data(
    cls: type[Any], method: str
) -> None:
    values = [
        Quantity(Fraction(1, 7), METER),
        1 << 300,
        Fraction(1, 13),
        None,
        Ok(None),
        Failed(Err(ErrorCode.APPLICATION_ERROR, "数据 / Data")),
        np.array([1, 2]),
    ]
    data = _objects(values)
    data.flags.writeable = False
    source = cls(Shape1(len(values)), data)
    result = _transform(source=source, method=method, target=DynShape((len(values),)))
    assert result._data.dtype == object and result._data.flags.writeable
    assert all(result._data[index] is leaf for index, leaf in enumerate(values))
    assert not np.shares_memory(result._data, data)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", list(StorageOrder))
def test_reshape_explicitly_reinterprets_physical_order_across_layouts(
    cls: type[Any], order: StorageOrder
) -> None:
    other = (
        StorageOrder.COLUMN_MAJOR
        if order is StorageOrder.ROW_MAJOR
        else StorageOrder.ROW_MAJOR
    )
    source = cls(Shape2(2, 3, order), np.arange(6))
    target = DynShape((3, 2), other)
    result = source.reshape(target).unwrap()
    assert result.shape is target
    assert result._data.tolist() == list(range(6))
    for i, j in itertools.product(range(3), range(2)):
        assert result.get(i, j) == (
            i * 2 + j if other is StorageOrder.ROW_MAJOR else i + j * 3
        )


@pytest.mark.parametrize("cls", _TYPES)
def test_reshape_count_is_checked_against_storage_not_source_shape(
    cls: type[Any],
) -> None:
    # flat_map 当前能产生此状态，不能把它当作不可达输入。 / flat_map can produce this state today; it is not unreachable input.
    source = cls(Shape1(2), np.arange(6))
    result = source.reshape(DynShape((3, 2))).unwrap()
    assert result.size == 6 and result._data.tolist() == list(range(6))
    mismatch = source.reshape(DynShape((2,)))
    assert isinstance(mismatch, Failed)
    assert mismatch.error.code == ErrorCode.ILLEGAL_ARGUMENT
    flat = source.flatten().unwrap()
    assert flat.size == 2 and flat._data.tolist() == list(range(6))


@pytest.mark.parametrize("cls", _TYPES)
def test_flatten_retains_actual_ndarray_rank_when_source_storage_is_not_flat(
    cls: type[Any],
) -> None:
    source = cls(Shape1(6), np.arange(6).reshape(2, 3))
    flat = source.flatten().unwrap()
    assert flat.shape.dims == (6,)
    assert flat._data.shape == (2, 3)
    assert not np.shares_memory(flat._data, source._data)
    reshaped = source.reshape(DynShape((3, 2))).unwrap()
    assert reshaped._data.shape == (6,)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("strides", [(3, 1), (1, 2), (3, -1)])
def test_custom_flat_index_and_signed_stride_mapping_are_real_extensions(
    cls: type[Any], strides: tuple[int, int]
) -> None:
    calls: list[Any] = []

    class Custom:
        dims = (2, 3)
        size = 6
        ndim = 2
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> tuple[int, int]:
            calls.append("strides")
            return strides

        def flat_index(self, *indices: int) -> int:
            calls.append(indices)
            return 5 - (3 * indices[0] + indices[1])

    source = cls(Custom(), np.arange(6))
    result = source.transpose().unwrap()
    expected = np.empty(6, dtype=int)
    for i, j in itertools.product(range(2), range(3)):
        expected[strides[0] * i + strides[1] * j] = 5 - (3 * i + j)
    np.testing.assert_array_equal(result._data, expected)
    assert calls == ["strides"] + list(itertools.product(range(2), range(3)))


@pytest.mark.parametrize("cls", _TYPES)
def test_transpose_immutable_reads_live_but_mutable_copies_before_layout_callbacks(
    cls: type[Any],
) -> None:
    class Custom:
        dims = (2, 2)
        size = 4
        ndim = 2
        storage_order = StorageOrder.ROW_MAJOR

        def strides(self) -> tuple[int, int]:
            return (2, 1)

        def flat_index(self, *indices: int) -> int:
            source._data = np.array([9, 8, 7, 6])
            return indices[0] * 2 + indices[1]

    source = cls(Custom(), np.array([1, 2, 3, 4]))
    result = source.transpose().unwrap()
    assert result._data.tolist() == (
        [9, 8, 7, 6] if cls is MultiArray else [1, 2, 3, 4]
    )


@pytest.mark.parametrize("cls", _TYPES)
def test_reshape_external_protocol_order_and_original_exception(cls: type[Any]) -> None:
    events: list[Any] = []
    error = RuntimeError("外部重塑 / External reshape")

    class Flat:
        def copy(self) -> np.ndarray[Any, Any]:
            events.append("copy-final")
            return np.array([1, 2])

    class Shaped:
        def flatten(self) -> Flat:
            events.append("flatten")
            return Flat()

    class Data:
        def copy(self) -> Data:
            events.append("copy-input")
            return self

        @property
        def reshape(self) -> Any:
            events.append("resolve-reshape")

            def reshape(dims: Any) -> Shaped:
                events.append(("reshape", dims))
                return Shaped()

            return reshape

    class Target:
        @property
        def dims(self) -> tuple[int, ...]:
            events.append("target-dims")
            return (2,)

    source = cls(Shape1(2), Data())
    target = Target()
    result = source.reshape(target).unwrap()
    assert result.shape is target and result._data.tolist() == [1, 2]
    assert events == (["copy-input"] if cls is MutableMultiArray else []) + [
        "resolve-reshape",
        "target-dims",
        ("reshape", (2,)),
        "flatten",
        "copy-final",
    ]

    class Invalid:
        def copy(self) -> Invalid:
            raise error

        def reshape(self, dims: Any) -> Any:
            raise error

    source._data = Invalid()
    failed = source.reshape(target)
    assert isinstance(failed, Failed)
    assert failed.error.value.callback_exception is error


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("method", _METHODS)
def test_dtype_subclass_copy_hooks_remain_observable(
    cls: type[Any], method: str
) -> None:
    events: list[Any] = []

    class Data(np.ndarray[Any, Any]):
        def copy(self, order: Any = "C") -> Any:
            events.append("copy")
            return super().copy(order=order)

    data = np.arange(6).view(Data)
    result = _transform(
        source=cls(Shape2(2, 3), data), method=method, target=DynShape((6,))
    )
    assert result._data.tolist() == list(range(6))
    assert len(events) == (
        0
        if method == "transpose" and cls is MultiArray
        else 2
        if method == "reshape" and cls is MutableMultiArray
        else 1
    )
    assert type(result._data) is (np.ndarray if method == "transpose" else Data)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", list(StorageOrder))
def test_transformed_array_feeds_live_view_without_second_storage_authority(
    cls: type[Any], order: StorageOrder
) -> None:
    source = cls(Shape2(2, 3, order), np.arange(6))
    transformed = source.transpose().unwrap()
    view = MultiArrayView(transformed)
    transformed._data[0] = 17
    assert view.get(0, 0) == 17
    assert source.get(0, 0) == 0


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("quantity", [False, True])
def test_transpose_then_mapped_materialize_must_keep_coordinate_correspondence(
    cls: type[Any], quantity: bool
) -> None:
    values = [
        Quantity(Fraction(index, 7), METER) if quantity else index for index in range(6)
    ]
    source = cls(Shape2(2, 3), _objects(values))
    transformed = source.transpose().unwrap()

    def double(value: Any) -> Any:
        return (value * 2).unwrap() if quantity else value * 2

    lazy = MultiArrayView(transformed).map(double)
    actual = lazy.materialize().unwrap()
    for i, j in itertools.product(range(3), range(2)):
        assert actual.get(i, j) == double(transformed.get(i, j))
