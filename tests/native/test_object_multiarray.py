"""通用 Rust 存储的身份、布局和 GC 合同 / Identity, layout and GC contracts for Rust object storage."""

from __future__ import annotations

import gc
import itertools
import subprocess
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.multiarray import MultiArray, Shape
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


class _Payload:
    def __init__(self) -> None:
        self.owner: object = None


@pytest.mark.parametrize("storage", _ORDERS)
@pytest.mark.parametrize("access", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (6,), (2, 3), (2, 1, 3), (2, 2, 2, 2)])
def test_identity_layout_snapshot_and_reshape(
    *, dims: tuple[int, ...], storage: StorageOrder, access: StorageOrder
) -> None:
    shape = Shape.create(dims=dims, storage_order=storage).unwrap()
    values = [_Payload() for _ in range(shape.size)]
    array = MultiArray.create(values=values, shape=shape, access_order=access).unwrap()
    assert isinstance(array._handle, _native.MultiArray)
    assert len(array) == shape.size
    assert array.shape.dims == dims
    assert array.shape is not array.shape
    oracle = np.empty(len(values), dtype=object)
    oracle[:] = values
    oracle = oracle.reshape(dims, order="C" if access is _ORDERS[0] else "F")
    for vector in itertools.product(*(range(dim) for dim in dims)):
        assert array.at(vector).unwrap() is oracle[vector]
    for output_order in _ORDERS:
        output = array.flatten(access_order=output_order).unwrap()
        expected = oracle.flatten(order="C" if output_order is _ORDERS[0] else "F")
        assert all(a is b for a, b in zip(output, expected, strict=True))
        converted = array.to_storage_order(output_order).unwrap()
        assert converted._handle is not array._handle
        assert converted.shape.storage_order is output_order
        for vector in itertools.product(*(range(dim) for dim in dims)):
            assert converted.at(vector).unwrap() is oracle[vector]
    flattened = array.flatten().unwrap()
    flattened[0].owner = "changed"
    assert array.flatten().unwrap()[0].owner == "changed"
    flattened.clear()
    original = values.copy()
    values.clear()
    assert array.flatten(access_order=access).unwrap()[0] is original[0]
    target = DynShape((shape.size,), storage)
    reshaped = array.reshape(target).unwrap()
    expected = oracle.flatten(order="C" if storage is _ORDERS[0] else "F")
    assert all(
        a is b for a, b in zip(reshaped.flatten().unwrap(), expected, strict=True)
    )


def test_heterogeneous_elements_do_not_coerce_or_copy() -> None:
    class Hostile:
        def __float__(self) -> float:
            raise AssertionError("must not coerce")

        def __eq__(self, other: object) -> bool:
            raise AssertionError("must not compare")

        def __deepcopy__(self, memo: object) -> Any:
            raise AssertionError("must not copy")

    values = [None, False, 1 << 20000, Fraction(1, 3), Decimal("0.1"), Hostile(), []]
    array = MultiArray.create(values=values, shape=DynShape((len(values),))).unwrap()
    for index, value in enumerate(values):
        assert array.at((index,)).is_ok()
        assert array.at((index,)).unwrap() is value
    assert array.at((0,)).unwrap() is None
    assert all(a is b for a, b in zip(values, array.flatten().unwrap(), strict=True))


@pytest.mark.parametrize("values", [None, (), iter([1]), np.array([1]), "x"])
def test_no_implicit_numpy_sharing_or_iterator_execution(values: Any) -> None:
    assert MultiArray.create(values=values, shape=DynShape((1,))).is_failed()


def test_list_subclass_is_not_implicitly_executed() -> None:
    class Items(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("must not run user iterable")

    assert MultiArray.create(values=Items([None]), shape=DynShape((1,))).is_failed()


def test_failed_creation_and_transformations_do_not_publish_partial_storage() -> None:
    payload = _Payload()
    refs = sys.getrefcount(payload)
    for _ in range(50):
        assert MultiArray.create(values=[payload], shape=DynShape((2,))).is_failed()
    assert sys.getrefcount(payload) == refs
    array = MultiArray.create(values=[payload], shape=DynShape((1,))).unwrap()
    assert array.reshape(DynShape((2,))).is_failed()
    assert array.reshape(DynShape((1,), StorageOrder.COLUMN_MAJOR)).is_failed()
    for operation in (
        lambda: array.to_storage_order("C"),
        lambda: array.flatten(access_order=None),
        lambda: array.reshape(object()),
    ):
        assert operation().is_failed()
    assert array.at((0,)).unwrap() is payload
    with pytest.raises(FrozenInstanceError):
        array._handle = None  # type: ignore[misc, assignment]


@pytest.mark.parametrize(
    ("indices", "code"),
    [
        ((), ErrorCode.ILLEGAL_ARGUMENT),
        ((0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((-1,), ErrorCode.OUT_OF_RANGE),
        ((1,), ErrorCode.OUT_OF_RANGE),
        ((1 << 20000,), ErrorCode.OUT_OF_RANGE),
        ((False,), ErrorCode.ILLEGAL_ARGUMENT),
        ((0.0,), ErrorCode.ILLEGAL_ARGUMENT),
        ([0], ErrorCode.ILLEGAL_ARGUMENT),
    ],
)
def test_invalid_coordinates_preserve_result(indices: Any, code: ErrorCode) -> None:
    array = MultiArray.create(values=[None], shape=DynShape((1,))).unwrap()
    result = array.at(indices)
    assert isinstance(result, Failed)
    assert result.error.code is code


def test_each_owned_slot_is_reported_to_gc_including_duplicate_edges() -> None:
    payload = _Payload()
    baseline = sys.getrefcount(payload)
    array = MultiArray.create(values=[payload] * 4, shape=DynShape((2, 2))).unwrap()
    assert sys.getrefcount(payload) == baseline + 4
    assert gc.is_tracked(array._handle)
    referents = gc.get_referents(array._handle)
    assert sum(item is payload for item in referents) == 4
    del referents, array
    assert sys.getrefcount(payload) == baseline


@pytest.mark.parametrize("copies", [1, 2, 16])
def test_cycles_through_facade_and_native_are_collected(copies: int) -> None:
    def cycle() -> weakref.ReferenceType[_Payload]:
        payload = _Payload()
        array = MultiArray.create(
            values=[payload] * copies, shape=DynShape((copies,))
        ).unwrap()
        payload.owner = array
        return weakref.ref(payload)

    references = [cycle() for _ in range(100)]
    gc.collect()
    assert all(reference() is None for reference in references)


def test_reachable_duplicate_payload_is_not_prematurely_cleared() -> None:
    payload = _Payload()
    array = MultiArray.create(values=[payload] * 3, shape=DynShape((3,))).unwrap()
    payload.owner = array
    reference = weakref.ref(payload)
    del array
    gc.collect()
    assert reference() is payload
    assert isinstance(payload.owner, MultiArray)
    assert payload.owner.at((2,)).unwrap() is payload
    del payload
    gc.collect()
    assert reference() is None


def test_snapshot_owns_elements_after_source_array_dies() -> None:
    payload = _Payload()
    reference = weakref.ref(payload)
    array = MultiArray.create(values=[payload], shape=DynShape((1,))).unwrap()
    snapshot = array.flatten().unwrap()
    converted = array.to_storage_order(StorageOrder.COLUMN_MAJOR).unwrap()
    del payload, array
    gc.collect()
    assert reference() is snapshot[0]
    del snapshot
    assert reference() is converted.at((0,)).unwrap()
    del converted
    gc.collect()
    assert reference() is None


def test_cycles_through_independent_transformed_storage_are_collected() -> None:
    def cycle() -> weakref.ReferenceType[_Payload]:
        payload = _Payload()
        source = MultiArray.create(
            values=[payload] * 6, shape=DynShape((2, 3))
        ).unwrap()
        converted = source.to_storage_order(StorageOrder.COLUMN_MAJOR).unwrap()
        reshaped = converted.reshape(
            DynShape((3, 2), StorageOrder.COLUMN_MAJOR)
        ).unwrap()
        payload.owner = [source, converted, reshaped, source.flatten().unwrap()]
        return weakref.ref(payload)

    references = [cycle() for _ in range(100)]
    gc.collect()
    assert all(reference() is None for reference in references)


def test_concurrent_reads_snapshots_and_gc_preserve_identity() -> None:
    values = [_Payload() for _ in range(64)]
    array = MultiArray.create(values=values, shape=DynShape((8, 8))).unwrap()

    def read(index: int) -> None:
        assert array.at(divmod(index % 64, 8)).unwrap() is values[index % 64]
        assert array.flatten().unwrap()[index % 64] is values[index % 64]
        converted = array.to_storage_order(StorageOrder.COLUMN_MAJOR).unwrap()
        assert converted.at(divmod(index % 64, 8)).unwrap() is values[index % 64]
        if index % 20 == 0:
            gc.collect()

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(read, range(400)))


def test_finalizer_reentry_resurrection_and_gc_have_bounded_completion() -> None:
    code = """
import gc
import os
import weakref
directories = []
if os.name == 'nt':
    directories = [os.add_dll_directory(path) for path in
                   os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path]
from ospf_python._binding.multiarray import MultiArray
from ospf_python.multiarray.shape import DynShape, StorageOrder
events = []
resurrected = []
class Item:
    def __del__(self):
        owner = self.owner
        events.append(owner.at((0,)).is_ok())
        events.append(owner.flatten().is_ok())
        events.append(owner.to_storage_order(StorageOrder.COLUMN_MAJOR).is_ok())
        resurrected.append(owner)
def make():
    item = Item()
    array = MultiArray.create(values=[item, item], shape=DynShape((2,))).unwrap()
    item.owner = array
    return weakref.ref(item)
ref = make()
gc.collect()
assert events == [True, True, True], events
assert len(resurrected) == 1
assert resurrected[0].at((0,)).unwrap() is resurrected[0].at((1,)).unwrap()
finalref = weakref.ref(resurrected[0].at((0,)).unwrap())
resurrected.clear()
gc.collect()
assert finalref() is None
assert not gc.garbage
print('finalizer-reentry-ok')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-X", "dev", "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert "finalizer-reentry-ok" in completed.stdout
    assert "Exception ignored" not in completed.stderr
