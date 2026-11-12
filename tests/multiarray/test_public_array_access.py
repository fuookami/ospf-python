"""公共共享数组受检读写合同 / Checked read/write contracts for public shared arrays."""

from __future__ import annotations

import gc
import weakref
from typing import Any, get_type_hints

import numpy as np
import pytest

from ospf_python._binding import public_array_access as access
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
)
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
@pytest.mark.parametrize("step", [1, -2])
def test_checked_reads_follow_coordinates_and_live_strided_storage(
    *, cls: type[Any], order: StorageOrder, step: int
) -> None:
    data = np.arange(12, dtype=np.int16)[::step][:6]
    source = cls(Shape2(2, 3, order), data)
    for i in range(2):
        for j in range(3):
            offset = i * 3 + j if order is StorageOrder.ROW_MAJOR else i + j * 2
            result = source.at(indices=(i, j))
            assert isinstance(result, Ok)
            assert type(result.value) is int and result.value == data[offset]
    data[-1] = 42
    assert source.at(indices=(1, 2)).unwrap() == 42
    replacement = np.arange(6) + 100
    source._data = replacement
    assert source.at(indices=(1, 2)).unwrap() == 105
    source._shape = Shape2(3, 2, order)
    assert source.at(indices=(2, 1)).unwrap() == 105


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize(
    "source_shape",
    [Shape1(6), Shape2(2, 3), Shape3(2, 1, 3), Shape4(1, 2, 1, 3)],
    ids=["shape1", "shape2", "shape3", "shape4"],
)
def test_builtin_fixed_shape_ranks_use_the_same_checked_boundary(
    *, cls: type[Any], order: StorageOrder, source_shape: Any
) -> None:
    shape = type(source_shape)(*source_shape.dims, storage_order=order)
    source = cls(shape, np.arange(6))
    first = tuple(0 for _ in shape.dims)
    last = tuple(dimension - 1 for dimension in shape.dims)
    assert source.at(indices=first).unwrap() == 0
    assert source.at(indices=last).unwrap() == 5
    if cls is MutableMultiArray:
        source.set_at(indices=last, value=23).unwrap()
        assert source._data[shape.flat_index(*last)] == 23


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    ("indices", "code"),
    [
        ((), ErrorCode.ILLEGAL_ARGUMENT),
        ((0,), ErrorCode.ILLEGAL_ARGUMENT),
        ((0, 0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((-1, 0), ErrorCode.OUT_OF_RANGE),
        ((0, 3), ErrorCode.OUT_OF_RANGE),
        ((2, 0), ErrorCode.OUT_OF_RANGE),
        ((2**200, 0), ErrorCode.OUT_OF_RANGE),
        ((True, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((0.0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ([0, 0], ErrorCode.ILLEGAL_ARGUMENT),
        ((np.int64(0), 0), ErrorCode.ILLEGAL_ARGUMENT),
    ],
)
def test_invalid_coordinates_are_results_without_legacy_aliasing(
    *, cls: type[Any], indices: Any, code: ErrorCode
) -> None:
    source = cls(Shape2(2, 3), np.arange(6))
    result = source.at(indices=indices)
    assert isinstance(result, Failed) and result.error.code is code
    if cls is MutableMultiArray:
        failure = source.set_at(indices=indices, value=99)
        assert isinstance(failure, Failed) and failure.error.code is code
        np.testing.assert_array_equal(source._data, np.arange(6))


@pytest.mark.parametrize("cls", _TYPES)
def test_scalar_access_uses_one_shared_native_protocol_call(
    cls: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    read, write = access._read_shared_slot, access._write_shared_slot
    calls: list[tuple[str, tuple[int, ...], bool]] = []

    def read_slot(**kwargs: Any) -> Any:
        calls.append(("read", kwargs["indices"], kwargs["standard_layout"]))
        return read(**kwargs)

    def write_slot(**kwargs: Any) -> Any:
        calls.append(("write", kwargs["indices"], kwargs["standard_layout"]))
        return write(**kwargs)

    monkeypatch.setattr(access, "_read_shared_slot", read_slot)
    monkeypatch.setattr(access, "_write_shared_slot", write_slot)
    source = cls(Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6))
    assert source.at(indices=(1, 1)).unwrap() == 3
    if cls is MutableMultiArray:
        source.set_at(indices=(1, 1), value=80).unwrap()
        assert source._data[3] == 80
        assert calls == [
            ("read", (1, 1), False),
            ("write", (1, 1), False),
        ]
    else:
        assert calls == [("read", (1, 1), False)]


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("step", [1, -2])
def test_checked_write_preserves_external_aliases_dtype_and_no_mirror(
    order: StorageOrder, step: int
) -> None:
    backing = np.arange(12, dtype=np.int16)
    data = backing[::step][:6]
    source = MutableMultiArray(Shape2(2, 3, order), data)
    alias = MultiArray(source.shape, data)
    source.set_at(indices=(1, 1), value=17).unwrap()
    offset = 4 if order is StorageOrder.ROW_MAJOR else 3
    assert data[offset] == 17
    assert alias.at(indices=(1, 1)).unwrap() == 17
    assert source._data is data and data.dtype == np.int16
    assert vars(source) == {"_shape": source.shape, "_data": data}
    source.set_at(indices=(0, 0), value=1.9).unwrap()
    assert alias.at(indices=(0, 0)).unwrap() == 1


@pytest.mark.parametrize("cls", _TYPES)
def test_scalar_shape_result_and_opaque_leaves_are_not_unwrapped(
    cls: type[Any],
) -> None:
    class Opaque:
        @property
        def __class__(self) -> Any:
            raise AssertionError("不得执行伪装类型 / Do not execute spoofed type")

        def item(self) -> Any:
            raise AssertionError("不得调用普通 item / Do not call ordinary item")

    values = [
        None,
        Opaque(),
        np.array([1]),
        Ok(3),
        Failed(Err(ErrorCode.APPLICATION_ERROR, "leaf")),
    ]
    for value in values:
        source = cls(DynShape(()), _objects([value]))
        result = source.at(indices=())
        assert isinstance(result, Ok) and result.value is value
        if cls is MutableMultiArray:
            source.set_at(indices=(), value=value).unwrap()
            assert source._data[0] is value


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("scalar", [np.int16(3), np.float32(1.5), np.bool_(True)])
def test_true_numpy_scalars_keep_item_conversion(cls: type[Any], scalar: Any) -> None:
    source = cls(Shape1(1), _objects([scalar]))
    value = source.at(indices=(0,)).unwrap()
    assert type(value) is type(scalar.item()) and value == scalar.item()


@pytest.mark.parametrize("cls", _TYPES)
def test_custom_shape_is_never_implicitly_reinterpreted(cls: type[Any]) -> None:
    class Custom:
        dims = (2, 3)
        storage_order = StorageOrder.COLUMN_MAJOR

        @property
        def size(self) -> int:
            raise AssertionError("不得读取 size / Do not read size")

        def strides(self) -> Any:
            raise AssertionError("不得调用 strides / Do not call strides")

        def flat_index(self, *indices: int) -> int:
            raise AssertionError("不得调用旧算法 / Do not call legacy indexing")

    source = cls(Custom(), np.arange(6))
    assert source.at(indices=(1, 1)).is_failed()
    assert source.at(indices=(1, 1), standard_layout=True).unwrap() == 3
    assert source.at(indices=(1, 1), standard_layout=1).is_failed()
    if cls is MutableMultiArray:
        assert source.set_at(indices=(1, 1), value=9).is_failed()
        source.set_at(indices=(1, 1), value=9, standard_layout=True).unwrap()
        assert source._data[3] == 9


@pytest.mark.parametrize("cls", _TYPES)
def test_shape_subclasses_require_opt_in_and_huge_metadata_stays_valid(
    cls: type[Any],
) -> None:
    class Child(Shape2):
        def flat_index(self, *indices: int) -> int:
            raise AssertionError("不得调用覆盖的映射 / Do not call overridden mapping")

    source = cls(Child(2, 3), np.arange(6))
    assert source.at(indices=(1, 1)).is_failed()
    assert source.at(indices=(1, 1), standard_layout=True).unwrap() == 4
    huge = DynShape((2**128, 3))
    source._shape = huge
    assert source.at(indices=(0, 0)).is_failed()
    assert huge.size == 3 * 2**128


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "data", [np.arange(5), np.arange(7), np.arange(6).reshape(2, 3), list(range(6))]
)
def test_inconsistent_or_non_ndarray_storage_is_rejected(
    cls: type[Any], data: Any
) -> None:
    source = cls(Shape2(2, 3), data)
    assert source.at(indices=(0, 0)).is_failed()
    if cls is MutableMultiArray:
        assert source.set_at(indices=(0, 0), value=99).is_failed()


def test_readonly_and_failed_dtype_assignment_return_original_external_exception() -> (
    None
):
    data = np.arange(2)
    source = MutableMultiArray(Shape1(2), data)
    data.flags.writeable = False
    result = source.set_at(indices=(0,), value=5)
    assert isinstance(result, Failed)
    assert isinstance(result.error.value.callback_exception, ValueError)
    assert result.error.value.error_class == "EXTERNAL_ARRAY"
    assert source.at(indices=(0,)).unwrap() == 0
    data.flags.writeable = True
    result = source.set_at(indices=(0,), value="not-an-int")
    assert isinstance(result, Failed)
    assert isinstance(result.error.value.callback_exception, ValueError)
    np.testing.assert_array_equal(data, [0, 1])


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "exception_type", [RuntimeError, StopIteration, KeyboardInterrupt, SystemExit]
)
def test_external_exception_identity_no_stringification_and_process_control(
    cls: type[Any], exception_type: type[BaseException]
) -> None:
    class Unprintable(exception_type):
        def __str__(self) -> str:
            raise AssertionError("不得格式化用户异常 / Do not format user exceptions")

    error = Unprintable()

    class Data(np.ndarray):
        def __getitem__(self, key: Any) -> Any:
            raise error

        def __setitem__(self, key: Any, value: Any) -> None:
            raise error

    source = cls(Shape1(1), np.zeros(1).view(Data))
    operations = [lambda: source.at(indices=(0,))]
    if cls is MutableMultiArray:
        operations.append(lambda: source.set_at(indices=(0,), value=2))
    for operation in operations:
        if issubclass(exception_type, Exception):
            result = operation()
            assert isinstance(result, Failed)
            assert result.error.value.callback_exception is error
            assert error.__traceback__ is not None
        else:
            with pytest.raises(exception_type) as caught:
                operation()
            assert caught.value is error


@pytest.mark.parametrize("cls", _TYPES)
def test_custom_shape_property_failure_retains_identity(cls: type[Any]) -> None:
    error = RuntimeError("shape failure")

    class Shape:
        @property
        def dims(self) -> Any:
            raise error

    source = cls(Shape(), np.zeros(1))
    assert source.at(indices=(0,)).is_failed()
    result = source.at(indices=(0,), standard_layout=True)
    assert isinstance(result, Failed) and result.error.value.callback_exception is error


def test_successful_access_keeps_no_owner_or_buffer_cache() -> None:
    for _ in range(100):
        data = np.arange(2)
        source = MutableMultiArray(Shape1(2), data)
        source_ref, data_ref = weakref.ref(source), weakref.ref(data)
        result = source.at(indices=(0,))
        written = source.set_at(indices=(1,), value=4)
        del source, data
        gc.collect()
        assert source_ref() is None and data_ref() is None
        assert result.unwrap() == 0 and written.is_ok()


@pytest.mark.parametrize("cls", _TYPES)
def test_public_type_hints_are_resolvable_and_new_arguments_are_keyword_only(
    cls: type[Any],
) -> None:
    assert "return" in get_type_hints(cls.at)
    source = cls(Shape1(1), np.zeros(1))
    with pytest.raises(TypeError):
        source.at((0,))
    if cls is MutableMultiArray:
        assert "return" in get_type_hints(cls.set_at)
        with pytest.raises(TypeError):
            source.set_at((0,), 5)


@pytest.mark.parametrize("cls", _TYPES)
def test_failed_index_does_not_access_external_storage(cls: type[Any]) -> None:
    class Source(cls):
        def __getattribute__(self, name: str) -> Any:
            if name == "_data":
                raise AssertionError(
                    "无效索引不得访问存储 / Invalid indices must not access storage"
                )
            return super().__getattribute__(name)

    source = Source(Shape2(2, 3), np.arange(6))
    result = source.at(indices=(0, 3))
    assert isinstance(result, Failed) and result.error.code is ErrorCode.OUT_OF_RANGE
    if cls is MutableMultiArray:
        result = source.set_at(indices=(0, 3), value=4)
        assert (
            isinstance(result, Failed) and result.error.code is ErrorCode.OUT_OF_RANGE
        )


@pytest.mark.parametrize("cls", _TYPES)
def test_real_scalar_subclass_item_is_an_external_protocol(cls: type[Any]) -> None:
    error = RuntimeError("scalar failure")

    class Scalar(np.float64):
        def item(self, *args: Any) -> Any:
            raise error

    source = cls(Shape1(1), _objects([Scalar(1)]))
    result = source.at(indices=(0,))
    assert isinstance(result, Failed) and result.error.value.callback_exception is error


def test_dtype_callback_can_reenter_without_a_storage_lock() -> None:
    source = MutableMultiArray(Shape1(2), np.zeros(2))

    class Value:
        def __float__(self) -> float:
            source.set_at(indices=(1,), value=7.0).unwrap()
            assert source.at(indices=(1,)).unwrap() == 7.0
            return 3.5

    source.set_at(indices=(0,), value=Value()).unwrap()
    np.testing.assert_array_equal(source._data, [3.5, 7.0])
