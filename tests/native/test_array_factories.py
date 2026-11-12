"""Rust 填充工厂及逐槽所有权合同 / Rust fill factories and per-slot ownership contracts."""

from __future__ import annotations

import gc
import itertools
import os
import subprocess
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.multiarray import MultiArray, MutableMultiArray, Shape
from ospf_python.multiarray.shape import DynShape, Shape2, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


class _Payload:
    owner: Any = None


class _Hostile:
    def __iter__(self) -> Any:
        raise AssertionError("must not iterate leaf")

    def __len__(self) -> int:
        raise AssertionError("must not measure leaf")

    def __array__(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("must not coerce leaf")

    def __copy__(self) -> Any:
        raise AssertionError("must not copy leaf")

    def item(self) -> Any:
        raise AssertionError("must not convert leaf")


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (5,), (2, 3), (2, 1, 3), (2, 1, 2, 3)])
def test_fill_owns_identical_references_at_every_logical_coordinate(
    *, cls: type[Any], order: StorageOrder, dims: tuple[int, ...]
) -> None:
    shape = Shape.create(dims=dims, storage_order=order).unwrap()
    payload = _Payload()
    before = sys.getrefcount(payload)
    array = cls.full(shape=shape, value=payload).unwrap()
    assert sys.getrefcount(payload) == before + shape.size
    assert array.shape.dims == dims and array.shape.storage_order is order
    for indices in itertools.product(*(range(dim) for dim in dims)):
        assert array.at(indices).unwrap() is payload
    for access in _ORDERS:
        snapshot = array.flatten(access_order=access).unwrap()
        assert len(snapshot) == shape.size
        assert all(item is payload for item in snapshot)
    del snapshot, array
    assert sys.getrefcount(payload) == before


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("method,value", [("zeros", 0.0), ("ones", 1.0)])
def test_float_convenience_factories_use_plain_floats_without_numpy_storage(
    *, cls: type[Any], order: StorageOrder, method: str, value: float
) -> None:
    source_shape = Shape2(2, 3, order)
    array = getattr(cls, method)(shape=source_shape).unwrap()
    assert type(array) is cls
    assert array.shape.dims == (2, 3) and array.shape.storage_order is order
    assert array.to_list().unwrap() == [[value] * 3, [value] * 3]
    assert all(type(item) is float for item in array.flatten().unwrap())
    assert not hasattr(array, "_data")


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("value", [None, [], {"x": 1}, (1, 2), np.int16(7), _Hostile()])
def test_fill_treats_sequences_none_and_numpy_scalars_as_leaf_objects(
    cls: type[Any], value: Any
) -> None:
    array = cls.full(shape=DynShape((2, 2)), value=value).unwrap()
    assert all(item is value for item in array.flatten().unwrap())
    nested = array.to_list().unwrap()
    assert nested[0][0] is value and nested[1][1] is value
    scalar = cls.full(shape=DynShape(()), value=value).unwrap()
    assert scalar.at(()).unwrap() is value
    assert scalar.to_list().unwrap() is value


@pytest.mark.parametrize("cls", _TYPES)
def test_result_is_fill_data_not_a_factory_failure(cls: type[Any]) -> None:
    original = Failed(Err(ErrorCode.NOT_FOUND, "填充值 / Fill data"))
    array = cls.full(shape=DynShape((3,)), value=original).unwrap()
    assert all(item is original for item in array.flatten().unwrap())


def test_mutable_slots_are_independent_but_leaf_state_is_shared() -> None:
    payload: list[int] = []
    first = MutableMultiArray.full(shape=DynShape((2, 3)), value=payload).unwrap()
    second = MutableMultiArray.full(shape=first.shape, value=payload).unwrap()
    frozen = first.to_immutable().unwrap()
    payload.append(7)
    assert first.at((1, 2)).unwrap() is payload
    assert second.at((1, 2)).unwrap() == [7]
    assert first.set(indices=(1, 2), value=None).is_ok()
    assert first.at((1, 2)).unwrap() is None
    assert first.at((0, 0)).unwrap() is payload
    assert second.at((1, 2)).unwrap() is frozen.at((1, 2)).unwrap() is payload


@pytest.mark.parametrize("cls", _TYPES)
def test_shape_validation_and_byte_capacity_fail_before_leaf_protocols(
    cls: type[Any],
) -> None:
    value = _Hostile()
    malformed = []
    for dims in [(0,), (-1,)]:
        shape = DynShape.__new__(DynShape)
        object.__setattr__(shape, "dims", dims)
        object.__setattr__(shape, "storage_order", _ORDERS[0])
        malformed.append(shape)
    for shape in [None, (2, 3), *malformed, DynShape((sys.maxsize, 2))]:
        assert cls.full(shape=shape, value=value).is_failed()
        assert cls.zeros(shape=shape).is_failed()
        assert cls.ones(shape=shape).is_failed()
    shape = Shape.create(dims=(sys.maxsize,)).unwrap()
    before = sys.getrefcount(value)
    result = cls.full(shape=shape, value=value)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.OVERFLOW
    assert result.error.value.source == "ospf-python-native"
    assert sys.getrefcount(value) == before


@pytest.mark.parametrize("cls", _TYPES)
def test_full_preserves_facade_subclass_without_using_legacy_constructors(
    cls: type[Any],
) -> None:
    class Extended(cls):
        pass

    value = _Payload()
    result = Extended.full(shape=DynShape((2,)), value=value).unwrap()
    assert type(result) is Extended
    assert result.at((0,)).unwrap() is value
    assert type(Extended.zeros(shape=DynShape((1,))).unwrap()) is cls
    assert type(Extended.ones(shape=DynShape((1,))).unwrap()) is cls


@pytest.mark.parametrize("cls", _TYPES)
def test_each_duplicate_gc_edge_is_traversed_and_released(cls: type[Any]) -> None:
    for size in [1, 2, 127]:
        payload = _Payload()
        ref = weakref.ref(payload)
        array = cls.full(shape=DynShape((size,)), value=payload).unwrap()
        payload.owner = array
        del array, payload
        gc.collect()
        assert ref() is None


def test_concurrent_fill_and_release_preserves_shared_leaf_lifetime() -> None:
    payload = _Payload()
    before = sys.getrefcount(payload)
    shape = Shape.create(dims=(4, 5)).unwrap()

    def operation(index: int) -> None:
        cls = _TYPES[index % 2]
        array = cls.full(shape=shape, value=payload).unwrap()
        assert all(item is payload for item in array.flatten().unwrap())

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(operation, range(200)))
    assert sys.getrefcount(payload) == before


def test_raw_native_capacity_failure_has_structured_transport() -> None:
    shape = Shape.create(dims=(sys.maxsize,)).unwrap()
    for factory in [_native._full_multiarray, _native._full_mutable_multiarray]:
        value, failure = factory(shape=shape._handle, value=_Hostile())
        assert value is None
        assert failure.category == "OVERFLOW"
        assert failure.rust_code is None


def test_last_fill_reference_finalizer_can_reenter_another_array() -> None:
    code = """
import os, gc
directories = []
if os.name == 'nt':
    directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p]
from ospf_python._binding.multiarray import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape
events = []
target = MutableMultiArray.zeros(shape=DynShape((2,))).unwrap()
class Item:
    def __del__(self):
        replacement = MultiArray.ones(shape=DynShape((3,))).unwrap()
        events.append(replacement.reduce(lambda a, b: a+b).unwrap())
        events.append(target.set(indices=(0,), value=9).is_ok())
source = MutableMultiArray.full(shape=DynShape((16,)), value=Item()).unwrap()
assert source.set_many([((i,), None) for i in range(16)]).is_ok()
assert events == [3.0, True], events
assert target.to_list().unwrap() == [9, 0.0]
print('fill-finalizer-reentry-ok')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-X", "dev", "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
        env={**os.environ, "PYTHONMALLOC": "debug"},
    )
    assert "fill-finalizer-reentry-ok" in completed.stdout
    assert "Exception ignored" not in completed.stderr
