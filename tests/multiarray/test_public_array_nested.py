"""公共数组嵌套导出的完整协议 / Complete public-array nested-export protocols."""

from __future__ import annotations

import copy
import gc
import pickle
import weakref
from fractions import Fraction
from typing import Any, cast, get_type_hints

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape, Shape1, Shape2, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = list(StorageOrder)


class _Opaque:
    def item(self) -> Any:
        pytest.fail("普通叶不能调用 item / Ordinary leaves must not call item")

    def __iter__(self) -> Any:
        pytest.fail("普通叶不能遍历 / Ordinary leaves must not be iterated")


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (6,), (2, 3), (1, 2, 1, 3)])
@pytest.mark.parametrize("step", [1, -2])
def test_logical_nested_values_follow_pinned_layout_not_physical_c_reshape(
    *, cls: type[Any], order: StorageOrder, dims: tuple[int, ...], step: int
) -> None:
    count = int(np.prod(dims))
    backing = np.arange(2 * count, dtype=np.int16)
    data = backing[::step][:count]
    shape = DynShape(dims, order)
    source = cls(shape, data)
    expected = data.reshape(
        dims, order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    ).tolist()
    actual = source.to_list()
    assert isinstance(actual, Ok) and actual.value == expected
    assert source.shape is shape and source._data is data
    if dims:
        assert type(actual.value) is list
    else:
        assert type(actual.value) is int


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize(
    "dtype",
    [
        "bool",
        "int16",
        ">i4",
        "uint64",
        "float32",
        "complex128",
        "datetime64[ns]",
        "timedelta64[us]",
        "S4",
        "U4",
        "V2",
    ],
)
def test_dtype_conversion_is_numpy_serialization_not_public_get_item(
    *, cls: type[Any], order: StorageOrder, dtype: str
) -> None:
    data = np.zeros(6, dtype=dtype)
    data.flags.writeable = False
    result = cls(Shape2(2, 3, order), data).to_list().unwrap()
    expected = data.reshape(
        (2, 3), order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    ).tolist()
    assert result == expected
    assert type(result[0][0]) is type(expected[0][0])


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_structured_subarray_and_metadata_dtype_keep_numpy_leaf_protocols(
    *, cls: type[Any], order: StorageOrder
) -> None:
    dtype = np.dtype([("key", "i2"), ("values", "f8", (2,))], metadata={"unit": "m"})
    data = np.zeros(6, dtype=dtype)
    data["key"] = np.arange(6)
    data["values"] = np.arange(12).reshape((6, 2))
    actual = cls(Shape2(2, 3, order), data).to_list().unwrap()
    expected = data.reshape(
        (2, 3), order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    ).tolist()
    for row in range(2):
        for col in range(3):
            assert type(actual[row][col]) is tuple
            assert actual[row][col][0] == expected[row][col][0]
            np.testing.assert_array_equal(actual[row][col][1], expected[row][col][1])
    assert data.dtype is dtype


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_string_dtype_missing_values_and_extended_float_keep_numpy_conversion(
    *, cls: type[Any], order: StorageOrder
) -> None:
    arrays = [
        np.array(
            ["a", None, "b", "c", "d", "e"], dtype=np.dtypes.StringDType(na_object=None)
        ),
        np.arange(6, dtype=np.longdouble) / 8,
    ]
    for data in arrays:
        actual = cls(Shape2(2, 3, order), data).to_list().unwrap()
        expected = data.reshape(
            (2, 3), order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
        ).tolist()
        assert actual == expected
        assert type(actual[0][0]) is type(expected[0][0])


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_object_leaves_results_numpy_scalars_and_aliases_are_opaque(
    *, cls: type[Any], order: StorageOrder
) -> None:
    leaf = _Opaque()
    scalar = np.int16(7)
    failure: Any = Failed(Err(ErrorCode.NOT_FOUND, "leaf"))
    values = [leaf, leaf, scalar, failure, None, np.array([1, 2])]
    data = np.empty(6, dtype=object)
    for index, value in enumerate(values):
        data[index] = value
    source = cls(Shape2(2, 3, order), data)
    nested = source.to_list().unwrap()
    for row in range(2):
        for col in range(3):
            offset = row * 3 + col if order is StorageOrder.ROW_MAJOR else row + col * 2
            assert nested[row][col] is values[offset]
    assert source.get(*((0, 2) if order is StorageOrder.ROW_MAJOR else (0, 1))) == 7
    assert type(scalar) is np.int16
    nested[0][0] = 42
    assert data[0] is leaf
    source._data = data.copy()
    source._data[0] = Fraction(2, 3)
    assert source.to_list().unwrap()[0][0] == Fraction(2, 3)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_nonflat_and_transposed_external_storage_uses_its_c_physical_sequence(
    *, cls: type[Any], order: StorageOrder
) -> None:
    data = np.arange(6).reshape((3, 2)).T
    source = cls(Shape2(3, 2, order), data)
    expected = (
        data.ravel(order="C")
        .reshape((3, 2), order="F" if order is StorageOrder.COLUMN_MAJOR else "C")
        .tolist()
    )
    assert source.to_list().unwrap() == expected
    assert source._data is data and data.shape == (2, 3)


@pytest.mark.parametrize("cls", _TYPES)
def test_standard_path_is_native_without_get_flat_index_or_python_reshape(
    cls: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    import ospf_python.multiarray.multi_array as module
    from ospf_python._binding import shared_nested

    original = module._DEFAULT_NESTED_TO_LIST
    calls = []

    def wrapped(owner: Any) -> Any:
        calls.append(owner)
        return original(owner)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("默认导出不调用旧索引 / Default export must not call old indexing")

    assert type(shared_nested._protocol) is _native._SharedNested
    monkeypatch.setattr(module, "_DEFAULT_NESTED_TO_LIST", wrapped)
    monkeypatch.setattr(cls, "get", forbidden)
    monkeypatch.setattr(Shape2, "flat_index", forbidden)
    source = cls(Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6))
    assert source.to_list().unwrap() == [[0, 2, 4], [1, 3, 5]]
    assert calls == [source]


@pytest.mark.parametrize("cls", _TYPES)
def test_exact_shape2_fast_path_still_reads_public_dims_once(
    cls: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = cls(Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6))
    events: list[str] = []

    def dims(shape: Shape2) -> tuple[int, int]:
        events.append("dims")
        assert shape.d0 == 2 and shape.d1 == 3
        return (2, 3)

    monkeypatch.setattr(Shape2, "dims", property(dims))
    assert source.to_list().unwrap() == [[0, 2, 4], [1, 3, 5]]
    assert events == ["dims"]


@pytest.mark.parametrize("cls", _TYPES)
def test_scalar_none_and_results_have_one_outer_success(cls: type[Any]) -> None:
    values: tuple[Any, ...] = (
        None,
        Ok(3),
        Failed(Err(ErrorCode.NOT_FOUND, "leaf")),
        _Opaque(),
    )
    for value in values:
        data = np.empty(1, dtype=object)
        data[0] = value
        result = cls(DynShape(()), data).to_list()
        assert isinstance(result, Ok) and result.value is value


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("dims", [(0,), (-1,), (2**128,), (2**62, 4)])
def test_invalid_or_overflowing_raw_shape_returns_failure_without_changing_source(
    *, cls: type[Any], dims: tuple[int, ...]
) -> None:
    shape = DynShape((1,))
    object.__setattr__(shape, "dims", dims)
    data = np.array([1])
    source = cls(shape, data)
    assert isinstance(source.to_list(), Failed)
    assert source._data is data and source.shape is shape


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    ("dims", "code"),
    [
        ((True, 3), ErrorCode.ILLEGAL_ARGUMENT),
        ((-1, 3), ErrorCode.OVERFLOW),
        ((2**128, 3), ErrorCode.OVERFLOW),
        ((2**62, 4), ErrorCode.OVERFLOW),
    ],
)
def test_exact_shape2_fast_path_keeps_metadata_failure_codes(
    *, cls: type[Any], dims: tuple[int, int], code: ErrorCode
) -> None:
    shape = Shape2(1, 1)
    object.__setattr__(shape, "d0", dims[0])
    object.__setattr__(shape, "d1", dims[1])
    data = np.array([1])
    result = cls(shape, data).to_list()
    assert isinstance(result, Failed) and result.error.code is code


@pytest.mark.parametrize("cls", _TYPES)
def test_shape_count_mismatch_does_not_truncate_or_fill(cls: type[Any]) -> None:
    for data in (np.arange(5), np.arange(7), np.array(3)):
        source = cls(Shape2(2, 3), data)
        result = source.to_list()
        assert (
            isinstance(result, Failed)
            and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        )
        assert source._data is data


@pytest.mark.parametrize("cls", _TYPES)
def test_external_protocol_captures_callable_before_shape_and_preserves_result_data(
    cls: type[Any],
) -> None:
    events: list[Any] = []
    token = object()
    result: Any = Failed(Err(ErrorCode.NOT_FOUND, "external data"))

    class Storage:
        @property
        def reshape(self) -> Any:
            events.append("reshape")

            def reshape(dims: Any) -> Any:
                assert dims is token
                events.append("call")
                return self

            return reshape

        def tolist(self) -> Any:
            events.append("tolist")
            return result

    class Shape:
        @property
        def dims(self) -> Any:
            events.append("dims")
            source._data = object()
            return token

    source = cls(Shape(), Storage())
    actual = source.to_list()
    assert isinstance(actual, Ok) and actual.value is result
    assert events == ["reshape", "dims", "call", "tolist"]


@pytest.mark.parametrize("cls", _TYPES)
def test_ndarray_and_shape_subclasses_keep_their_external_protocol(
    cls: type[Any],
) -> None:
    calls: list[Any] = []

    class Data(np.ndarray[Any, Any]):
        def reshape(self, *args: Any, **kwargs: Any) -> Any:
            calls.append(("reshape", args, kwargs))
            return self

        def tolist(self) -> Any:
            calls.append("tolist")
            return "custom"

    source = cls(Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6).view(Data))
    assert source.to_list().unwrap() == "custom"
    assert calls == [("reshape", ((2, 3),), {}), "tolist"]

    class Shape(Shape2):
        pass

    source = cls(Shape(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6))
    assert source.to_list().unwrap() == [[0, 1, 2], [3, 4, 5]]


@pytest.mark.parametrize("cls", _TYPES)
def test_metadata_failure_stops_before_later_integer_protocols(cls: type[Any]) -> None:
    class Forbidden:
        def __index__(self) -> int:
            pytest.fail(
                "容量失败后不再读取维度 / Do not read dimensions after capacity failure"
            )

    for dims, code in [
        ((True, Forbidden()), ErrorCode.ILLEGAL_ARGUMENT),
        ((2**128, Forbidden()), ErrorCode.OVERFLOW),
        ((2**62, 4, Forbidden()), ErrorCode.OVERFLOW),
    ]:
        shape = DynShape((1,))
        object.__setattr__(shape, "dims", dims)
        result = cls(shape, np.array([1])).to_list()
        assert isinstance(result, Failed) and result.error.code is code


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "exception_type",
    [
        TypeError,
        ValueError,
        OverflowError,
        RuntimeError,
        StopIteration,
        KeyboardInterrupt,
        SystemExit,
    ],
)
def test_external_exceptions_keep_original_identity_without_formatting(
    *, cls: type[Any], exception_type: type[BaseException]
) -> None:
    class Unprintable:
        def __str__(self) -> str:
            pytest.fail(
                "不得格式化外部异常 / External exceptions must not be formatted"
            )

    error: BaseException = type("ExternalError", (Unprintable, exception_type), {})()

    class Storage:
        def reshape(self, dims: Any) -> Any:
            raise error

    source = cls(Shape1(1), Storage())
    if issubclass(exception_type, Exception):
        result = source.to_list()
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
        assert result.error.value.error_class == "EXTERNAL_NESTED_CONVERSION"
    else:
        with pytest.raises(exception_type) as caught:
            source.to_list()
        assert caught.value is error


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_legacy_fields_copy_pickle_and_no_persistent_source_cache(
    *, cls: type[Any], protocol: int
) -> None:
    source = object.__new__(cls)
    data = np.arange(6)
    source.__dict__.update(_shape=Shape2(2, 3, StorageOrder.COLUMN_MAJOR), _data=data)
    restored = pickle.loads(pickle.dumps(source, protocol=protocol))
    assert (
        restored.to_list().unwrap()
        == copy.copy(source).to_list().unwrap()
        == [[0, 2, 4], [1, 3, 5]]
    )
    source_ref, data_ref = weakref.ref(source), weakref.ref(data)
    result = source.to_list()
    del source, data
    gc.collect()
    assert source_ref() is None and data_ref() is None
    assert result.unwrap() == [[0, 2, 4], [1, 3, 5]]
    assert "return" in get_type_hints(cls.to_list)


@pytest.mark.parametrize("cls", _TYPES)
def test_numpy_integer_dimensions_and_high_rank_do_not_use_python_recursion(
    cls: type[Any],
) -> None:
    shape = cast("Any", Shape2)(np.int64(2), np.int64(3), StorageOrder.COLUMN_MAJOR)
    assert cls(shape, np.arange(6)).to_list().unwrap() == [[0, 2, 4], [1, 3, 5]]
    nested = cls(DynShape((1,) * 1024), np.array([7])).to_list().unwrap()
    for _ in range(1024):
        assert type(nested) is list and len(nested) == 1
        nested = nested[0]
    assert nested == 7


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(3, 2, 5), (2, 1, 3, 2), (17, 1), (1, 31), (7, 3)])
@pytest.mark.parametrize("storage", ["forward", "reverse", "broadcast"])
def test_native_inner_runs_preserve_opaque_identity_and_all_axis_boundaries(
    *, cls: type[Any], order: StorageOrder, dims: tuple[int, ...], storage: str
) -> None:
    count = int(np.prod(dims))
    backing = np.empty(count, dtype=object)
    for index in range(count):
        backing[index] = _Opaque()
    data = (
        backing[::-1]
        if storage == "reverse"
        else np.broadcast_to(backing[:1], (count,))
        if storage == "broadcast"
        else backing
    )
    expected = data.reshape(
        dims, order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    ).tolist()
    source = cls(DynShape(dims, order), data)
    assert source.to_list().unwrap() == expected
    assert source._data is data and source.shape.dims == dims


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_structured_export_keeps_buffer_owner_until_last_leaf_is_released(
    *, cls: type[Any], order: StorageOrder
) -> None:
    data = np.zeros(6, dtype=[("values", "i2", (2,))])
    data["values"] = np.arange(12).reshape((6, 2))
    owner_ref = weakref.ref(data)
    nested = cls(Shape2(3, 2, order), data).to_list().unwrap()
    del data
    gc.collect()

    assert owner_ref() is not None
    leaf = nested[0][0][0]
    del nested
    gc.collect()
    assert owner_ref() is not None
    np.testing.assert_array_equal(leaf, [0, 1])

    del leaf
    gc.collect()
    assert owner_ref() is None


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_zero_itemsize_and_structured_leaf_bases_survive_temporary_rows(
    *, cls: type[Any], order: StorageOrder
) -> None:
    empty = np.empty(6, dtype="V0")
    assert cls(Shape2(3, 2, order), empty).to_list().unwrap() == [
        [b"", b""],
        [b"", b""],
        [b"", b""],
    ]
    data = np.zeros(6, dtype=[("values", "i2", (2,))])
    data["values"] = np.arange(12).reshape((6, 2))
    source = cls(Shape2(3, 2, order), data)
    nested = source.to_list().unwrap()
    del source, data
    gc.collect()
    for row in range(3):
        for col in range(2):
            index = row * 2 + col if order is StorageOrder.ROW_MAJOR else row + col * 3
            leaf = nested[row][col][0]
            assert type(leaf) is np.ndarray
            np.testing.assert_array_equal(leaf, [2 * index, 2 * index + 1])
            leaf[0] = -1
            assert nested[row][col][0][0] == -1


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("width", [31, 32, 33, 512])
@pytest.mark.parametrize("domain", ["int16", "longdouble", "void", "string"])
def test_tiny_and_batched_runs_share_dtype_and_layout_contracts(
    *, cls: type[Any], order: StorageOrder, width: int, domain: str
) -> None:
    count = 2 * width
    data: np.ndarray[Any, Any]
    if domain == "void":
        data = np.empty(count, dtype="V0")
    elif domain == "string":
        data = np.array(
            [None if index % 3 == 0 else str(index) for index in range(count)],
            dtype=np.dtypes.StringDType(na_object=None),
        )
    else:
        data = np.arange(count, dtype=domain)
    data.flags.writeable = False
    expected = data.reshape(
        (2, width), order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    ).tolist()
    source = cls(Shape2(2, width, order), data)
    actual = source.to_list().unwrap()
    assert actual == expected
    assert type(actual[0][0]) is type(expected[0][0])
    assert source._data is data and not data.flags.writeable
