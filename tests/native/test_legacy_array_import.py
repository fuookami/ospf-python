"""旧字段的显式所有权迁移合同 / Explicit ownership migration for legacy array fields."""

from __future__ import annotations

import gc
import itertools
import pickle
import weakref
from typing import Any

import numpy as np
import pytest

from ospf_python._binding.multiarray import MultiArray, MutableMultiArray
from ospf_python.multiarray.multi_array import MultiArray as LegacyArray
from ospf_python.multiarray.multi_array import MutableMultiArray as LegacyMutableArray
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


class _Leaf:
    def item(self) -> Any:
        raise AssertionError("不得执行叶转换 / Leaf conversion must not run")


class _Shape(DynShape):
    def flat_index(self, *indices: int) -> int:
        raise AssertionError("不得调用旧索引 / Legacy indexing must not run")


class _Extended(MultiArray[Any]):
    pass


class _ExtendedMutable(MutableMultiArray[Any]):
    pass


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (2, 3), (2, 1, 3)])
@pytest.mark.parametrize("strided", [False, True])
def test_import_uses_legacy_physical_order_without_reinterpreting_as_logical_input(
    *, cls: type[Any], order: StorageOrder, dims: tuple[int, ...], strided: bool
) -> None:
    shape = DynShape(dims, order)
    backing = np.arange(shape.size * 2, dtype=np.int16)
    data = backing[::-2] if strided else backing[: shape.size]
    legacy = LegacyArray(shape, data)
    array = cls.from_legacy_state(payload=vars(legacy), copy=True).unwrap()
    assert array.shape.dims == dims and array.shape.storage_order is order
    assert array.flatten(access_order=order).unwrap() == list(data)
    for indices in itertools.product(*(range(dim) for dim in dims)):
        actual = array.at(indices).unwrap()
        assert type(actual) is np.int16
        assert actual == legacy.get(*indices)
    backing[:] = -99
    assert all(value != -99 for value in array.flatten().unwrap())


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_public_pickle_remains_public_then_explicit_state_import_detaches_storage(
    *, cls: type[Any], order: StorageOrder, protocol: int
) -> None:
    legacy_type = LegacyArray if cls is MultiArray else LegacyMutableArray
    legacy = legacy_type(DynShape((2, 3), order), np.arange(6))
    restored = pickle.loads(pickle.dumps(legacy, protocol=protocol))
    assert type(restored) is legacy_type
    array = cls.from_legacy_state(payload=vars(restored), copy=True).unwrap()
    assert array.flatten(access_order=order).unwrap() == list(range(6))
    assert array.at((1, 2)).unwrap() == restored.get(1, 2)
    restored._data[:] = -1
    assert array.at((1, 2)).unwrap() == 5


@pytest.mark.parametrize("order", _ORDERS)
def test_readonly_shared_legacy_data_is_never_written_back(order: StorageOrder) -> None:
    data = np.arange(6, dtype=np.int64)
    data.flags.writeable = False
    payload = {"_shape": DynShape((2, 3), order), "_data": data}
    array = MutableMultiArray.from_legacy_state(payload=payload, copy=True).unwrap()
    assert array.set(indices=(1, 2), value=99).is_ok()
    assert data.tolist() == list(range(6))
    assert array.at((1, 2)).unwrap() == 99


@pytest.mark.parametrize("cls", _TYPES)
def test_import_preserves_opaque_leaf_identity_without_retaining_source_storage(
    cls: type[Any],
) -> None:
    leaf = _Leaf()
    data = np.empty(2, dtype=object)
    data[:] = [leaf, leaf]
    reference = weakref.ref(data)
    state = {"_shape": DynShape((2,)), "_data": data}
    array = cls.from_legacy_state(payload=state, copy=True).unwrap()
    del data, state
    gc.collect()
    assert reference() is None
    assert array.at((0,)).unwrap() is leaf
    assert array.at((1,)).unwrap() is leaf
    leaf.owner = array
    leaf_reference = weakref.ref(leaf)
    del leaf, array
    gc.collect()
    assert leaf_reference() is None


@pytest.mark.parametrize("cls", _TYPES)
def test_import_does_not_relocate_leaf_owner_or_silently_drop_subclass_state(
    cls: type[Any],
) -> None:
    leaf = _Leaf()
    data = np.empty(1, dtype=object)
    data[0] = leaf
    legacy = LegacyArray(DynShape((1,)), data)
    leaf.owner = legacy
    array = cls.from_legacy_state(payload=vars(legacy), copy=True).unwrap()
    assert array.at((0,)).unwrap().owner is legacy
    legacy.label = "extra-state"
    assert cls.from_legacy_state(payload=vars(legacy), copy=True).is_failed()
    # NumPy object 环不受 GC 管理；测试主动断开旧环。 / Break the old non-GC-tracked NumPy object cycle explicitly.
    del leaf.owner


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "dtype",
    [
        "bool",
        "int16",
        "uint64",
        "float32",
        "complex64",
        "U4",
        "S4",
        "datetime64[D]",
        "timedelta64[D]",
    ],
)
def test_scalar_types_survive_without_promising_persistent_dtype(
    *, cls: type[Any], dtype: str
) -> None:
    data = np.array([1, 0], dtype=dtype)
    payload = {"_shape": DynShape((2,)), "_data": data}
    array = cls.from_legacy_state(payload=payload, copy=True).unwrap()
    for index in range(2):
        assert type(array.at((index,)).unwrap()) is type(data[index])
        assert array.at((index,)).unwrap() == data[index]
    if cls is MutableMultiArray:
        leaf = _Leaf()
        assert array.set(indices=(0,), value=leaf).is_ok()
        assert array.at((0,)).unwrap() is leaf


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("copy", [False, None, 0, 1, "True"])
def test_explicit_copy_decision_is_required(*, cls: type[Any], copy: Any) -> None:
    result = cls.from_legacy_state(payload={}, copy=copy)
    assert isinstance(result, Failed)
    assert result.error.code is (
        ErrorCode.NOT_SUPPORTED if copy is False else ErrorCode.ILLEGAL_ARGUMENT
    )


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"_shape": DynShape((1,))},
        {"_shape": DynShape((1,)), "_data": [1]},
        {"_shape": DynShape((1,)), "_data": np.array(1)},
        {"_shape": DynShape((2, 3)), "_data": np.zeros((2, 3))},
        {"_shape": DynShape((2,)), "_data": np.array([1])},
        {"_shape": DynShape(()), "_data": np.array([])},
        {"_shape": object(), "_data": np.array([1])},
        {"_shape": DynShape((1,)), "_data": np.array([1]), "label": 1},
    ],
)
def test_invalid_state_is_rejected_without_partial_publication(
    *, cls: type[Any], payload: object
) -> None:
    assert cls.from_legacy_state(payload=payload, copy=True).is_failed()


@pytest.mark.parametrize("cls", _TYPES)
def test_custom_shape_requires_explicit_mapping_opt_in(cls: type[Any]) -> None:
    payload = {
        "_shape": _Shape((2, 3), StorageOrder.COLUMN_MAJOR),
        "_data": np.arange(6),
    }
    assert cls.from_legacy_state(payload=payload, copy=True).is_failed()
    assert (
        cls.from_legacy_state(payload=payload, copy=True, standard_layout=True)
        .unwrap()
        .at((1, 1))
        .unwrap()
        == 3
    )
    assert cls.from_legacy_state(
        payload=payload, copy=True, standard_layout=1
    ).is_failed()


@pytest.mark.parametrize("cls", _TYPES)
def test_array_and_mapping_subclass_protocols_are_not_invoked(cls: type[Any]) -> None:
    class Array(np.ndarray):
        def ravel(self, *args: Any, **kwargs: Any) -> Any:
            raise AssertionError(
                "数组子类协议不得调用 / Array subclass protocol must not run"
            )

    class State(dict[str, Any]):
        def __iter__(self) -> Any:
            raise AssertionError(
                "字典子类协议不得调用 / Dict subclass protocol must not run"
            )

    payload = {"_shape": DynShape((2,)), "_data": np.arange(2).view(Array)}
    assert cls.from_legacy_state(payload=payload, copy=True).is_failed()
    assert cls.from_legacy_state(payload=State(payload), copy=True).is_failed()


@pytest.mark.parametrize("cls", _TYPES)
def test_unsupported_dtype_is_explicit(cls: type[Any]) -> None:
    payload = {"_shape": DynShape((2,)), "_data": np.zeros(2, dtype=[("x", "i4")])}
    result = cls.from_legacy_state(payload=payload, copy=True)
    assert isinstance(result, Failed) and result.error.code is ErrorCode.NOT_SUPPORTED


@pytest.mark.parametrize("cls", [_Extended, _ExtendedMutable])
def test_import_preserves_requested_new_facade_class(cls: type[Any]) -> None:
    payload = {"_shape": DynShape((2,)), "_data": np.arange(2)}
    assert type(cls.from_legacy_state(payload=payload, copy=True).unwrap()) is cls
