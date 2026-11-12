"""公共批量共享读取与旧字段实际消费合同 / Public batch shared reads and actual legacy-state consumer contracts."""

from __future__ import annotations

import gc
import sys
import weakref
from typing import Any, get_type_hints

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding import multiarray as binding
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape, Shape1, Shape2, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


def _objects(values: list[Any]) -> np.ndarray:
    data = np.empty(len(values), dtype=object)
    for index, value in enumerate(values):
        data[index] = value
    return data


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("stride", [1, -2, 0])
def test_requested_order_duplicates_and_shared_strided_data(
    *, cls: type[Any], order: StorageOrder, stride: int
) -> None:
    backing = np.arange(12, dtype=np.int16)
    data = np.broadcast_to(backing[:1], (6,)) if stride == 0 else backing[::stride][:6]
    source = cls(Shape2(2, 3, order), data)
    indices = [(1, 2), (0, 1), (1, 0), (0, 1)]
    expected = [source.get(*coordinate) for coordinate in indices]
    result = source.at_many(indices=indices).unwrap()
    assert result == expected and all(type(value) is int for value in result)
    if stride:
        data[-1] = 42
        assert source.at_many(indices=indices).unwrap()[0] == 42
    source._data = np.arange(6) + 100
    assert source.at_many(indices=[(1, 2)]).unwrap() == [105]
    assert result == expected
    assert source.at_many(indices=[]).unwrap() == []


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "bad",
    [
        [(0,)],
        [(0, 0), (0, 3)],
        [(0, 0), (-1, 1)],
        [(0, 0), (True, 1)],
        [(0, 0), [0, 0]],
        [(0, 0), (2**200, 0)],
    ],
)
def test_entire_coordinate_batch_fails_before_any_external_storage_access(
    cls: type[Any], bad: Any
) -> None:
    class Source(cls):
        def __getattribute__(self, name: str) -> Any:
            if name == "_data":
                raise AssertionError(
                    "整批校验前不得读取 / Do not read before full batch validation"
                )
            return super().__getattribute__(name)

    source = Source(Shape2(2, 3), np.arange(6))
    result = source.at_many(indices=bad)
    assert isinstance(result, Failed)
    assert result.error.code in (ErrorCode.ILLEGAL_ARGUMENT, ErrorCode.OUT_OF_RANGE)
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize("cls", _TYPES)
def test_only_builtin_list_is_accepted_without_executing_custom_iterators(
    cls: type[Any],
) -> None:
    class Coordinates(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError(
                "不得遍历自定义容器 / Do not iterate custom containers"
            )

    source = cls(Shape1(1), np.zeros(1))
    for indices in (Coordinates([(0,)]), ((0,),), None, 4):
        assert source.at_many(indices=indices).is_failed()
    with pytest.raises(TypeError):
        source.at_many([(0,)])
    assert "return" in get_type_hints(cls.at_many)


@pytest.mark.parametrize("cls", _TYPES)
def test_one_shape_one_native_batch_index_and_one_native_collection(
    cls: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    create, indices_of, collect = (
        _native._create_shape,
        _native.Shape.indices_of,
        _native._read_shared_array,
    )

    def create_shape(**kwargs: Any) -> Any:
        calls.append("shape")
        return create(**kwargs)

    def batch_indices(shape: Any, vectors: Any) -> Any:
        calls.append("indices")
        return indices_of(shape, vectors)

    def collect_values(**kwargs: Any) -> Any:
        calls.append("read")
        return collect(**kwargs)

    monkeypatch.setattr(_native, "_create_shape", create_shape)
    monkeypatch.setattr(_native.Shape, "indices_of", batch_indices)
    monkeypatch.setattr(_native, "_read_shared_array", collect_values)
    source = cls(Shape2(2, 3), np.arange(6))
    assert source.at_many(indices=[(0, 2), (1, 1), (0, 2)]).unwrap() == [2, 4, 2]
    assert calls == ["shape", "indices", "read"]


@pytest.mark.parametrize("cls", _TYPES)
def test_custom_shape_is_explicit_metadata_read_once_and_no_legacy_algorithms(
    cls: type[Any],
) -> None:
    calls: list[str] = []

    class Shape:
        @property
        def dims(self) -> tuple[int, ...]:
            calls.append("dims")
            return (2, 3)

        @property
        def storage_order(self) -> StorageOrder:
            calls.append("order")
            return StorageOrder.COLUMN_MAJOR

        def flat_index(self, *indices: int) -> int:
            raise AssertionError("不得调用旧索引 / Do not call legacy indexing")

        def strides(self) -> Any:
            raise AssertionError("不得调用旧步长 / Do not call legacy strides")

    source = cls(Shape(), np.arange(6))
    assert source.at_many(indices=[(1, 1)]).is_failed()
    assert calls == []
    assert source.at_many(indices=[(1, 1), (1, 2)], standard_layout=True).unwrap() == [
        3,
        5,
    ]
    assert calls == ["dims", "order"]
    assert source.at_many(indices=[], standard_layout=1).is_failed()


@pytest.mark.parametrize("cls", _TYPES)
def test_scalar_empty_and_inconsistent_storage(cls: type[Any]) -> None:
    source = cls(DynShape(()), _objects([None]))
    assert source.at_many(indices=[(), (), ()]).unwrap() == [None, None, None]
    assert source.at_many(indices=[(0,)]).is_failed()
    assert source.at_many(indices=[]).unwrap() == []
    source._data = np.empty(0)
    assert source.at_many(indices=[]).is_failed()
    source._data = [None]
    assert source.at_many(indices=[]).is_failed()
    source._data = np.zeros((1, 1))
    assert source.at_many(indices=[]).is_failed()
    source._shape = DynShape((2**128, 1))
    assert source.at_many(indices=[]).is_failed()
    assert source._shape.size == 2**128


@pytest.mark.parametrize("cls", _TYPES)
def test_opaque_result_and_spoofed_class_leaves_retain_identity(cls: type[Any]) -> None:
    class Opaque:
        @property
        def __class__(self) -> Any:
            raise AssertionError("不得执行伪装类型 / Do not execute spoofed type")

        def item(self) -> Any:
            raise AssertionError("不得执行普通 item / Do not execute ordinary item")

    values = [
        Opaque(),
        np.array([1]),
        None,
        Ok(4),
        Failed(Err(ErrorCode.APPLICATION_ERROR, "leaf")),
    ]
    source = cls(Shape1(len(values)), _objects(values))
    result = source.at_many(indices=[(index,) for index in range(len(values))]).unwrap()
    assert all(left is right for left, right in zip(result, values, strict=True))


@pytest.mark.parametrize("cls", _TYPES)
def test_item_reentry_observes_ordered_live_slots_on_the_captured_buffer(
    cls: type[Any],
) -> None:
    class Scalar(np.float64):
        def item(self, *args: Any) -> Any:
            data[1] = 42
            source._data = np.array([100, 101])
            assert source.at_many(indices=[(1,)]).unwrap() == [101]
            return 1.5

    data = _objects([Scalar(1.5), 0])
    source = cls(Shape1(2), data)
    assert source.at_many(indices=[(0,), (1,)]).unwrap() == [1.5, 42]
    assert source.at_many(indices=[(0,), (1,)]).unwrap() == [100, 101]


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "exception_type", [RuntimeError, StopIteration, KeyboardInterrupt, SystemExit]
)
def test_external_failure_identity_and_no_partial_result(
    cls: type[Any], exception_type: type[BaseException]
) -> None:
    class Error(exception_type):
        def __str__(self) -> str:
            raise AssertionError(
                "不得格式化外部异常 / Do not format external exception"
            )

    error = Error()
    reads: list[int] = []

    class Data(np.ndarray):
        def __getitem__(self, index: int) -> Any:
            reads.append(index)
            if index == 1:
                raise error
            return super().__getitem__(index)

    source = cls(Shape1(3), np.arange(3).view(Data))
    if issubclass(exception_type, Exception):
        result = source.at_many(indices=[(0,), (1,), (2,)])
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
        assert error.__traceback__ is not None
    else:
        with pytest.raises(exception_type) as caught:
            source.at_many(indices=[(0,), (1,), (2,)])
        assert caught.value is error
    assert reads == [0, 1]


def test_failed_collection_releases_unpublished_leaves() -> None:
    references: list[weakref.ReferenceType[Any]] = []

    class Leaf:
        pass

    class Scalar(np.float64):
        def item(self, *args: Any) -> Any:
            leaf = Leaf()
            references.append(weakref.ref(leaf))
            return leaf

    class Broken(np.float64):
        def item(self, *args: Any) -> Any:
            raise RuntimeError("failure")

    source = MultiArray(Shape1(2), _objects([Scalar(0), Broken(1)]))
    failure = source.at_many(indices=[(0,), (1,)])
    assert failure.is_failed()
    gc.collect()
    assert references[0]() is None


@pytest.mark.parametrize("cls", _TYPES)
def test_completed_list_retains_leaves_but_not_owner_or_numeric_buffer(
    cls: type[Any],
) -> None:
    for _ in range(100):
        data = np.arange(4, dtype=np.int16)
        source = cls(Shape2(2, 2), data)
        source_ref, data_ref = weakref.ref(source), weakref.ref(data)
        result = source.at_many(indices=[(0, 1), (1, 0), (0, 1)])
        del source, data
        assert source_ref() is None and data_ref() is None
        assert result.unwrap() == [1, 2, 1]


@pytest.mark.parametrize("cls", [binding.MultiArray, binding.MutableMultiArray])
@pytest.mark.parametrize("order", _ORDERS)
def test_actual_legacy_consumer_reuses_raw_collector_without_numpy_snapshot(
    *, cls: type[Any], order: StorageOrder, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []
    original = _native._read_shared_array

    def collect(**kwargs: Any) -> Any:
        calls.append(kwargs)
        return original(**kwargs)

    def forbidden(**kwargs: Any) -> Any:
        raise AssertionError(
            "不得调用旧 NumPy 快照 / Do not call the old NumPy snapshot"
        )

    monkeypatch.setattr(_native, "_read_shared_array", collect)
    monkeypatch.setattr(binding, "_numpy_snapshot", forbidden)
    data = np.arange(12, dtype=np.int16)[::-2]
    source = MultiArray(Shape2(2, 3, order), data)
    imported = cls.from_legacy_state(payload=vars(source), copy=True).unwrap()
    assert len(calls) == 1 and calls[0]["data"] is data
    assert calls[0]["count"] == 6 and "scalar_type" not in calls[0]
    leaves = imported.flatten(access_order=order).unwrap()
    assert leaves == [11, 9, 7, 5, 3, 1] and all(
        type(value) is np.int16 for value in leaves
    )
    data[:] = -1
    assert imported.at((1, 2)).unwrap() == 1


@pytest.mark.parametrize("cls", [binding.MultiArray, binding.MutableMultiArray])
def test_legacy_import_preserves_original_external_collector_error(
    cls: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    error = RuntimeError("external collection")

    def collect(**kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(_native, "_read_shared_array", collect)
    result = cls.from_legacy_state(
        payload={"_shape": Shape1(1), "_data": np.zeros(1)}, copy=True
    )
    assert isinstance(result, Failed) and result.error.value.callback_exception is error


def test_native_collector_defensive_count_validation() -> None:
    with pytest.raises(ValueError):
        _native._read_shared_array(data=[1], count=2, offsets=[0])
    with pytest.raises(OverflowError):
        _native._read_shared_array(data=[], count=sys.maxsize)
    with pytest.raises(ValueError):
        _native._read_shared_array(data=[1, 2], count=1)

    class Changed:
        def __len__(self) -> int:
            return 2

        def __iter__(self) -> Any:
            return iter([1, 2, 3])

    with pytest.raises(ValueError):
        _native._read_shared_array(data=Changed(), count=2)


_NATIVE_HAS_BATCH_READ = hasattr(_native.MultiArray, "at_many") and hasattr(
    _native.MultiArray, "get"
)


@pytest.mark.skipif(
    not _NATIVE_HAS_BATCH_READ,
    reason=(
        "native build predates the bound at_many/get; rebuild the extension to exercise these"
    ),
)
@pytest.mark.parametrize("order", _ORDERS)
def test_binding_layer_single_and_duplicate_batch_reads(
    *, order: StorageOrder
) -> None:
    """绑定层 `get` / `at_many` 必须能读，且重复坐标按输入顺序重复返回。

    The binding layer's `get` / `at_many` must read, and repeated coordinates must be returned
    once per occurrence in input order. `at_many` exists precisely because `set_many`-style
    coordinate de-duplication would silently drop repeats, so a batch with duplicates is the
    only shape that proves the method is wired to the native read path.
    """
    data = np.arange(6, dtype=np.float64)
    source = MultiArray(Shape2(2, 3, order), data)
    # `get` / `at_many` 只加在不可变类上，与既有的 `reshape` / `to_storage_order` 同一取向：
    # 可变类暴露 `set` / `set_many`，只读的派生操作留在不可变类。
    # `get` / `at_many` live on the immutable class only, matching the existing `reshape` /
    # `to_storage_order` split: the mutable class exposes `set` / `set_many`.
    native = binding.MultiArray.from_legacy_state(
        payload=vars(source), copy=True
    ).unwrap()

    # 期望值一律经 `at` 求出，避免把行主序的结果写死——列主序下同样的逻辑坐标对应不同物理槽位。
    # Derive every expectation through `at` so the assertion is storage-order independent.
    expected_first = native.at((0, 1)).unwrap()
    expected_second = native.at((1, 0)).unwrap()
    assert native.get(1, 2) == native.at((1, 2)).unwrap()
    assert native.at_many([(0, 1), (0, 1), (1, 0)]).unwrap() == [
        expected_first,
        expected_first,
        expected_second,
    ]
    assert native.at_many([]).unwrap() == []
    assert isinstance(native.at_many([(0, 1), (9, 9)]), Failed)
