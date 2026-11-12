"""公开数组切换前的有效行为基线，非原生验收 / Valid public array behavior baseline, not native cutover verification."""

from __future__ import annotations

import copy
import pickle
from typing import Any

import numpy as np
import pytest

import ospf_python.multiarray as public
from ospf_python.multiarray.multi_array import (
    AbstractMultiArray,
    MultiArray,
    MutableMultiArray,
)
from ospf_python.multiarray.multi_array_view import MappedMultiArrayView, MultiArrayView
from ospf_python.multiarray.shape import DynShape, Shape1, Shape2, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed

_TYPES = [MultiArray, MutableMultiArray]


class _ExtendedArray(MultiArray[Any, Any]):
    pass


class _Payload:
    pass


def _identity(value: Any) -> Any:
    return value


def test_public_imports_and_abstract_array_identity() -> None:
    assert public.MultiArray is MultiArray
    assert public.MutableMultiArray is MutableMultiArray
    assert public.AbstractMultiArray is AbstractMultiArray
    assert public.MultiArrayView is MultiArrayView
    assert public.MappedMultiArrayView is MappedMultiArrayView
    assert issubclass(MultiArray, AbstractMultiArray)
    assert issubclass(MutableMultiArray, AbstractMultiArray)


@pytest.mark.parametrize("cls", _TYPES)
def test_constructor_retains_shape_and_external_ndarray(cls: type[Any]) -> None:
    shape = Shape2(2, 3)
    data = np.arange(12)[::2]
    array = cls(shape, data)
    assert array.shape is shape
    assert array._data is data
    assert array.ndim == 2 and array.size == len(array) == 6
    assert array.get(1, 2) == array[1, 2] == 10
    data[0] = 99
    assert array.get(0, 0) == 99
    assert list(array) == [99, 2, 4, 6, 8, 10]


def test_mutable_writes_reach_shared_external_storage() -> None:
    data = np.arange(6)
    array = MutableMultiArray(Shape2(2, 3), data)
    array[1, 2] = 99
    assert data.tolist() == [0, 1, 2, 3, 4, 99]
    array.set(0, 1, 42)
    assert array[0, 1] == data[1] == 42


@pytest.mark.parametrize("cls", _TYPES)
def test_object_identity_none_and_scalar_layout(cls: type[Any]) -> None:
    payload = _Payload()
    array = cls.from_list([payload, None], Shape1(2))
    assert array[0] is payload
    assert array[1] is None
    scalar_data = np.empty(1, dtype=object)
    scalar_data[0] = payload
    scalar = cls(DynShape(()), scalar_data)
    assert scalar.get() is payload
    assert scalar.to_list().unwrap() is payload
    assert list(scalar) == [payload]


@pytest.mark.parametrize("cls", _TYPES)
def test_builtin_numeric_get_returns_python_scalar(cls: type[Any]) -> None:
    array = cls(Shape1(2), np.array([1, 2], dtype=np.int16))
    assert type(array.get(0)) is int
    assert all(type(value) is int for value in array)


@pytest.mark.parametrize("cls", _TYPES)
def test_eager_mapping_reduction_and_row_major_conversion(cls: type[Any]) -> None:
    array = cls.from_list([[1, 2, 3], [4, 5, 6]], Shape2(2, 3))
    calls = []

    def callback(value: int) -> int:
        calls.append(value)
        return value * 2

    mapped = array.map(callback).unwrap()
    assert isinstance(mapped, MultiArray)
    assert calls == [1, 2, 3, 4, 5, 6]
    assert mapped.to_list().unwrap() == [[2, 4, 6], [8, 10, 12]]
    assert array.reduce(lambda left, right: left - right).unwrap() == -19
    flattened = array.flatten().unwrap()
    assert flattened.shape.dims == (6,)
    assert flattened.to_list().unwrap() == [1, 2, 3, 4, 5, 6]
    assert not np.shares_memory(flattened._data, array._data)
    reshaped = array.reshape(DynShape((3, 2))).unwrap()
    assert reshaped.to_list().unwrap() == [[1, 2], [3, 4], [5, 6]]
    assert not np.shares_memory(reshaped._data, array._data)


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
@pytest.mark.parametrize("cls", _TYPES)
def test_pickle_and_copy_preserve_array_state(cls: type[Any], protocol: int) -> None:
    array = cls.from_list([[1, 2, 3], [4, 5, 6]], Shape2(2, 3))
    restored = pickle.loads(pickle.dumps(array, protocol=protocol))
    assert type(restored) is cls
    assert restored.shape == array.shape
    assert restored.to_list().unwrap() == array.to_list().unwrap()
    assert not np.shares_memory(restored._data, array._data)
    shallow = copy.copy(array)
    assert shallow.shape is array.shape and shallow._data is array._data
    deep = copy.deepcopy(array)
    assert deep.shape == array.shape
    assert not np.shares_memory(deep._data, array._data)


def test_subclass_extra_state_and_legacy_field_only_restore() -> None:
    original = _ExtendedArray(Shape1(2), np.array([1, 2]))
    original.tag = {"purpose": "downstream"}
    restored = pickle.loads(pickle.dumps(original))
    assert type(restored) is _ExtendedArray
    assert restored.tag == original.tag
    assert restored.to_list().unwrap() == [1, 2]
    field_only = MultiArray.__new__(MultiArray)
    field_only.__dict__.update(_shape=Shape1(2), _data=np.array([3, 4]))
    assert field_only.to_list().unwrap() == [3, 4]
    assert pickle.loads(pickle.dumps(field_only)).to_list().unwrap() == [3, 4]


def test_lazy_public_view_reexecutes_callbacks_and_observes_mutations() -> None:
    source = MutableMultiArray.from_list([1, 2, 3], Shape1(3))
    calls = []

    def callback(value: int) -> int:
        calls.append(value)
        return value * 10

    view = MultiArrayView(source)
    mapped = view.map(callback)
    assert calls == []
    assert mapped.shape is source.shape and mapped.ndim == 1
    assert mapped.get(0) == mapped.get(0) == 10
    assert calls == [1, 1]
    source[0] = 9
    assert mapped.get(0) == 90
    assert calls == [1, 1, 9]
    snapshot = mapped.materialize().unwrap()
    assert snapshot.to_list().unwrap() == [90, 20, 30]
    source[0] = 7
    assert snapshot[0] == 90 and mapped.get(0) == 70


def test_column_major_coordinates_and_physical_iteration_are_distinct() -> None:
    array = MultiArray(Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6))
    assert [[array.get(row, col) for col in range(3)] for row in range(2)] == [
        [0, 2, 4],
        [1, 3, 5],
    ]
    assert list(array) == [0, 1, 2, 3, 4, 5]


def test_public_lazy_view_does_not_interpret_callback_result_objects() -> None:
    source = MultiArray.from_list([1], Shape1(1))
    original = Failed(Err(ErrorCode.NOT_FOUND, "作为数据 / As data"))
    mapped = MultiArrayView(source).map(lambda value: original)
    assert mapped.get(0) is original


def test_public_callback_exception_is_currently_a_direct_protocol_failure() -> None:
    source = MultiArray.from_list([1], Shape1(1))
    error = ValueError("外部回调失败 / External callback failure")

    def callback(value: Any) -> Any:
        raise error

    mapped = MultiArrayView(source).map(callback)
    with pytest.raises(ValueError) as raised:
        mapped.get(0)
    assert raised.value is error


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_public_scalar_factories_preserve_shape_dtype_and_leaf_contracts(
    *, cls: type[Any], order: StorageOrder
) -> None:
    shape = Shape2(2, 3, order)
    for name, value in [("zeros", 0.0), ("ones", 1.0)]:
        array = getattr(cls, name)(shape)
        assert type(array) is cls and array.shape is shape
        assert array._data.dtype == np.dtype("float64")
        assert list(array) == [value] * 6
        assert all(type(item) is float for item in array)
    payload = _Payload()
    array = cls.full(shape, payload)
    assert array.shape is shape and array._data.dtype == np.dtype("object")
    assert all(item is payload for item in array)
    assert all(item is None for item in cls.full(shape, None))
    assert list(cls.full(shape, "leaf")) == ["leaf"] * 6


@pytest.mark.parametrize("cls", _TYPES)
def test_public_from_list_copies_structure_but_preserves_object_leaves(
    cls: type[Any],
) -> None:
    shape = Shape2(2, 2)
    payload = _Payload()
    data = [[payload, None], [1, 2]]
    array = cls.from_list(data, shape)
    assert array.shape is shape and array._data.dtype == np.dtype("object")
    assert array[0, 0] is payload and array[0, 1] is None
    data[0][0] = None
    assert array[0, 0] is payload
    assert array.to_list().unwrap() == [[payload, None], [1, 2]]


def test_public_valid_equality_repr_and_mutable_identity_protocols() -> None:
    left = MultiArray(Shape1(2), np.array([1, 2], dtype=np.int16))
    right = MultiArray(Shape1(2), np.array([1.0, 2.0]))
    assert left == right
    assert left != MultiArray(Shape1(2), np.array([1, 3]))
    assert left != MultiArray(Shape2(1, 2), np.array([1, 2]))
    assert MultiArray.__eq__(left, object()) is NotImplemented
    assert repr(left) == "MultiArray(shape=(2,), data=[1, 2])"
    first = MutableMultiArray.from_list([1, 2], Shape1(2))
    second = MutableMultiArray.from_list([1, 2], Shape1(2))
    assert first == first and first != second
    assert MutableMultiArray.__hash__ is object.__hash__
    assert MutableMultiArray.__repr__ is object.__repr__


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_public_pickle_preserves_recursive_leaf_graph(
    cls: type[Any], protocol: int
) -> None:
    payload = _Payload()
    array = cls.from_list([payload, payload], Shape1(2))
    payload.owner = array
    restored = pickle.loads(pickle.dumps(array, protocol=protocol))
    assert restored[0] is restored[1]
    assert restored[0] is not payload
    assert restored[0].owner is restored


@pytest.mark.parametrize("cls", _TYPES)
def test_public_deepcopy_preserves_recursive_leaf_graph(cls: type[Any]) -> None:
    payload = _Payload()
    array = cls.from_list([payload, payload], Shape1(2))
    payload.owner = array
    restored = copy.deepcopy(array)
    assert restored[0] is restored[1]
    assert restored[0].owner is restored
    assert restored[0] is not payload


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_public_lazy_pickle_preserves_global_callable_and_source_alias(
    protocol: int,
) -> None:
    source = MultiArray.from_list([1, 2], Shape1(2))
    mapped = MultiArrayView(source).map(_identity)
    restored_source, restored_mapped = pickle.loads(
        pickle.dumps((source, mapped), protocol=protocol)
    )
    assert restored_mapped._source._source is restored_source
    assert restored_mapped._f is _identity
    assert restored_mapped.get(1) == 2
