"""剩余区域及旧视图显式导入合同 / Remaining regions and explicit legacy view import contracts."""

from __future__ import annotations

import copy
import gc
import itertools
import pickle
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
    MutableMultiArrayView,
    Shape,
)
from ospf_python.multiarray.multi_array import MultiArray as PublicArray
from ospf_python.multiarray.multi_array import MutableMultiArray as PublicMutableArray
from ospf_python.multiarray.multi_array_view import MultiArrayView as PublicView
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok

_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]
_ARRAYS = [MultiArray, MutableMultiArray]


class _Leaf:
    owner: object = None

    def item(self) -> Any:
        raise AssertionError("不得转换叶 / Do not convert leaves")

    def __iter__(self) -> Any:
        raise AssertionError("不得遍历叶 / Do not iterate leaves")


@pytest.mark.parametrize("cls", _ARRAYS)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize(
    ("dims", "offsets"),
    [((), ()), ((4,), (3,)), ((3, 4), (1, 2)), ((2, 1, 3), (1, 0, 1))],
)
def test_suffix_extent_uses_logical_coordinates_and_preserves_leaf_identity(
    *,
    cls: type[Any],
    order: StorageOrder,
    dims: tuple[int, ...],
    offsets: tuple[int, ...],
) -> None:
    shape = DynShape(dims, order)
    values = [_Leaf() for _ in range(shape.size)]
    source = cls.create(values=values, shape=shape).unwrap()
    view = source.view(offsets=offsets).unwrap()
    expected_dims = tuple(
        dim - offset for dim, offset in zip(dims, offsets, strict=True)
    )
    assert view.shape.dims == expected_dims
    assert view.shape.storage_order is order
    assert view._source is source
    assert type(view) is (
        MultiArrayView if cls is MultiArray else MutableMultiArrayView
    )
    for indices in itertools.product(*(range(dim) for dim in expected_dims)):
        absolute = tuple(i + o for i, o in zip(indices, offsets, strict=True))
        leaf = source.at(absolute).unwrap()
        assert view.at(indices).unwrap() is leaf
        assert view.materialize().unwrap().at(indices).unwrap() is leaf
    assert source.view().unwrap().shape.dims == dims
    assert source.view(shape=shape).unwrap().shape.dims == dims
    assert view.view().unwrap().shape.dims == expected_dims
    assert view.view(offsets=(0,) * len(dims)).unwrap().shape.dims == expected_dims


@pytest.mark.parametrize("cls", _ARRAYS)
@pytest.mark.parametrize("order", _ORDERS)
def test_nested_omitted_extent_stays_inside_parent_and_composes_origin(
    *, cls: type[Any], order: StorageOrder
) -> None:
    source = cls.create(values=list(range(30)), shape=DynShape((5, 6), order)).unwrap()
    outer = source.view(offsets=(1, 1), shape=DynShape((3, 4), order)).unwrap()
    inner = outer.view(offsets=(1, 2)).unwrap()
    assert inner.shape.dims == (2, 2)
    assert inner._source is source
    assert inner.at((1, 1)).unwrap() == source.at((3, 4)).unwrap()
    assert inner.at((2, 0)).is_failed()
    assert outer.view(offsets=(3, 0)).is_failed()
    assert (
        inner.view(shape=DynShape((1, 1), order)).unwrap().at((0, 0)).unwrap()
        == source.at((2, 3)).unwrap()
    )
    if cls is MutableMultiArray:
        assert inner.set(indices=(0, 1), value=None).is_ok()
        assert source.at((2, 4)).unwrap() is None
        live = inner.iter_live().unwrap()
        assert next(live) == inner.flatten(access_order=order).unwrap()[0]
        live.close()


@pytest.mark.parametrize("cls", _ARRAYS)
@pytest.mark.parametrize(
    "offsets",
    [
        (),
        (0,),
        (0, 0, 0),
        (-1, 0),
        (3, 0),
        (0, 4),
        (10**100, 0),
        (True, 0),
        (0.0, 0),
        [0, 0],
        "00",
    ],
)
def test_invalid_suffix_metadata_returns_result_without_changing_source(
    cls: type[Any], offsets: Any
) -> None:
    source = cls.create(values=list(range(12)), shape=DynShape((3, 4))).unwrap()
    baseline = source.flatten().unwrap()
    for parent in (source, source.view().unwrap()):
        result = parent.view(offsets=offsets)
        assert isinstance(result, Failed)
        assert result.error.code in (ErrorCode.ILLEGAL_ARGUMENT, ErrorCode.OUT_OF_RANGE)
    assert source.flatten().unwrap() == baseline


def test_native_defaults_and_deep_rank_do_not_require_python_index_algorithms() -> None:
    shape = Shape.create(dims=(1,) * 2200).unwrap()
    region, failure = _native._create_multiarray_view(source_shape=shape._handle)
    assert failure is None and region is not None
    assert region.shape.size == 1
    nested, failure = region.subview()
    assert failure is None and nested is not None and nested.shape.size == 1
    source = MutableMultiArray.full(shape=shape, value=None).unwrap()
    view = source.view(offsets=(0,) * 2200).unwrap().view().unwrap()
    assert view.at((0,) * 2200).unwrap() is None
    assert view.shape.dims == (1,) * 2200


@pytest.mark.parametrize("public_type", [PublicArray, PublicMutableArray])
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("strided", [False, True])
def test_legacy_view_import_corrects_extent_and_offset_without_retaining_buffer(
    *, public_type: type[Any], order: StorageOrder, strided: bool
) -> None:
    backing = np.arange(24, dtype=np.int16)
    data = backing[::-2] if strided else backing[:12]
    source = public_type(DynShape((3, 4), order), data)
    old_view = PublicView(source, offsets=(1, 2))
    source_ref, data_ref, view_ref = (
        weakref.ref(source),
        weakref.ref(data),
        weakref.ref(old_view),
    )
    imported = MultiArrayView.from_legacy_state(
        payload=vars(old_view), copy=True
    ).unwrap()
    assert type(imported) is MultiArrayView and type(imported._source) is MultiArray
    assert imported.shape.dims == (2, 2)
    assert imported.shape.storage_order is order
    expected = np.array(data).reshape(
        (3, 4), order="C" if order is StorageOrder.ROW_MAJOR else "F"
    )[1:, 2:]
    assert imported.to_list().unwrap() == expected.tolist()
    leaf = imported.at((0, 0)).unwrap()
    assert type(leaf) is np.int16
    backing[:] = -1
    assert imported.at((0, 0)).unwrap() == leaf
    assert imported.materialize().unwrap().at((1, 1)).unwrap() == expected[1, 1]
    del source, old_view, data
    gc.collect()
    assert source_ref() is None and view_ref() is None and data_ref() is None


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
@pytest.mark.parametrize("order", _ORDERS)
def test_decoded_old_view_state_import_and_new_graph_roundtrip(
    protocol: int, order: StorageOrder
) -> None:
    source = PublicArray(DynShape((2, 3), order), np.arange(6))
    old = PublicView(source, offsets=(1, 1))
    restored = pickle.loads(pickle.dumps(old, protocol=protocol))
    assert type(restored) is PublicView
    view = MultiArrayView.from_legacy_state(payload=vars(restored), copy=True).unwrap()
    assert view.shape.dims == (1, 2)
    assert copy.copy(view)._source is view._source
    for cloned in (
        copy.deepcopy(view),
        pickle.loads(pickle.dumps(view, protocol=protocol)),
    ):
        assert cloned._source is not view._source
        assert cloned.shape.dims == (1, 2)
        assert cloned.to_list().unwrap() == view.to_list().unwrap()


@pytest.mark.parametrize("order", _ORDERS)
def test_legacy_import_never_calls_old_kernels_or_leaf_protocols(
    order: StorageOrder, monkeypatch: pytest.MonkeyPatch
) -> None:
    leaf = _Leaf()
    result_leaf = Ok(None)
    values = [leaf, None, result_leaf, leaf, leaf, leaf]
    data = np.empty(6, dtype=object)
    for i, value in enumerate(values):
        data[i] = value
    source = PublicArray(DynShape((2, 3), order), data)
    old = PublicView(source)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("不得调用旧内核 / Do not call legacy kernels")

    monkeypatch.setattr(PublicArray, "get", forbidden)
    monkeypatch.setattr(PublicView, "materialize", forbidden)
    monkeypatch.setattr(DynShape, "flat_index", forbidden)
    view = MultiArrayView.from_legacy_state(payload=vars(old), copy=True).unwrap()
    assert all(
        a is b
        for a, b in zip(view.flatten(access_order=order).unwrap(), values, strict=True)
    )
    # 显式导入不重定位叶上的旧源回边。 / Explicit import does not relocate a leaf's old-source backedge.
    leaf.owner = source
    assert view.flatten(access_order=order).unwrap()[0].owner is source


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "extra",
        "offset-list",
        "offset-none",
        "offset-bool",
        "offset-end",
        "rank",
        "source-object",
        "source-state",
        "source-subclass",
        "nested-view",
        "mapped-view",
        "source-extra",
        "source-count",
    ],
)
def test_legacy_view_rejects_unhandled_metadata_without_silent_loss(
    change: str,
) -> None:
    source = PublicArray(DynShape((2, 3)), np.arange(6))
    payload: dict[str, Any] = {"_source": source, "_offsets": (0, 0)}
    if change == "missing":
        del payload["_offsets"]
    elif change == "extra":
        payload["extra"] = 1
    elif change.startswith("offset-"):
        payload["_offsets"] = {
            "offset-list": [0, 0],
            "offset-none": None,
            "offset-bool": (True, 0),
            "offset-end": (2, 0),
        }[change]
    elif change == "rank":
        payload["_offsets"] = ()
    elif change == "source-object":
        payload["_source"] = object()
    elif change == "source-state":
        payload["_source"] = vars(source)
    elif change == "source-subclass":

        class Extended(PublicArray[Any, Any]):
            pass

        payload["_source"] = Extended(source.shape, source._data)
    elif change == "nested-view":
        payload["_source"] = PublicView(source)
    elif change == "mapped-view":
        payload["_source"] = PublicView(source).map(lambda value: value)
    elif change == "source-extra":
        source.extra = 1  # type: ignore[attr-defined]
    elif change == "source-count":
        source._data = np.arange(5)
    result = MultiArrayView.from_legacy_state(payload=payload, copy=True)
    assert isinstance(result, Failed)


@pytest.mark.parametrize("copy_value", [False, None, 1, "yes"])
def test_view_import_requires_explicit_copy_policy(copy_value: Any) -> None:
    result = MultiArrayView.from_legacy_state(payload={}, copy=copy_value)
    assert isinstance(result, Failed)
    assert result.error.code is (
        ErrorCode.NOT_SUPPORTED if copy_value is False else ErrorCode.ILLEGAL_ARGUMENT
    )


def test_scalar_and_custom_shape_require_explicit_standard_mapping() -> None:
    class Custom(DynShape):
        def flat_index(self, *indices: int) -> int:
            raise AssertionError("不得执行自定义映射 / Do not execute custom mapping")

    leaf = _Leaf()
    data = np.empty(1, dtype=object)
    data[0] = leaf
    source = PublicArray(Custom(()), data)
    payload = {"_source": source, "_offsets": ()}
    assert MultiArrayView.from_legacy_state(payload=payload, copy=True).is_failed()
    view = MultiArrayView.from_legacy_state(
        payload=payload, copy=True, standard_layout=True
    ).unwrap()
    assert view.shape.dims == () and view.at(()).unwrap() is leaf
    assert MultiArrayView.from_legacy_state(
        payload=payload, copy=True, standard_layout=1
    ).is_failed()  # type: ignore[arg-type]


def test_imported_source_cycles_are_gc_visible_and_concurrent_reads_share_no_cursor() -> (
    None
):
    def build_cycle() -> weakref.ReferenceType[Any]:
        leaf = _Leaf()
        data = np.empty(2, dtype=object)
        data[:] = leaf
        source = PublicArray(DynShape((2,)), data)
        view = MultiArrayView.from_legacy_state(
            payload={"_source": source, "_offsets": (1,)}, copy=True
        ).unwrap()
        leaf.owner = view
        with ThreadPoolExecutor(max_workers=8) as executor:
            assert all(
                item is leaf
                for item in executor.map(lambda _: view.at((0,)).unwrap(), range(80))
            )
        return weakref.ref(leaf)

    leaf_ref = build_cycle()
    gc.collect()
    assert leaf_ref() is None
