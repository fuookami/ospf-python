"""公开数组权威状态的替换基线，不认证原生切换 / Public authoritative-state baseline, not native cutover acceptance."""

from __future__ import annotations

import copy
import pickle
from typing import Any, cast

import numpy as np
import pytest

from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.multi_array_view import MappedMultiArrayView, MultiArrayView
from ospf_python.multiarray.shape import DynShape, Shape1, Shape2, StorageOrder
from ospf_python.utils.functional.result import Failed

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]
_RESTORERS = ["deepcopy", *range(pickle.HIGHEST_PROTOCOL + 1)]
_GRAPH_RESTORERS = [
    pytest.param(
        "deepcopy",
        False,
        marks=pytest.mark.xfail(
            strict=True,
            reason=(
                "AS-001 residual: when the buffer precedes the holder in the copied graph, "
                "ndarray.__deepcopy__ re-enters the holder before registering the buffer, so the "
                "holder cannot observe the in-flight copy. The leaf-first order is fixed."
            ),
        ),
    ),
    ("deepcopy", True),
    *[
        (protocol, leaf_first)
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1)
        for leaf_first in (False, True)
    ],
]


class _Payload:
    owner: Any
    peer: Any


class _SlottedArray(MultiArray[Any, Any]):
    __slots__ = ("__private", "label")
    extra: dict[str, Any]

    def attach(self, value: Any) -> None:
        self.__private = value
        self.label = value

    def attached(self) -> Any:
        return self.__private


def _identity(value: Any) -> Any:
    return value


def _restore(value: Any, mode: str | int) -> Any:
    if mode == "deepcopy":
        return copy.deepcopy(value)
    assert isinstance(mode, int)
    return pickle.loads(pickle.dumps(value, protocol=mode))


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_shallow_facade_rebinding_is_independent_but_storage_is_shared(
    *, cls: type[Any], order: StorageOrder
) -> None:
    shape = Shape2(2, 3, order)
    data = np.arange(6)
    original = cls(shape, data)
    shallow = copy.copy(original)
    assert shallow is not original
    assert shallow.shape is original.shape is shape
    assert shallow._data is original._data is data
    data[0] = 31
    assert shallow.get(0, 0) == original.get(0, 0) == 31

    replacement_shape = Shape2(3, 2, order)
    replacement_data = np.arange(6) + 100
    shallow._shape = replacement_shape
    shallow._data = replacement_data
    assert shallow.shape is replacement_shape and shallow._data is replacement_data
    assert original.shape is shape and original._data is data
    assert original.get(0, 0) == 31 and shallow.get(0, 0) == 100


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_views_and_suspended_iteration_resolve_replaced_authority(
    *, cls: type[Any], order: StorageOrder
) -> None:
    source = cls(Shape2(2, 3, order), np.arange(6))
    view = MultiArrayView(source)
    mapped = MappedMultiArrayView(view, f=_identity)
    cursor = iter(source)
    assert next(cursor) == 0
    replacement_shape = Shape2(3, 2, order)
    replacement_data = np.arange(6) + 100
    source._shape = replacement_shape
    source._data = replacement_data
    assert view.shape is mapped.shape is replacement_shape
    assert view.get(2, 1) == mapped.get(2, 1) == 105
    assert source.at(indices=(2, 1)).unwrap() == 105
    assert list(cursor) == [101, 102, 103, 104, 105]
    replacement_data[-1] = 99
    assert view.get(2, 1) == mapped.get(2, 1) == 99


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize(("mode", "leaf_first"), _GRAPH_RESTORERS)
def test_restore_preserves_whole_array_view_buffer_and_leaf_alias_graph(
    *, cls: type[Any], order: StorageOrder, mode: str | int, leaf_first: bool
) -> None:
    leaf = _Payload()
    shape = Shape2(2, 3, order)
    data = np.empty(6, dtype=object)
    data[:] = [leaf, leaf, 2, 3, 4, 5]
    first = cls(shape, data)
    second: MutableMultiArray[Any, Shape2] = MutableMultiArray(shape, data)
    leaf.owner, leaf.peer = first, second
    view = MultiArrayView(first)
    mapped = MappedMultiArrayView(view, f=_identity)
    graph = [shape, data, first, second, view, mapped, leaf]
    restored = _restore(graph[::-1] if leaf_first else graph, mode)
    if leaf_first:
        restored.reverse()
    new_shape, new_data, left, right, new_view, new_mapped, new_leaf = restored
    assert type(left) is cls and type(right) is MutableMultiArray
    assert left.shape is right.shape is new_shape
    assert left._data is right._data is new_data
    assert new_data is not data and not np.shares_memory(new_data, data)
    assert new_view._source is left and new_mapped._source is new_view
    assert new_mapped._f is _identity
    assert new_leaf is not leaf
    assert new_data[0] is new_data[1] is new_leaf
    assert new_leaf.owner is left and new_leaf.peer is right
    assert new_mapped.get(0, 0) is new_leaf
    right[1, 2] = 87
    assert left.get(1, 2) == new_view.get(1, 2) == new_mapped.get(1, 2) == 87
    assert data[-1] == 5


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("mode", _RESTORERS)
def test_legacy_field_only_graph_restores_without_calling_constructor(
    *, cls: type[Any], mode: str | int, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = object.__new__(cls)
    data = np.array([2, 3])
    shape = Shape1(2)
    source.__dict__.update(_shape=shape, _data=data)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("恢复不得重新调用构造器 / Restoration must not rerun constructors")

    monkeypatch.setattr(cls, "__init__", forbidden)
    restored, restored_data, restored_shape = _restore([source, data, shape], mode)
    assert type(restored) is cls
    assert restored._data is restored_data and restored.shape is restored_shape
    assert restored.get(1) == restored.at(indices=(1,)).unwrap() == 3


@pytest.mark.parametrize("mode", ["deepcopy", 2, 3, 4, 5])
def test_restore_preserves_subclass_dict_slots_private_slots_and_back_edges(
    mode: str | int,
) -> None:
    leaf = _Payload()
    source = _SlottedArray(Shape1(1), np.array([leaf], dtype=object))
    source.attach(leaf)
    source.extra = {"leaf": leaf}
    leaf.owner, leaf.peer = source, source
    restored = _restore(source, mode)
    assert type(restored) is _SlottedArray
    new_leaf = restored.get(0)
    assert restored.attached() is restored.label is restored.extra["leaf"] is new_leaf
    assert new_leaf.owner is new_leaf.peer is restored
    assert new_leaf is not leaf


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.filterwarnings(
    "ignore:Setting the (dtype|shape) on a NumPy array has been deprecated:DeprecationWarning"
)
def test_external_dtype_and_rank_mutations_invalidate_then_recover_checked_access(
    cls: type[Any],
) -> None:
    data = np.array([-1, 2, 3, 4], dtype=np.int32)
    source = cls(Shape1(4), data)
    cast("Any", data).dtype = np.uint32
    assert source.get(0) == source.at(indices=(0,)).unwrap() == 2**32 - 1
    assert source._data is data and type(source.get(0)) is int
    data.shape = (2, 2)
    assert isinstance(source.at(indices=(0,)), Failed)
    assert source._data is data and data.shape == (2, 2)
    data.shape = (4,)
    assert source.at(indices=(3,)).unwrap() == 4
    cast("Any", data).dtype = np.uint16
    assert isinstance(source.at(indices=(0,)), Failed)
    assert data.size == 8 and source._data is data
    source._shape = Shape1(8)
    assert source.at(indices=(7,)).unwrap() == int(data[7])


def test_external_write_permission_applies_to_all_aliases_without_detaching() -> None:
    data = np.arange(3)
    first: MutableMultiArray[int, Shape1] = MutableMultiArray(Shape1(3), data)
    second = copy.copy(first)
    data.flags.writeable = False
    for source in (first, second):
        result = source.set_at(indices=(0,), value=90)
        assert isinstance(result, Failed)
        assert isinstance(result.error.value.callback_exception, ValueError)
        assert source._data is data
        assert source.at(indices=(0,)).unwrap() == 0
    data.flags.writeable = True
    second.set_at(indices=(0,), value=90).unwrap()
    assert first.get(0) == data[0] == 90


@pytest.mark.parametrize("cls", _TYPES)
def test_sparse_shape_rebinding_does_not_allocate_or_normalize_storage(
    cls: type[Any],
) -> None:
    data = np.array([5])
    source = cls(Shape1(1), data)
    sparse = DynShape((2**128, 3))
    source._shape = sparse
    assert source.shape is sparse and source.size == 3 * 2**128
    assert source._data is data
    assert isinstance(source.at(indices=(0, 0)), Failed)
    source._shape = Shape1(1)
    assert source.at(indices=(0,)).unwrap() == 5
