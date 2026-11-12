"""Rust 引用数组的复制、对象图和版本化快照 / Copy, object graphs and versioned Rust reference-array snapshots."""

from __future__ import annotations

import copy
import gc
import itertools
import pickle
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.multiarray import (
    MappedMultiArrayView,
    MultiArray,
    MutableMultiArray,
    Shape,
)
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


class _Payload:
    owner: Any = None


class _Extended(MultiArray[Any]):
    __slots__ = ("label", "__private", "__dict__", "__weakref__")


class _ExtendedMutable(MutableMultiArray[Any]):
    __slots__ = ("label", "__private", "__dict__", "__weakref__")


class _Callback:
    def __init__(self, owner: Any) -> None:
        self.owner = owner
        self.calls = 0

    def __call__(self, value: Any) -> Any:
        self.calls += 1
        return value


class _Unpicklable:
    def __reduce__(self) -> Any:
        raise ValueError("外部叶序列化失败 / External leaf serialization failure")


class _RestoreReader:
    owner: Any = None

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.observed = self.owner.at([0])[1].category
        assert MultiArray.ones(shape=DynShape((2,))).unwrap().flatten().unwrap() == [
            1.0,
            1.0,
        ]


def _twice(value: Any) -> Any:
    return value * 2


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (2, 3), (2, 1, 3)])
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_all_pickle_protocols_preserve_layout_and_recursive_leaf_aliases(
    *, cls: type[Any], order: StorageOrder, dims: tuple[int, ...], protocol: int
) -> None:
    payload = _Payload()
    original = cls.full(shape=DynShape(dims, order), value=payload).unwrap()
    payload.owner = original
    restored = pickle.loads(pickle.dumps(original, protocol=protocol))
    assert type(restored) is cls and restored._handle is not original._handle
    assert restored.shape.dims == dims and restored.shape.storage_order is order
    leaf = restored.at((0,) * len(dims)).unwrap()
    assert leaf is not payload and leaf.owner is restored
    assert all(item is leaf for item in restored.flatten().unwrap())
    ref = weakref.ref(leaf)
    del restored, leaf
    gc.collect()
    assert ref() is None


@pytest.mark.parametrize("cls", [_Extended, _ExtendedMutable])
@pytest.mark.parametrize("method", [copy.copy, copy.deepcopy])
def test_copy_preserves_subclass_dict_slots_and_memo_aliases(
    cls: type[Any], method: Any
) -> None:
    payload = _Payload()
    array = cls.full(shape=DynShape((2,)), value=payload).unwrap()
    payload.owner = array
    object.__setattr__(array, "label", payload)
    private_name = "_" + cls.__name__.lstrip("_") + "__private"
    object.__setattr__(array, private_name, payload)
    array.__dict__["extra"] = {"alias": payload, "array": array}
    restored = method(array)
    assert type(restored) is cls
    if method is copy.copy:
        assert restored._handle is array._handle
        assert restored.label is payload
        assert restored.extra is array.extra
    else:
        leaf = restored.at((0,)).unwrap()
        assert leaf is not payload and leaf.owner is restored
        assert restored.label is getattr(restored, private_name) is leaf
        assert restored.extra["alias"] is leaf
        assert restored.extra["array"] is restored


@pytest.mark.parametrize("cls", [_Extended, _ExtendedMutable])
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_preserves_subclass_extra_state(cls: type[Any], protocol: int) -> None:
    payload = _Payload()
    array = cls.full(shape=DynShape((2,)), value=payload).unwrap()
    object.__setattr__(array, "label", payload)
    array.__dict__["extra"] = array
    restored = pickle.loads(pickle.dumps(array, protocol=protocol))
    assert type(restored) is cls and restored.extra is restored
    assert restored.label is restored.at((0,)).unwrap()


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_tuple_graph_keeps_shared_handle_views_offsets_and_live_lazy_mapping(
    order: StorageOrder, protocol: int
) -> None:
    source = MutableMultiArray.create(
        values=list(range(12)), shape=DynShape((3, 4), order)
    ).unwrap()
    shallow = copy.copy(source)
    view = source.view(offsets=(1, 1), shape=DynShape((2, 3), order)).unwrap()
    nested = view.view(offsets=(1, 1), shape=DynShape((1, 2), order)).unwrap()
    lazy = MappedMultiArrayView.create(source=nested, callback=_twice).unwrap()
    restored, alias, region, mapped = pickle.loads(
        pickle.dumps((source, shallow, nested, lazy), protocol=protocol)
    )
    assert restored._handle is alias._handle
    assert region._source is restored and mapped._source is region
    assert region.to_list().unwrap() == [[10, 11]]
    assert mapped.at((0, 1)).unwrap() == 22
    region.set(indices=(0, 1), value=30).unwrap()
    assert alias.at((2, 3)).unwrap() == 30
    assert mapped.at((0, 1)).unwrap() == 60
    assert source.at((2, 3)).unwrap() == 11


def test_deepcopy_graph_preserves_callback_source_cycle_without_executing_callback() -> (
    None
):
    source = MutableMultiArray.ones(shape=DynShape((2,))).unwrap()
    callback = _Callback(source)
    lazy = MappedMultiArrayView.create(source=source, callback=callback).unwrap()
    callback.lazy = lazy
    cloned = copy.deepcopy(lazy)
    new_callback = cloned._callbacks[0]
    assert new_callback is not callback and new_callback.calls == callback.calls == 0
    assert new_callback.owner is cloned._source and new_callback.lazy is cloned
    assert cloned.at((0,)).unwrap() == 1.0
    assert new_callback.calls == 1 and callback.calls == 0
    ref = weakref.ref(new_callback)
    del cloned, new_callback
    gc.collect()
    assert ref() is None


@pytest.mark.parametrize("cls", _TYPES)
def test_protocol_keeps_numpy_leaf_dtype_and_shared_object_arrays(
    cls: type[Any],
) -> None:
    payload = _Payload()
    array = cls.create(
        values=[np.int16(7), Fraction(2, 3), payload, payload, None],
        shape=DynShape((5,)),
    ).unwrap()
    for operation in [copy.deepcopy, lambda value: pickle.loads(pickle.dumps(value))]:
        restored = operation(array)
        values = restored.flatten().unwrap()
        assert type(values[0]) is np.int16 and values[0] == 7
        assert values[1] == Fraction(2, 3)
        assert values[2] is values[3] and values[2] is not payload
        assert values[4] is None


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_versioned_reference_snapshot_is_detached_physical_dto_not_graph_relocation(
    cls: type[Any], order: StorageOrder
) -> None:
    payload = _Payload()
    array = cls.create(
        values=[payload, None, 2, 3, 4, 5], shape=DynShape((2, 3), order)
    ).unwrap()
    payload.owner = array
    snapshot = array.to_snapshot().unwrap()
    assert set(snapshot) == {
        "schema",
        "version",
        "kind",
        "dims",
        "storage_order",
        "values",
    }
    assert snapshot["storage_order"] == order.name
    assert snapshot["values"] == array.flatten(access_order=order).unwrap()
    restored = cls.from_snapshot(snapshot).unwrap()
    assert restored.at((0, 0)).unwrap() is payload
    assert payload.owner is array
    for indices in itertools.product(range(2), range(3)):
        assert restored.at(indices).unwrap() is array.at(indices).unwrap()
    snapshot["values"].clear()
    assert restored.at((0, 0)).unwrap() is payload
    if cls is MutableMultiArray:
        restored.set(indices=(0, 0), value=9).unwrap()
        assert array.at((0, 0)).unwrap() is payload


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", "unknown"),
        ("version", 2),
        ("version", True),
        ("kind", "wrong"),
        ("dims", (0,)),
        ("dims", (sys.maxsize, 2)),
        ("dims", [2]),
        ("storage_order", "C"),
        ("storage_order", 1),
        ("values", (1, 2)),
        ("values", []),
    ],
)
def test_snapshot_rejects_invalid_metadata_without_publishing_partial_arrays(
    *, cls: type[Any], field: str, value: Any
) -> None:
    source = cls.ones(shape=DynShape((2,))).unwrap()
    snapshot = source.to_snapshot().unwrap()
    snapshot[field] = value
    assert cls.from_snapshot(snapshot).is_failed()
    assert source.flatten().unwrap() == [1.0, 1.0]


@pytest.mark.parametrize("cls", _TYPES)
def test_snapshot_unknown_missing_keys_dict_subclasses_and_kind_mismatch(
    cls: type[Any],
) -> None:
    class Hostile(dict[str, Any]):
        def __iter__(self) -> Any:
            raise AssertionError("must not iterate dict subclass")

    source = cls.ones(shape=DynShape((2,))).unwrap()
    valid = source.to_snapshot().unwrap()
    for value in [
        None,
        [],
        Hostile(valid),
        {**valid, "extra": 1},
        {key: value for key, value in valid.items() if key != "dims"},
    ]:
        assert cls.from_snapshot(value).is_failed()
    other = MutableMultiArray if cls is MultiArray else MultiArray
    assert other.from_snapshot(valid).is_failed()
    restored = cls.from_snapshot({**valid, "dims": (), "values": [None]}).unwrap()
    assert restored.at(()).unwrap() is None


def test_pending_native_restore_is_one_shot_and_never_publishes_short_state() -> None:
    for factory in [_native._unpickle_multiarray, _native._unpickle_mutable_multiarray]:
        pending = factory((1, [2], True))
        assert pending.at([0])[1].category == "FAILED_PRECONDITION"
        for invalid in [[], [1], [1, 2, 3], (1, 2)]:
            with pytest.raises(ValueError):
                pending.__setstate__(invalid)
            assert pending.flatten(False)[1].category == "FAILED_PRECONDITION"
        pending.__setstate__([None, 2])
        assert pending.flatten(False) == ([None, 2], None)
        with pytest.raises(ValueError, match="finalized"):
            pending.__setstate__([3, 4])
        assert pending.flatten(False) == ([None, 2], None)


@pytest.mark.parametrize(
    "factory",
    [
        _native._unpickle_shape,
        _native._unpickle_multiarray,
        _native._unpickle_mutable_multiarray,
    ],
)
def test_pickle_constructor_rejects_bad_version_and_shape(factory: Any) -> None:
    for metadata in [(2, [2], False), (1, [0], False), (1, [sys.maxsize, 2], False)]:
        with pytest.raises(ValueError):
            factory(metadata)
    with pytest.raises(ValueError):
        _native._unpickle_multiarray_view((1, [3], False, [2], [2]))


def test_unpicklable_leaf_or_callback_uses_standard_protocol_failure_not_snapshot_failure() -> (
    None
):
    leaf = _Unpicklable()
    source = MultiArray.full(shape=DynShape((2,)), value=leaf).unwrap()
    assert source.to_snapshot().unwrap()["values"] == [leaf, leaf]
    with pytest.raises(ValueError, match="External leaf"):
        pickle.dumps(source)
    assert source.at((0,)).unwrap() is leaf
    mapped = MappedMultiArrayView.create(
        source=MultiArray.ones(shape=DynShape((2,))).unwrap(),
        callback=lambda value: value,
    ).unwrap()
    with pytest.raises((AttributeError, pickle.PicklingError)):
        pickle.dumps(mapped)


def test_concurrent_pickle_and_checked_snapshots_observe_complete_batch_versions() -> (
    None
):
    source = MutableMultiArray.zeros(shape=DynShape((2, 4))).unwrap()
    indices = list(itertools.product(range(2), range(4)))

    def operation(index: int) -> None:
        source.set_many([(position, index) for position in indices]).unwrap()
        snapshot = source.to_snapshot().unwrap()["values"]
        assert all(item == snapshot[0] for item in snapshot)
        restored = pickle.loads(pickle.dumps(source))
        values = restored.flatten().unwrap()
        assert all(item == values[0] for item in values)

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(operation, range(120)))


def test_restore_result_preserves_existing_result_family_and_input_leaf_identity() -> (
    None
):
    original = Failed(Err(ErrorCode.NOT_FOUND, "data"))
    source = MultiArray.full(shape=DynShape((2,)), value=original).unwrap()
    restored = MultiArray.from_snapshot(source.to_snapshot().unwrap()).unwrap()
    assert restored.at((0,)).unwrap() is original


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_shape_protocol_roundtrip_and_immutable_view_source_aliases(
    order: StorageOrder, protocol: int
) -> None:
    shape = Shape.create(dims=(3, 4), storage_order=order).unwrap()
    restored_shape = pickle.loads(pickle.dumps(shape, protocol=protocol))
    assert restored_shape.dims == shape.dims
    assert restored_shape.strides() == shape.strides()
    assert (
        copy.deepcopy(shape).index_of((2, 3)).unwrap()
        == shape.index_of((2, 3)).unwrap()
    )
    source = MultiArray.create(values=list(range(12)), shape=shape).unwrap()
    view = source.view(offsets=(1, 1), shape=DynShape((2, 3), order)).unwrap()
    restored_source, restored_view = pickle.loads(
        pickle.dumps((source, view), protocol=protocol)
    )
    assert restored_view._source is restored_source
    assert restored_view.to_list().unwrap() == [[5, 6, 7], [9, 10, 11]]


def test_restore_leaf_can_reenter_pending_native_storage_without_publishing_partial_values() -> (
    None
):
    leaf = _RestoreReader()
    source = MultiArray.full(shape=DynShape((2,)), value=leaf).unwrap()
    leaf.owner = source._handle
    restored = pickle.loads(pickle.dumps(source))
    new_leaf = restored.at((0,)).unwrap()
    assert new_leaf.observed == "FAILED_PRECONDITION"
    assert new_leaf.owner is restored._handle
    assert new_leaf.owner.at([1])[0] is new_leaf
