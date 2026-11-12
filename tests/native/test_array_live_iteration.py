"""非快照数组游标的顺序、生命周期与协议合同 / Non-snapshot cursor order, lifecycle and protocol contracts."""

from __future__ import annotations

import copy
import gc
import operator
import pickle
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
    MultiArrayIterator,
    MutableMultiArray,
)
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok

_KINDS = ["immutable", "mutable", "immutable-view", "mutable-view"]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


def _subject(
    *, kind: str, order: StorageOrder, data: Any, dims: tuple[int, ...]
) -> Any:
    cls = MutableMultiArray if kind.startswith("mutable") else MultiArray
    source = cls.from_list(data=data, shape=DynShape(dims, order)).unwrap()
    if kind.endswith("view"):
        return source.view(offsets=(0,) * len(dims), shape=source.shape).unwrap()
    return source


class _Leaf:
    owner: Any = None


class _TrackedArray(MultiArray[Any]):
    pass


class _Opaque:
    def item(self) -> Any:
        raise AssertionError("不得转换叶 / Must not convert leaves")

    def __iter__(self) -> Any:
        raise AssertionError("不得展开叶 / Must not expand leaves")

    def __bool__(self) -> bool:
        raise AssertionError("不得判断叶真值 / Must not truth-test leaves")


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("access", [None, *_ORDERS])
def test_default_physical_order_and_explicit_logical_orders(
    *, kind: str, order: StorageOrder, access: StorageOrder | None
) -> None:
    subject = _subject(kind=kind, order=order, data=[[0, 1, 2], [3, 4, 5]], dims=(2, 3))
    with pytest.raises(TypeError):
        iter(subject)
    cursor = subject.iter_live(access_order=access).unwrap()
    assert isinstance(cursor, MultiArrayIterator) and iter(cursor) is cursor
    expected = (
        [0, 1, 2, 3, 4, 5] if (access or order) is _ORDERS[0] else [0, 3, 1, 4, 2, 5]
    )
    for remaining, value in zip(range(6, 0, -1), expected, strict=True):
        assert operator.length_hint(cursor) == remaining
        assert next(cursor) == value
    assert operator.length_hint(cursor) == 0
    assert cursor.advance().unwrap() == (False, None)
    with pytest.raises(StopIteration):
        next(cursor)


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("access", [None, *_ORDERS])
def test_nested_offset_view_retains_rank_and_only_iterates_its_extent(
    order: StorageOrder, access: StorageOrder | None
) -> None:
    source = MutableMultiArray.from_list(
        data=[[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]], shape=DynShape((3, 4), order)
    ).unwrap()
    first = source.view(offsets=(1, 1), shape=DynShape((2, 3), order)).unwrap()
    view = first.view(offsets=(0, 1), shape=DynShape((2, 2), order)).unwrap()
    expected = [6, 7, 10, 11] if (access or order) is _ORDERS[0] else [6, 10, 7, 11]
    assert list(view.iter_live(access_order=access).unwrap()) == expected
    singleton = view.view(offsets=(0, 0), shape=DynShape((1, 2), order)).unwrap()
    assert list(singleton.iter_live().unwrap()) == [6, 7]


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize(
    "value",
    [
        None,
        np.int16(7),
        float("nan"),
        [1, 2],
        _Leaf(),
        _Opaque(),
        Ok(None),
        Failed(Err(ErrorCode.NOT_FOUND, "leaf")),
    ],
)
def test_scalar_leaf_identity_and_checked_none_vs_exhaustion(
    kind: str, value: Any
) -> None:
    subject = _subject(kind=kind, order=_ORDERS[1], data=value, dims=())
    cursor = subject.iter_live().unwrap()
    present, item = cursor.advance().unwrap()
    assert present is True and item is value
    assert cursor.advance().unwrap() == (False, None)
    assert cursor.advance().unwrap() == (False, None)


@pytest.mark.parametrize("kind", _KINDS)
def test_creation_and_advances_do_not_snapshot_or_cache_unread_leaves(
    kind: str,
) -> None:
    first, unread = _Leaf(), _Leaf()
    subject = _subject(kind=kind, order=_ORDERS[0], data=[first, unread], dims=(2,))
    count = sys.getrefcount(unread)
    cursor = subject.iter_live().unwrap()
    assert sys.getrefcount(unread) == count
    assert next(cursor) is first
    assert sys.getrefcount(unread) == count
    count_first = sys.getrefcount(first)
    returned = next(cursor)
    assert returned is unread
    assert sys.getrefcount(first) == count_first
    del returned
    assert sys.getrefcount(unread) == count


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("view", [False, True])
def test_later_writes_are_visible_but_snapshots_and_past_positions_do_not_change(
    order: StorageOrder, view: bool
) -> None:
    source = MutableMultiArray.from_list(
        data=[[0, 1], [2, 3]], shape=DynShape((2, 2), order)
    ).unwrap()
    subject = (
        source.view(offsets=(0, 0), shape=source.shape).unwrap() if view else source
    )
    live = subject.iter_live(access_order=_ORDERS[0]).unwrap()
    snapshot = subject.iter_snapshot().unwrap()
    source.set(indices=(0, 0), value=10).unwrap()
    assert next(live) == 10
    source.set_many([((0, 0), 20), ((0, 1), 11), ((1, 0), 12)]).unwrap()
    assert list(live) == [11, 12, 3]
    assert list(snapshot) == [0, 1, 2, 3]


def test_next_and_checked_advance_share_exactly_one_native_position() -> None:
    source = MultiArray.from_list(data=[0, None, 2, 3], shape=DynShape((4,))).unwrap()
    cursor = source.iter_live().unwrap()
    assert next(cursor) == 0
    assert cursor.advance().unwrap() == (True, None)
    assert next(cursor._handle) == 2
    assert cursor.advance().unwrap() == (True, 3)
    assert next(cursor, "done") == "done"
    assert cursor.advance().unwrap() == (False, None)


@pytest.mark.parametrize("mode", ["last-value", "close", "abandon"])
def test_live_cursor_keeps_facade_alive_and_releases_it_without_extra_next(
    mode: str,
) -> None:
    source = _TrackedArray.from_list(data=[1], shape=DynShape((1,))).unwrap()
    reference = weakref.ref(source)
    cursor = source.iter_live().unwrap()
    del source
    gc.collect()
    assert reference() is not None
    if mode == "last-value":
        assert next(cursor) == 1
    elif mode == "close":
        assert cursor.close() is None and cursor.close() is None
    else:
        del cursor
    gc.collect()
    assert reference() is None


def test_view_cursor_retains_source_facade_even_after_view_variable_is_released() -> (
    None
):
    source = _TrackedArray.from_list(data=[0, 1, 2], shape=DynShape((3,))).unwrap()
    reference = weakref.ref(source)
    view = source.view(offsets=(1,), shape=DynShape((2,))).unwrap()
    cursor = view.iter_live().unwrap()
    del source, view
    gc.collect()
    assert reference() is not None and next(cursor) == 1
    assert next(cursor) == 2
    gc.collect()
    assert reference() is None and list(cursor) == []


@pytest.mark.parametrize("kind", _KINDS)
def test_gc_visits_cursor_owner_edges_and_reclaims_cycles(kind: str) -> None:
    def operation() -> Any:
        leaf = _Leaf()
        subject = _subject(kind=kind, order=_ORDERS[0], data=[leaf, leaf], dims=(2,))
        cursor = subject.iter_live().unwrap()
        leaf.owner = cursor
        return weakref.ref(leaf)

    leaf = operation()
    gc.collect()
    assert leaf() is None


def test_reachable_cursor_cycle_is_not_prematurely_cleared() -> None:
    leaf = _Leaf()
    source = MultiArray.from_list(data=[leaf, leaf], shape=DynShape((2,))).unwrap()
    cursor = source.iter_live().unwrap()
    leaf.owner = cursor
    reference = weakref.ref(leaf)
    del source, leaf
    gc.collect()
    returned = next(cursor)
    assert returned is reference()
    del returned
    assert next(cursor) is reference()
    gc.collect()
    assert reference() is None


def test_raw_gc_edges_include_both_real_strong_references_even_when_identical() -> None:
    leaf = _Leaf()
    source = MultiArray.from_list(data=[leaf], shape=DynShape((1,))).unwrap()
    value, error = _native._create_reference_iterator(
        source=source._handle, owner=source._handle
    )
    assert error is None
    assert sum(item is source._handle for item in gc.get_referents(value)) == 2
    value.close()
    assert all(item is type(value) for item in gc.get_referents(value))


def test_native_cursor_concurrent_consumers_never_duplicate_or_lose_positions() -> None:
    subject = MultiArray.from_list(
        data=list(range(2000)), shape=DynShape((2000,))
    ).unwrap()
    cursor = subject.iter_live().unwrap()

    def consume(_: int) -> list[int]:
        output = []
        while True:
            present, value = cursor.advance().unwrap()
            if not present:
                return output
            output.append(value)

    with ThreadPoolExecutor(max_workers=8) as pool:
        values = [value for group in pool.map(consume, range(8)) for value in group]
    assert sorted(values) == list(range(2000))
    assert operator.length_hint(cursor) == 0


@pytest.mark.parametrize("order", _ORDERS)
def test_cross_thread_writes_are_visible_to_next_advance(order: StorageOrder) -> None:
    subject = MutableMultiArray.from_list(
        data=[[0, 1], [2, 3]], shape=DynShape((2, 2), order)
    ).unwrap()
    cursor = subject.iter_live(access_order=_ORDERS[0]).unwrap()
    assert next(cursor) == 0
    with ThreadPoolExecutor(max_workers=1) as pool:
        assert (
            pool.submit(subject.set_many, [((0, 1), 9), ((1, 0), 8)])
            .result(timeout=5)
            .is_ok()
        )
    assert list(cursor) == [9, 8, 3]


def test_shallow_copy_aliases_position_and_close_while_pickle_and_deepcopy_are_explicitly_unsupported() -> (
    None
):
    subject = MultiArray.from_list(data=[0, 1, 2], shape=DynShape((3,))).unwrap()
    cursor = subject.iter_live().unwrap()
    alias = copy.copy(cursor)
    assert alias is not cursor and alias._handle is cursor._handle
    assert next(alias) == 0 and cursor.advance().unwrap() == (True, 1)
    with pytest.raises(TypeError):
        copy.deepcopy(cursor)
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        with pytest.raises(TypeError):
            pickle.dumps(cursor, protocol=protocol)
    assert operator.length_hint(cursor) == 1
    alias.close()
    assert cursor.advance().unwrap() == (False, None)


@pytest.mark.parametrize("value", [True, 0, "ROW_MAJOR", [], object()])
def test_invalid_access_order_is_rejected_at_creation(value: Any) -> None:
    source = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    result = source.iter_live(access_order=value)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )


@pytest.mark.parametrize("mutable", [False, True])
def test_pending_source_cannot_publish_a_live_cursor(mutable: bool) -> None:
    if mutable:
        source = MutableMultiArray(
            _native._unpickle_mutable_multiarray((1, [2], False))
        )
    else:
        source = MultiArray(_native._unpickle_multiarray((1, [2], False)))
    result = source.iter_live()
    assert (
        isinstance(result, Failed)
        and result.error.code is ErrorCode.FAILED_PRECONDITION
    )


def test_raw_factory_validates_foreign_region_and_source_kind() -> None:
    source = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    foreign = (
        MultiArray.from_list(data=[0, 1], shape=DynShape((2,)))
        .unwrap()
        .view(offsets=(0,), shape=DynShape((1,)))
        .unwrap()
    )
    value, error = _native._create_reference_iterator(
        source=source._handle, owner=source, region=foreign._handle
    )
    assert value is None and error.category == "ILLEGAL_ARGUMENT"
    value, error = _native._create_reference_iterator(source=None, owner=None)
    assert value is None and error.category == "ILLEGAL_ARGUMENT"
    with pytest.raises(TypeError):
        _native.MultiArrayIterator()


@pytest.mark.parametrize("kind", _KINDS)
def test_high_rank_cursor_uses_upstream_coordinates_without_python_recursion(
    kind: str,
) -> None:
    leaf = _Leaf()
    cls = MutableMultiArray if kind.startswith("mutable") else MultiArray
    subject = cls.full(shape=DynShape((1,) * 2200, _ORDERS[0]), value=leaf).unwrap()
    if kind.endswith("view"):
        subject = subject.view(offsets=(0,) * 2200, shape=subject.shape).unwrap()
    cursor = subject.iter_live(access_order=_ORDERS[1]).unwrap()
    assert next(cursor) is leaf and cursor.advance().unwrap() == (False, None)


@pytest.mark.parametrize("mode", ["close", "last-value"])
def test_source_destructor_can_reenter_or_wait_for_another_thread(mode: str) -> None:
    code = """
import os
import threading
directories = [os.add_dll_directory(path) for path in
    os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path] if os.name == 'nt' else []
from ospf_python._binding.multiarray import MultiArray
from ospf_python.multiarray.shape import DynShape
events = []
class Source(MultiArray):
    def __del__(self):
        assert cursor.advance().unwrap() == (False, None)
        thread = threading.Thread(target=lambda: events.append(cursor.advance().unwrap()))
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
source = Source.from_list(data=[0], shape=DynShape((1,))).unwrap()
cursor = source.iter_live().unwrap()
del source
if MODE == 'close':
    cursor.close()
else:
    assert next(cursor) == 0
assert events == [(False, None)], events
assert cursor.advance().unwrap() == (False, None)
""".replace("MODE", repr(mode))
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
