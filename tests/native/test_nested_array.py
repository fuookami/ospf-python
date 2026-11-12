"""原生嵌套输入、叶身份及形状边界 / Native nested input, leaf identity and shape boundaries."""

from __future__ import annotations

import gc
import itertools
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.multiarray import MultiArray, MutableMultiArray, Shape
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


class _Payload:
    owner: Any = None


class _Hostile:
    def __iter__(self) -> Any:
        raise AssertionError("不得迭代叶 / Must not iterate leaves")

    def __len__(self) -> int:
        raise AssertionError("不得测量叶 / Must not measure leaves")

    def __array__(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("不得转换叶 / Must not coerce leaves")

    def item(self) -> Any:
        raise AssertionError("不得调用叶 item / Must not call leaf item")


class _List(list[Any]):
    def __iter__(self) -> Any:
        raise AssertionError("不得调用子类迭代 / Must not invoke subclass iteration")

    def __len__(self) -> int:
        raise AssertionError("不得调用子类长度 / Must not invoke subclass length")

    def __getitem__(self, index: Any) -> Any:
        raise AssertionError("不得调用子类取项 / Must not invoke subclass indexing")


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (3,), (2, 3), (2, 1, 3)])
@pytest.mark.parametrize("tuples", [False, True])
def test_nested_structure_represents_logical_coordinates_for_both_storage_layouts(
    *, cls: type[Any], order: StorageOrder, dims: tuple[int, ...], tuples: bool
) -> None:
    oracle = np.arange(np.prod(dims, dtype=int)).reshape(dims)
    data = oracle.tolist()
    if tuples:

        def convert(value: Any) -> Any:
            return (
                tuple(convert(item) for item in value) if type(value) is list else value
            )

        data = convert(data)
    shape = DynShape(dims, order)
    array = cls.from_list(data=data, shape=shape).unwrap()
    assert array.shape.dims == dims and array.shape.storage_order is order
    assert array.to_list().unwrap() == oracle.tolist()
    for indices in itertools.product(*(range(dim) for dim in dims)):
        assert array.at(indices).unwrap() == oracle[indices]
        assert type(array.at(indices).unwrap()) is int
    expected = list(
        oracle.ravel(order="F" if order is StorageOrder.COLUMN_MAJOR else "C")
    )
    assert array.flatten(access_order=order).unwrap() == expected


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_depth_defines_opaque_leaves_without_numpy_dtype_or_sequence_inference(
    *, cls: type[Any], order: StorageOrder
) -> None:
    failure = Failed(Err(ErrorCode.APPLICATION_ERROR, "opaque-result"))
    leaves = [
        None,
        [1, 2],
        (3, 4),
        np.arange(3),
        _List([7]),
        _Hostile(),
        Fraction(1, 3),
        Decimal("0.125"),
        np.int16(12),
        np.float32(0.25),
        np.datetime64("2026-10-25"),
        failure,
        Ok(1),
    ]
    data = [leaves, tuple(leaves)]
    array = cls.from_list(data=data, shape=DynShape((2, len(leaves)), order)).unwrap()
    for row in range(2):
        for index, leaf in enumerate(leaves):
            assert array.at((row, index)).unwrap() is leaf
    rebuilt = cls.from_list(data=array.to_list().unwrap(), shape=array.shape).unwrap()
    assert rebuilt.at((1, 3)).unwrap() is leaves[3]
    assert rebuilt.at((0, 11)).unwrap() is failure


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "leaf", [None, [1, 2], (1, 2), np.arange(3), _List([1]), _Hostile()]
)
def test_scalar_shape_keeps_the_entire_root_as_one_opaque_leaf(
    *, cls: type[Any], leaf: Any
) -> None:
    array = cls.from_list(data=leaf, shape=DynShape(())).unwrap()
    assert array.at(()).unwrap() is leaf
    assert array.to_list().unwrap() is leaf


@pytest.mark.parametrize("cls", _TYPES)
def test_container_structure_is_detached_but_repeated_leaves_are_not_copied(
    cls: type[Any],
) -> None:
    leaf = _Payload()
    row = [leaf, leaf]
    data = [row, tuple(row)]
    before = sys.getrefcount(leaf)
    row_before = sys.getrefcount(row)
    data_before = sys.getrefcount(data)
    array = cls.from_list(data=data, shape=DynShape((2, 2))).unwrap()
    assert sys.getrefcount(leaf) == before + 4
    assert sys.getrefcount(row) == row_before
    assert sys.getrefcount(data) == data_before
    row[:] = [None, None]
    data[:] = []
    assert all(item is leaf for item in array.flatten().unwrap())
    if cls is MutableMultiArray:
        array.set(indices=(0, 0), value="different-domain").unwrap()
        assert array.at((0, 0)).unwrap() == "different-domain"
        assert row == [None, None]


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "data,dims",
    [
        ([], (1,)),
        (1, (1,)),
        ("text", (4,)),
        ([1], (2,)),
        ([1, 2, 3, 4], (2, 2)),
        ([[1, 2], [3]], (2, 2)),
        ([[1, 2, 3], [4]], (2, 2)),
        ([1, 2], (2, 1)),
        ([[1, 2], [3, 4]], (4,)),
        (np.ones((2, 2)), (2, 2)),
        (_List([1, 2]), (2,)),
        ([_List([1]), [2]], (2, 1)),
        (_Hostile(), (1,)),
    ],
)
def test_structure_is_checked_per_axis_not_just_flat_element_count(
    *, cls: type[Any], data: object, dims: tuple[int, ...]
) -> None:
    result = cls.from_list(data=data, shape=DynShape(dims))
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize("cls", _TYPES)
def test_cycles_are_shape_bounded_and_output_edges_are_gc_visible(
    cls: type[Any],
) -> None:
    structural: list[Any] = []
    structural.append(structural)
    array = cls.from_list(data=structural, shape=DynShape((1, 1))).unwrap()
    assert array.at((0, 0)).unwrap() is structural
    leaf = _Payload()
    cyclic = cls.from_list(data=[[leaf, leaf]], shape=DynShape((1, 2))).unwrap()
    leaf.owner = cyclic
    reference = weakref.ref(leaf)
    del cyclic, leaf
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("cls", _TYPES)
def test_late_validation_failure_does_not_retain_temporary_leaves(
    cls: type[Any],
) -> None:
    leaf = _Payload()
    reference = weakref.ref(leaf)
    data = [[leaf, leaf], [leaf]]
    before = sys.getrefcount(leaf)
    result = cls.from_list(data=data, shape=DynShape((2, 2)))
    assert isinstance(result, Failed)
    assert sys.getrefcount(leaf) == before
    del data, leaf
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("cls", _TYPES)
def test_deep_rank_uses_no_python_or_rust_recursive_descent(cls: type[Any]) -> None:
    leaf = _Hostile()
    data: Any = leaf
    rank = 2500
    for _ in range(rank):
        data = (data,)
    array = cls.from_list(data=data, shape=DynShape((1,) * rank)).unwrap()
    assert array.at((0,) * rank).unwrap() is leaf
    nested = array.to_list().unwrap()
    rebuilt = cls.from_list(data=nested, shape=array.shape).unwrap()
    assert rebuilt.at((0,) * rank).unwrap() is leaf


@pytest.mark.parametrize("cls", _TYPES)
def test_reference_capacity_overflow_is_rejected_before_allocation(
    cls: type[Any],
) -> None:
    result = cls.from_list(data=[], shape=Shape.create(dims=(sys.maxsize,)).unwrap())
    assert isinstance(result, Failed) and result.error.code is ErrorCode.OVERFLOW


@pytest.mark.parametrize(
    "creator",
    [_native._multiarray_from_nested, _native._mutable_multiarray_from_nested],
)
def test_direct_transport_rejects_structure_with_failure_data(creator: Any) -> None:
    shape = Shape.create(dims=(2, 2)).unwrap()._handle
    value, failure = creator(data=[[1, 2], [3]], shape=shape)
    assert value is None and failure.category == "ILLEGAL_ARGUMENT"


@pytest.mark.parametrize("cls", _TYPES)
def test_independent_concurrent_imports_do_not_share_slots(cls: type[Any]) -> None:
    data = [[Fraction(1, 3), Fraction(2, 3)]]

    def create(order: StorageOrder) -> Any:
        array = cls.from_list(data=data, shape=DynShape((1, 2), order)).unwrap()
        assert array.reduce(lambda a, b: a + b).unwrap() == 1
        return array

    with ThreadPoolExecutor(max_workers=4) as pool:
        arrays = list(pool.map(create, _ORDERS * 40))
    assert len({id(array._handle) for array in arrays}) == len(arrays)
    assert all(array.at((0, 1)).unwrap() is data[0][1] for array in arrays)


@pytest.mark.parametrize("cls", _TYPES)
def test_classmethod_preserves_requested_facade_subclass(cls: type[Any]) -> None:
    class Extended(cls):
        pass

    array = Extended.from_list(data=[[1]], shape=DynShape((1, 1))).unwrap()
    assert type(array) is Extended


@pytest.mark.parametrize("cls", _TYPES)
def test_nested_path_never_uses_numpy_construction(
    cls: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("不得调用 NumPy 构造 / Must not call NumPy construction")

    with monkeypatch.context() as context:
        for name in ("array", "asarray", "full"):
            context.setattr(np, name, forbidden)
        leaf = _Hostile()
        array = cls.from_list(data=[[leaf]], shape=DynShape((1, 1))).unwrap()
    assert array.at((0, 0)).unwrap() is leaf
