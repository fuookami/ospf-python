"""普通公共视图的受检物化合同 / Checked materialization contracts for plain public views."""

from __future__ import annotations

import copy
import gc
import itertools
import pickle
import weakref
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from typing import Any, cast, get_type_hints

import numpy as np
import pytest

from ospf_python.multiarray import (
    DynShape,
    MultiArray,
    MultiArrayView,
    MutableMultiArray,
    Shape2,
    StorageOrder,
)
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = list(StorageOrder)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (5,), (3, 4), (2, 3, 4)])
@pytest.mark.parametrize("stride", [1, -1, 2, 0])
@pytest.mark.parametrize("cropped", [False, True])
def test_materialization_copies_the_checked_suffix_in_target_storage_order(
    *,
    cls: type[Any],
    order: StorageOrder,
    dims: tuple[int, ...],
    stride: int,
    cropped: bool,
) -> None:
    count = int(np.prod(dims))
    backing = np.arange(count * 2, dtype=np.int16)
    data = (
        np.broadcast_to(backing[:1], (count,))
        if stride == 0
        else backing[::stride][:count]
    )
    shape = DynShape(dims, order)
    offsets = tuple(1 if cropped and dim > 1 else 0 for dim in dims)
    source = cls(shape, data)
    view = MultiArrayView(source, offsets=offsets)
    result = view.materialize().unwrap()
    logical = data.reshape(
        dims, order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    )
    region = logical[tuple(slice(offset, None) for offset in offsets)]
    expected = np.asarray(region).ravel(
        order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    )
    np.testing.assert_array_equal(result._data, expected)
    assert result._data.dtype == data.dtype and type(result) is MultiArray
    assert result.shape.dims == tuple(
        dim - offset for dim, offset in zip(dims, offsets, strict=True)
    )
    assert result.shape.storage_order is order
    if not any(offsets):
        assert result.shape is shape
    else:
        assert type(result.shape) is DynShape
    assert not np.shares_memory(result._data, data)
    assert vars(view) == {"_source": source, "_offsets": offsets}
    assert view.shape is shape and source._data is data
    for indices in itertools.product(*(range(dim) for dim in result.shape.dims)):
        assert (
            result.get(*indices)
            == logical[
                tuple(
                    index + offset
                    for index, offset in zip(indices, offsets, strict=True)
                )
            ]
        )


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize(
    "dtype", ["int16", ">i4", "longdouble", "datetime64[ns]", "U4", "V0"]
)
def test_copy_and_take_preserve_dtype_and_trailing_storage_axes(
    *, order: StorageOrder, dtype: str
) -> None:
    data = np.zeros((12, 2), dtype=dtype)
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(3, 4, order), data)
    identity = MultiArrayView(source).materialize().unwrap()
    assert identity._data.shape == (12, 2) and identity._data.dtype == data.dtype
    cropped = MultiArrayView(source, offsets=(1, 1)).materialize().unwrap()
    assert cropped._data.shape == (6, 2) and cropped._data.dtype == data.dtype
    assert cropped.shape.dims == (2, 3)
    assert not np.shares_memory(cropped._data, data)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
def test_raw_opaque_results_exact_units_and_numpy_scalars_are_not_coerced(
    *, cls: type[Any], order: StorageOrder
) -> None:
    class Opaque:
        def item(self) -> Any:
            pytest.fail("不得探测叶 / Must not probe leaves")

        def __array__(self, *args: Any, **kwargs: Any) -> Any:
            pytest.fail("不得转换叶 / Must not convert leaves")

    leaves: list[Any] = [
        Opaque(),
        np.int16(8),
        None,
        Ok(4),
        Failed(Err(ErrorCode.NOT_FOUND, "leaf")),
        Fraction(2, 3),
        Quantity(Fraction(4, 5), METER),
    ]
    data = np.empty(12, dtype=object)
    for index in range(12):
        data[index] = leaves[index % len(leaves)]
    source = cls(Shape2(3, 4, order), data)
    view = MultiArrayView(source, offsets=(1, 1))
    result = view.materialize().unwrap()
    for row, col in itertools.product(range(2), range(3)):
        source_index = (
            (row + 1) * 4 + col + 1
            if order is StorageOrder.ROW_MAJOR
            else row + 1 + (col + 1) * 3
        )
        target_index = (
            row * 3 + col if order is StorageOrder.ROW_MAJOR else row + col * 2
        )
        assert result._data[target_index] is data[source_index]


@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("negative", [False, True])
def test_custom_layout_uses_external_index_protocol_without_guessing(
    order: StorageOrder, negative: bool
) -> None:
    calls = []

    class Custom:
        dims = (3, 4)
        ndim = 2
        size = 12
        storage_order = order

        def flat_index(self, *indices: int) -> Any:
            calls.append(indices)
            ordinal = indices[0] * 4 + indices[1]
            return np.int64(-1 - ordinal if negative else 11 - ordinal)

    source: MultiArray[Any, Any] = MultiArray(cast("Any", Custom()), np.arange(12))
    result = MultiArrayView(source, offsets=(1, 1)).materialize().unwrap()
    expected_coords = list(itertools.product(range(1, 3), range(1, 4)))
    if order is StorageOrder.COLUMN_MAJOR:
        expected_coords.sort(key=lambda coords: (coords[1], coords[0]))
    assert calls == expected_coords
    for row, col in itertools.product(range(2), range(3)):
        assert result.get(row, col) == 11 - ((row + 1) * 4 + col + 1)


@pytest.mark.parametrize(
    "offsets,code",
    [
        ((-1, 0), ErrorCode.OUT_OF_RANGE),
        ((3, 0), ErrorCode.OUT_OF_RANGE),
        ((0,), ErrorCode.ILLEGAL_ARGUMENT),
        ((True, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((1 << 100, 0), ErrorCode.OUT_OF_RANGE),
        ([0, 0], ErrorCode.ILLEGAL_ARGUMENT),
        (None, ErrorCode.ILLEGAL_ARGUMENT),
    ],
)
def test_invalid_raw_offsets_fail_without_publishing_or_mutating_source(
    *, offsets: Any, code: ErrorCode
) -> None:
    data = np.arange(12)
    source: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4), data)
    view = object.__new__(MultiArrayView)
    vars(view).update(_source=source, _offsets=offsets)
    result = view.materialize()
    assert isinstance(result, Failed) and result.error.code is code
    assert source._data is data and data.tolist() == list(range(12))


@pytest.mark.parametrize(
    "dims,code",
    [
        ((0, 4), ErrorCode.ILLEGAL_ARGUMENT),
        ((True, 4), ErrorCode.ILLEGAL_ARGUMENT),
        ((1 << 100, 4), ErrorCode.OVERFLOW),
        ((1 << 62, 4), ErrorCode.OVERFLOW),
    ],
)
def test_raw_invalid_shape_is_checked_after_actual_copy_without_huge_allocation(
    *, dims: tuple[Any, ...], code: ErrorCode
) -> None:
    shape = DynShape((3, 4))
    object.__setattr__(shape, "dims", dims)
    source: MultiArray[int, DynShape] = MultiArray(shape, np.arange(12))
    result = MultiArrayView(source, offsets=(1, 1)).materialize()
    assert isinstance(result, Failed) and result.error.code is code


@pytest.mark.parametrize("order", _ORDERS)
def test_standard_path_uses_native_plan_not_python_get_or_flat_index(
    order: StorageOrder, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ospf_python._binding.shared_view as bridge

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("不得调用旧内核 / Must not call legacy kernels")

    monkeypatch.setattr(MultiArray, "get", forbidden)
    monkeypatch.setattr(Shape2, "flat_index", forbidden)
    original = bridge._protocol.materialize
    calls = []

    class Delegate:
        @staticmethod
        def materialize(**kwargs: Any) -> Any:
            calls.append(kwargs["owner"])
            return original(**kwargs)

    monkeypatch.setattr(bridge, "_protocol", Delegate())
    view = MultiArrayView(
        MultiArray(Shape2(3, 4, order), np.arange(12)), offsets=(1, 1)
    )
    result = view.materialize().unwrap()
    assert result._data.tolist() == (
        [5, 6, 7, 9, 10, 11]
        if order is StorageOrder.ROW_MAJOR
        else [4, 5, 7, 8, 10, 11]
    )
    assert calls == [view]


@pytest.mark.parametrize(
    "stage", ["copy", "shape", "dims", "index", "take", "construct"]
)
@pytest.mark.parametrize(
    "error_type",
    [
        ValueError,
        TypeError,
        RuntimeError,
        StopIteration,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ],
)
def test_external_exception_identity_traceback_and_baseexception_propagation(
    *, stage: str, error_type: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    import ospf_python.multiarray.multi_array_view as module

    class Unprintable:
        def __str__(self) -> str:
            pytest.fail("禁止格式化外部异常 / Must not format external exceptions")

    error = type("External", (Unprintable, error_type), {})()

    def fail() -> None:
        raise error

    class Copied:
        def __len__(self) -> int:
            return 12

        @staticmethod
        def take(indices: Any, *, axis: int) -> Any:
            assert axis == 0
            if stage == "take":
                fail()
            return np.arange(len(indices))

    class Data:
        def copy(self) -> Copied:
            if stage == "copy":
                fail()
            return Copied()

    class Shape:
        storage_order = StorageOrder.ROW_MAJOR

        @property
        def dims(self) -> tuple[int, ...]:
            if stage == "dims":
                fail()
            return (3, 4)

        def flat_index(self, *indices: int) -> int:
            if stage == "index":
                fail()
            return indices[0] * 4 + indices[1]

    class Source:
        _data = Data()

        @property
        def shape(self) -> Shape:
            if stage == "shape":
                fail()
            return Shape()

    if stage == "construct":
        monkeypatch.setattr(module, "MultiArray", lambda *args: fail())
    view = MultiArrayView(cast("Any", Source()), offsets=(1, 1))
    if issubclass(error_type, Exception):
        result = view.materialize()
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
        assert result.error.value.error_class == "EXTERNAL_VIEW_MATERIALIZATION"
        assert error.__traceback__ is not None
    else:
        with pytest.raises(error_type) as caught:
            view.materialize()
        assert caught.value is error


def test_copy_precedes_constructor_capture_and_late_source_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ospf_python.multiarray.multi_array_view as module

    events = []
    shape = Shape2(3, 4)
    token = object()

    def chosen(actual_shape: Any, data: Any) -> Any:
        events.append("chosen")
        assert actual_shape is shape and data is token
        return token

    def forbidden(*args: Any) -> Any:
        pytest.fail("构造器须在shape前捕获 / Capture constructor before shape")

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            monkeypatch.setattr(module, "MultiArray", chosen)
            return token

    class Source:
        _data = Data()

        @property
        def shape(self) -> Any:
            events.append("shape")
            monkeypatch.setattr(module, "MultiArray", forbidden)
            return shape

    view = MultiArrayView(cast("Any", Source()), offsets=(0, 0))
    result = view.materialize()
    assert isinstance(result, Ok) and result.value is token
    assert events == ["copy", "shape", "chosen"]


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_old_view_fields_pickle_copy_and_no_persistent_source_cache(
    protocol: int,
) -> None:
    source: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4), np.arange(12))
    view = object.__new__(MultiArrayView)
    vars(view).update(_source=source, _offsets=(1, 1))
    restored = pickle.loads(pickle.dumps(view, protocol=protocol))
    for item in (restored, copy.copy(view), copy.deepcopy(view)):
        result = item.materialize().unwrap()
        assert result.shape.dims == (2, 3) and result._data.tolist() == [
            5,
            6,
            7,
            9,
            10,
            11,
        ]
    source_ref, view_ref = weakref.ref(source), weakref.ref(view)
    result = view.materialize().unwrap()
    del source, view, item
    gc.collect()
    assert source_ref() is None and view_ref() is None
    assert result._data.tolist() == [5, 6, 7, 9, 10, 11]
    assert "return" in get_type_hints(MultiArrayView.materialize)


def test_nonzero_region_checks_axis_zero_and_copy_callbacks_are_lock_free() -> None:
    invalid: MultiArray[int, Shape2] = MultiArray(
        Shape2(3, 4), np.arange(12).reshape((3, 4))
    )
    assert isinstance(MultiArrayView(invalid, offsets=(1, 1)).materialize(), Failed)
    source: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4), np.arange(12))
    view = MultiArrayView(source, offsets=(1, 1))
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda _: view.materialize().unwrap(), range(16)))
    assert all(item._data.tolist() == [5, 6, 7, 9, 10, 11] for item in outputs)
    assert len({id(item._data) for item in outputs}) == 16


@pytest.mark.parametrize("order", _ORDERS)
def test_structured_string_and_zero_dimensional_copy_protocols(
    order: StorageOrder,
) -> None:
    arrays = [
        np.zeros(12, dtype=[("key", "i2"), ("vector", "f8", (2,))]),
        np.array([None, "a", "b"] * 4, dtype=np.dtypes.StringDType(na_object=None)),
    ]
    for data in arrays:
        source: MultiArray[Any, Shape2] = MultiArray(Shape2(3, 4, order), data)
        result = MultiArrayView(source, offsets=(1, 1)).materialize().unwrap()
        assert result._data.dtype == data.dtype and result._data.shape == (6,)
        assert not np.shares_memory(result._data, data)
    scalar: MultiArray[int, DynShape] = MultiArray(DynShape((), order), np.array(7))
    result = MultiArrayView(scalar).materialize().unwrap()
    assert result.shape is scalar.shape and result._data.shape == ()
    assert result._data.item() == 7


def test_copy_rebinding_uses_late_source_shape_and_result_payload_is_data() -> None:
    payload: Any = Failed(Err(ErrorCode.NOT_FOUND, "copy data"))
    replacement: MultiArray[int, Shape2] = MultiArray(Shape2(4, 3), np.arange(12))

    class Data:
        def copy(self) -> Any:
            view._source = replacement
            return payload

    source: MultiArray[Any, Shape2] = MultiArray(Shape2(3, 4), cast("Any", Data()))
    view = MultiArrayView(source)
    result = view.materialize()
    assert isinstance(result, Ok)
    assert result.value.shape is replacement.shape and result.value._data is payload


def test_high_rank_scalar_axes_and_integer_metadata_do_not_recurse() -> None:
    shape = cast("Any", Shape2)(np.int64(3), np.int64(4), StorageOrder.COLUMN_MAJOR)
    source: MultiArray[Any, Any] = MultiArray(shape, np.arange(12))
    view = MultiArrayView(source, offsets=cast("Any", (np.int64(1), np.int64(1))))
    assert view.materialize().unwrap()._data.tolist() == [4, 5, 7, 8, 10, 11]
    source = MultiArray(DynShape((1,) * 1024), np.array([7]))
    result = MultiArrayView(source).materialize().unwrap()
    assert result.shape is source.shape and result._data.tolist() == [7]


@pytest.mark.parametrize("index", [0, -12, True, 12, -13, 1 << 100])
def test_custom_read_aliases_are_valid_but_bool_and_out_of_range_fail(
    index: Any,
) -> None:
    class Custom:
        dims = (3, 4)
        ndim = 2
        storage_order = StorageOrder.COLUMN_MAJOR

        def flat_index(self, *indices: int) -> Any:
            return index

    source: MultiArray[int, Any] = MultiArray(cast("Any", Custom()), np.arange(12))
    result = MultiArrayView(source, offsets=(1, 1)).materialize()
    if type(index) is int and index in (0, -12):
        assert isinstance(result, Ok)
        assert result.value._data.tolist() == [0] * 6
    else:
        assert isinstance(result, Failed)
        expected = (
            ErrorCode.ILLEGAL_ARGUMENT if index is True else ErrorCode.OUT_OF_RANGE
        )
        assert result.error.code is expected


def test_copy_protocol_can_wait_for_reentrant_materialization_on_another_thread() -> (
    None
):
    base: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4), np.arange(12))
    nested = MultiArrayView(base, offsets=(1, 1))

    class Data:
        def copy(self) -> Any:
            with ThreadPoolExecutor(max_workers=1) as pool:
                output = pool.submit(nested.materialize).result(timeout=5).unwrap()
            assert output._data.tolist() == [5, 6, 7, 9, 10, 11]
            return base._data.copy()

    outer: MultiArray[int, Shape2] = MultiArray(base.shape, cast("Any", Data()))
    result = MultiArrayView(outer, offsets=(1, 1)).materialize().unwrap()
    assert result._data.tolist() == [5, 6, 7, 9, 10, 11]
