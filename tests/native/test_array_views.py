"""可变存储、视图与 NumPy 快照合同 / Mutable storage, views and NumPy snapshot contracts."""

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
from ospf_python._binding.multiarray import (
    MultiArray,
    MultiArrayView,
    MutableMultiArray,
    Shape,
)
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]
_ARRAYS = [MultiArray, MutableMultiArray]


class _Payload:
    owner: object = None


@pytest.mark.parametrize("array_type", _ARRAYS)
@pytest.mark.parametrize("storage", _ORDERS)
@pytest.mark.parametrize(
    ("dims", "offsets", "region_dims"),
    [
        ((), (), ()),
        ((6,), (2,), (3,)),
        ((2, 3), (1, 0), (1, 3)),
        ((3, 4), (1, 1), (2, 2)),
        ((3, 2, 4), (1, 1, 2), (2, 1, 2)),
        ((1, 2, 1, 3), (0, 1, 0, 1), (1, 1, 1, 2)),
    ],
)
def test_checked_region_and_offset_materialization(
    *,
    array_type: Any,
    storage: StorageOrder,
    dims: tuple[int, ...],
    offsets: tuple[int, ...],
    region_dims: tuple[int, ...],
) -> None:
    shape = Shape.create(dims=dims, storage_order=storage).unwrap()
    values = [_Payload() for _ in range(shape.size)]
    array = array_type.create(values=values, shape=shape).unwrap()
    region = DynShape(region_dims, storage)
    view = array.view(offsets=offsets, shape=region).unwrap()
    assert isinstance(view, MultiArrayView)
    assert isinstance(view._handle, _native.MultiArrayView)
    assert view.shape.dims == region_dims
    assert len(view) == view.shape.size
    oracle = np.empty(shape.size, dtype=object)
    oracle[:] = values
    oracle = oracle.reshape(dims)
    expected = (
        oracle
        if not dims
        else oracle[
            tuple(slice(o, o + d) for o, d in zip(offsets, region_dims, strict=True))
        ]
    )
    materialized = view.materialize().unwrap()
    assert materialized.shape.dims == region_dims
    assert materialized.shape.storage_order is storage
    for vector in itertools.product(*(range(dim) for dim in region_dims)):
        assert view.at(vector).unwrap() is expected[vector]
        assert materialized.at(vector).unwrap() is expected[vector]
    for order in _ORDERS:
        flat = view.flatten(access_order=order).unwrap()
        expected_flat = expected.flatten(order="C" if order is _ORDERS[0] else "F")
        assert all(a is b for a, b in zip(flat, expected_flat, strict=True))
    nested = view.view(offsets=(0,) * len(region_dims), shape=region).unwrap()
    assert type(nested) is type(view)
    assert nested._source is array
    assert all(
        a is b
        for a, b in zip(nested.flatten().unwrap(), view.flatten().unwrap(), strict=True)
    )
    del array, values
    gc.collect()
    assert (
        view.at((0,) * len(region_dims)).unwrap()
        is materialized.at((0,) * len(region_dims)).unwrap()
    )


@pytest.mark.parametrize("storage", _ORDERS)
def test_mutable_views_write_through_and_materializations_do_not(
    storage: StorageOrder,
) -> None:
    source = MutableMultiArray.create(
        values=list(range(20)), shape=DynShape((4, 5), storage)
    ).unwrap()
    view = source.view(offsets=(1, 1), shape=DynShape((3, 4), storage)).unwrap()
    subview = view.view(offsets=(1, 2), shape=DynShape((2, 2), storage)).unwrap()
    before = subview.materialize().unwrap()
    frozen = source.to_immutable().unwrap()
    marker = _Payload()
    assert subview.set(indices=(1, 1), value=marker).is_ok()
    assert source.at((3, 4)).unwrap() is marker
    assert view.at((2, 3)).unwrap() is marker
    assert subview.at((1, 1)).unwrap() is marker
    assert before.at((1, 1)).unwrap() == frozen.at((3, 4)).unwrap() == 19
    assert source.set(indices=(2, 3), value=None).is_ok()
    assert subview.at((0, 0)).is_ok()
    assert subview.at((0, 0)).unwrap() is None


@pytest.mark.parametrize("use_view", [False, True])
def test_batch_writes_are_atomic_and_reject_duplicate_coordinates(
    use_view: bool,
) -> None:
    source = MutableMultiArray.create(
        values=[_Payload() for _ in range(6)], shape=DynShape((2, 3))
    ).unwrap()
    writer = (
        source.view(offsets=(0, 1), shape=DynShape((2, 2))).unwrap()
        if use_view
        else source
    )
    baseline = source.flatten().unwrap()
    for updates in (
        [((0, 0), None), ((-1, 0), None)],
        [((0, 0), None), ((2, 0), None)],
        [((0, 0), None), ((0,), None)],
        [((0, 0), None), ((0, 0), None)],
        [((0, 0), None), ((False, 0), None)],
        [((0, 0), None), ((0.0, 0), None)],
        [((0, 0), None), ([0, 0], None)],
        [((0, 0), None), ((0, 1),)],
        (((0, 0), None),),
        None,
    ):
        assert writer.set_many(updates).is_failed()
        assert all(
            a is b for a, b in zip(source.flatten().unwrap(), baseline, strict=True)
        )
    assert writer.set_many([]).is_ok()
    marker = _Payload()
    assert writer.set_many([((0, 0), marker), ((1, 1), None)]).is_ok()
    assert writer.at((0, 0)).unwrap() is marker
    assert writer.at((1, 1)).unwrap() is None


@pytest.mark.parametrize("array_type", _ARRAYS)
@pytest.mark.parametrize(
    ("offsets", "dims", "order"),
    [
        ((0,), (1, 1), _ORDERS[0]),
        ((0, 0), (1,), _ORDERS[0]),
        ((-1, 0), (1, 1), _ORDERS[0]),
        ((2, 0), (1, 1), _ORDERS[0]),
        ((0, 2), (1, 2), _ORDERS[0]),
        ((0, 0), (3, 1), _ORDERS[0]),
        ((0, 0), (1, 1), _ORDERS[1]),
        ((1 << 20000, 0), (1, 1), _ORDERS[0]),
        ((False, 0), (1, 1), _ORDERS[0]),
        ((0.0, 0), (1, 1), _ORDERS[0]),
        ([0, 0], (1, 1), _ORDERS[0]),
    ],
)
def test_bad_regions_are_results(
    *, array_type: Any, offsets: Any, dims: tuple[int, ...], order: StorageOrder
) -> None:
    array = array_type.create(values=list(range(6)), shape=DynShape((2, 3))).unwrap()
    assert array.view(offsets=offsets, shape=DynShape(dims, order)).is_failed()
    view = array.view(offsets=(0, 0), shape=DynShape((2, 3))).unwrap()
    assert view.view(offsets=offsets, shape=DynShape(dims, order)).is_failed()
    for indices in [(), (2, 0), (-1, 0), (False, 0), (0.0, 0), [0, 0]]:
        assert view.at(indices).is_failed()
    assert view.flatten(access_order="C").is_failed()


@pytest.mark.parametrize("array_type", _ARRAYS)
@pytest.mark.parametrize("storage", _ORDERS)
@pytest.mark.parametrize(
    "layout",
    ["C", "F", "transpose", "strided", "negative", "readonly", "broadcast", "scalar"],
)
def test_numpy_snapshots_are_explicit_and_independent(
    *, array_type: Any, storage: StorageOrder, layout: str
) -> None:
    base = np.arange(24, dtype=np.int64).reshape(4, 6)
    source = {
        "C": base,
        "F": np.asfortranarray(base),
        "transpose": base.T,
        "strided": base[::2, 1::2],
        "negative": base[::-1, ::-2],
        "readonly": base.view(),
        "broadcast": np.broadcast_to(base[0, :1], (2, 3)),
        "scalar": np.array(7, dtype=np.int64),
    }[layout]
    if layout == "readonly":
        source.flags.writeable = False
    expected = source.copy()
    array = array_type.from_numpy(
        values=source, copy=True, storage_order=storage
    ).unwrap()
    assert array.shape.dims == source.shape
    assert array.shape.storage_order is storage
    for vector in itertools.product(*(range(dim) for dim in source.shape)):
        assert array.at(vector).unwrap() == expected[vector]
        assert type(array.at(vector).unwrap()) is np.int64
    if source.flags.writeable:
        source[...] = -1
    assert array.flatten().unwrap() == list(expected.ravel(order="C"))
    if isinstance(array, MutableMultiArray):
        before = source.copy()
        assert array.set(indices=(0,) * source.ndim, value=_Payload()).is_ok()
        np.testing.assert_array_equal(source, before)


@pytest.mark.parametrize(
    "dtype",
    [
        np.bool_,
        np.int8,
        np.uint64,
        np.float32,
        np.longdouble,
        np.complex64,
        "U5",
        "S5",
        "datetime64[ns]",
        "timedelta64[ns]",
    ],
)
def test_numpy_scalar_types_are_not_coerced(dtype: Any) -> None:
    source = np.array([1, 2], dtype=dtype)
    array = MultiArray.from_numpy(values=source, copy=True).unwrap()
    for index in range(2):
        value = array.at((index,)).unwrap()
        assert type(value) is type(source[index])
        assert value == source[index]


@pytest.mark.parametrize("array_type", _ARRAYS)
def test_numpy_object_identity_and_cycle_collection(array_type: Any) -> None:
    def cycle() -> weakref.ReferenceType[_Payload]:
        payload = _Payload()
        source = np.empty((2, 2), dtype=object)
        source[:] = payload
        source[0, 1] = None
        array = array_type.from_numpy(values=source, copy=True).unwrap()
        assert array.at((0, 0)).unwrap() is payload
        assert array.at((0, 1)).unwrap() is None
        assert sum(item is payload for item in gc.get_referents(array._handle)) == 3
        assert not any(item is source for item in gc.get_referents(array._handle))
        payload.owner = array.view(offsets=(1, 0), shape=DynShape((1, 2))).unwrap()
        source[:] = None
        return weakref.ref(payload)

    references = [cycle() for _ in range(100)]
    gc.collect()
    assert all(reference() is None for reference in references)


@pytest.mark.parametrize("dtype", [np.int64, object])
@pytest.mark.parametrize("layout", ["C", "F", "negative"])
def test_numpy_snapshot_does_not_retain_source_or_its_base(
    dtype: Any, layout: str
) -> None:
    base = np.arange(12, dtype=np.int64).astype(dtype)
    source = base.reshape(3, 4)
    if layout == "F":
        source = np.asfortranarray(source)
    elif layout == "negative":
        source = source[::-1, ::-1]
    source_reference, base_reference = weakref.ref(source), weakref.ref(base)
    array = MultiArray.from_numpy(values=source, copy=True).unwrap()
    del source, base
    gc.collect()
    assert source_reference() is None
    assert base_reference() is None
    assert len(array.flatten().unwrap()) == 12


@pytest.mark.parametrize("array_type", _ARRAYS)
def test_numpy_unsupported_is_not_silent_copy_or_callback(array_type: Any) -> None:
    class ArrayProtocol:
        def __array__(self) -> Any:
            raise AssertionError("must not execute protocol")

    class SubArray(np.ndarray):
        def ravel(self, *args: Any, **kwargs: Any) -> Any:
            raise AssertionError("must not execute subclass")

    result = array_type.from_numpy(values=np.array([1]), copy=False)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.NOT_SUPPORTED
    assert result.error.value.category == "NOT_SUPPORTED"
    for values in [ArrayProtocol(), np.array([1]).view(SubArray), [], None]:
        assert array_type.from_numpy(values=values, copy=True).is_failed()
    for values in [
        np.array([], dtype=int),
        np.empty((2, 0)),
        np.array([(1,)], dtype=[("x", "i8")]),
        np.array([b"ab"], dtype="V2"),
    ]:
        assert array_type.from_numpy(values=values, copy=True).is_failed()
    assert array_type.from_numpy(values=np.array([1]), copy=1).is_failed()
    assert array_type.from_numpy(
        values=np.array([1]), copy=True, storage_order="C"
    ).is_failed()


def test_native_region_descriptor_rejects_incompatible_source() -> None:
    source = MultiArray.create(values=list(range(6)), shape=DynShape((2, 3))).unwrap()
    view = source.view(offsets=(1, 1), shape=DynShape((1, 2))).unwrap()
    wrong = MultiArray.create(values=list(range(6)), shape=DynShape((3, 2))).unwrap()
    for operation in (
        lambda: wrong._handle.region_at(view._handle, [0, 0]),
        lambda: wrong._handle.region_flatten(view._handle, False),
        lambda: wrong._handle.region_materialize(view._handle),
    ):
        assert operation()[1].category == "ILLEGAL_ARGUMENT"


def test_tuple_subclass_callbacks_are_not_executed_at_checked_boundaries() -> None:
    class Coordinates(tuple[int, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("must not execute user iterator")

    source = MutableMultiArray.create(values=[None], shape=DynShape((1,))).unwrap()
    indices = Coordinates((0,))
    assert source.at(indices).is_failed()
    assert source.set(indices=indices, value=None).is_failed()
    assert source.view(offsets=indices, shape=DynShape((1,))).is_failed()
    assert Shape.create(dims=Coordinates((1,))).is_failed()
    view = source.view(offsets=(0,), shape=DynShape((1,))).unwrap()
    assert view.at(indices).is_failed()
    assert view.set(indices=indices, value=None).is_failed()
    assert view.view(offsets=indices, shape=DynShape((1,))).is_failed()


def test_concurrent_batches_and_snapshots_never_expose_partial_writes() -> None:
    source = MutableMultiArray.create(values=[0] * 16, shape=DynShape((4, 4))).unwrap()
    view = source.view(offsets=(1, 1), shape=DynShape((2, 2))).unwrap()

    def run(index: int) -> None:
        assert source.set_many(
            [(v, index) for v in itertools.product(range(4), repeat=2)]
        ).is_ok()
        snapshot = source.flatten().unwrap()
        assert all(value == snapshot[0] for value in snapshot)
        snapshot = view.flatten().unwrap()
        assert all(value == snapshot[0] for value in snapshot)
        if index % 20 == 0:
            gc.collect()

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(run, range(300)))


def test_replaced_element_destructor_reenters_after_whole_batch_is_published() -> None:
    code = """
import gc, os, weakref
directories = []
if os.name == 'nt':
    directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p]
from ospf_python._binding.multiarray import MutableMultiArray
from ospf_python.multiarray.shape import DynShape
events = []
class Item:
    def __del__(self):
        events.append(source.flatten().unwrap() == [10, 20])
        events.append(view.materialize().unwrap().flatten().unwrap() == [10, 20])
        events.append(view.set(indices=(1,), value=30).is_ok())
source = MutableMultiArray.create(values=[Item(), None], shape=DynShape((2,))).unwrap()
view = source.view(offsets=(0,), shape=DynShape((2,))).unwrap()
assert source.set_many([((0,), 10), ((1,), 20)]).is_ok()
assert events == [True, True, True], events
assert source.flatten().unwrap() == [10, 30]
class Payload: pass
payload = Payload()
ref = weakref.ref(payload)
payload.owner = view
assert view.set(indices=(0,), value=payload).is_ok()
del payload, view, source
gc.collect()
assert ref() is None
print('mutable-reentry-ok')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-X", "dev", "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
        env={**os.environ, "PYTHONMALLOC": "debug"},
    )
    assert "mutable-reentry-ok" in completed.stdout
    assert "Exception ignored" not in completed.stderr
