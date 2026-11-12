"""原生物化发布与恒等区域边界 / Native materialization publication and identity-region boundaries."""

from __future__ import annotations

import gc
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any, cast

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding import shared_view
from ospf_python.multiarray import (
    DynShape,
    MultiArray,
    MultiArrayView,
    MutableMultiArray,
    Shape2,
    StorageOrder,
)
from ospf_python.multiarray.multi_array_view import _materialized_constructor
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("cropped", [False, True])
@pytest.mark.parametrize("domain", ["i2", ">f8", "object", "string"])
def test_native_publication_matches_the_actual_transport_operation(
    *, storage: type[Any], order: StorageOrder, cropped: bool, domain: str
) -> None:
    dtype = np.dtypes.StringDType() if domain == "string" else np.dtype(domain)
    data = (
        np.array([str(i) + "x" * 80 for i in range(12)], dtype=dtype)
        if domain == "string"
        else np.arange(12).astype(dtype)
    )
    source = storage(Shape2(3, 4, order), data)
    view = MultiArrayView(source, offsets=(1, 1) if cropped else (0, 0))
    actual = view.materialize()
    expected, error = _native._materialize_shared_view(
        owner=view,
        shape_types=shared_view._SHAPE_TYPES,
        row_major=StorageOrder.ROW_MAJOR,
        column_major=StorageOrder.COLUMN_MAJOR,
        make_shape=DynShape,
        resolve=_materialized_constructor,
    )
    assert error is None and expected is not None and isinstance(actual, Ok)
    assert actual.value.shape == expected.shape
    np.testing.assert_array_equal(actual.value._data, expected._data)
    assert actual.value._data.dtype == expected._data.dtype == data.dtype
    assert not np.shares_memory(actual.value._data, expected._data)
    assert vars(view) == {"_source": source, "_offsets": view._offsets}


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize(
    "dims,offsets,code",
    [
        ((0, 4), (0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((-1, 4), (0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((True, 4), (0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((1 << 100, 4), (0, 0), ErrorCode.OVERFLOW),
        ((1 << 62, 4), (0, 0), ErrorCode.OVERFLOW),
        ((np.uint64(2**64 - 1), 4), (0, 0), ErrorCode.OVERFLOW),
        ((3, 4), (0,), ErrorCode.ILLEGAL_ARGUMENT),
        ((3, 4), (0, 0, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((3, 4), (False, 0), ErrorCode.ILLEGAL_ARGUMENT),
        ((3, 4), (-1, 0), ErrorCode.OUT_OF_RANGE),
        ((3, 4), (1 << 100, 0), ErrorCode.OUT_OF_RANGE),
        ((3, 4), [0, 0], ErrorCode.ILLEGAL_ARGUMENT),
        ((3, 4), None, ErrorCode.ILLEGAL_ARGUMENT),
    ],
)
def test_identity_publication_does_not_skip_metadata_validation(
    *, storage: type[Any], dims: Any, offsets: Any, code: ErrorCode
) -> None:
    calls: list[str] = []

    class Data:
        def copy(self) -> Any:
            calls.append("copy")
            return np.arange(12)

    shape = DynShape((3, 4))
    object.__setattr__(shape, "dims", dims)
    source = storage(shape, cast("Any", Data()))
    view = object.__new__(MultiArrayView)
    vars(view).update(_source=source, _offsets=offsets)
    actual = view.materialize()
    assert isinstance(actual, Failed) and actual.error.code is code
    assert calls == ["copy"]
    assert actual.error.value.source == "ospf-python-native"
    assert actual.error.value.callback_exception is None


def test_identity_shape2_fast_path_reads_only_fields_in_legacy_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    token = object()

    class Integer:
        def __init__(self, tag: str, value: int) -> None:
            self.tag, self.value = tag, value

        def __index__(self) -> int:
            events.append("index:" + self.tag)
            return self.value

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            return token

    shape = Shape2(3, 4)

    def d0(self: Shape2) -> Integer:
        events.append("read:d0")
        return Integer("d0", 3)

    def d1(self: Shape2) -> Integer:
        events.append("read:d1")
        return Integer("d1", 4)

    def storage_order(self: Shape2) -> StorageOrder:
        events.append("order")
        return StorageOrder.ROW_MAJOR

    monkeypatch.setattr(Shape2, "d0", property(d0), raising=False)
    monkeypatch.setattr(Shape2, "d1", property(d1), raising=False)
    monkeypatch.setattr(Shape2, "storage_order", property(storage_order))
    monkeypatch.setattr(
        Shape2,
        "dims",
        property(
            lambda self: pytest.fail(
                "快速路径不得读取 dims / Fast path must not read dims"
            )
        ),
    )

    class Source:
        @property
        def _data(self) -> Any:
            events.append("data")
            return Data()

        @property
        def shape(self) -> Shape2:
            events.append("shape")
            return shape

    class Owner:
        @property
        def _source(self) -> Source:
            events.append("source")
            return Source()

        @property
        def _offsets(self) -> tuple[int, int]:
            events.append("offsets")
            return (0, 0)

    def resolve() -> Any:
        events.append("resolve")
        return construct

    def construct(actual_shape: Any, data: Any) -> Any:
        events.append("construct")
        assert actual_shape is shape and data is token
        return token

    actual, error = _native._materialize_shared_view(
        owner=Owner(),
        shape_types=shared_view._SHAPE_TYPES,
        row_major=StorageOrder.ROW_MAJOR,
        column_major=StorageOrder.COLUMN_MAJOR,
        make_shape=DynShape,
        resolve=resolve,
    )
    assert error is None and actual is token
    assert events == [
        "source",
        "data",
        "copy",
        "resolve",
        "source",
        "shape",
        "offsets",
        "read:d0",
        "read:d1",
        "index:d0",
        "index:d1",
        "order",
        "construct",
    ]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("cropped", [False, True])
def test_default_protocol_never_retains_call_owners_or_metadata_instances(
    *, storage: type[Any], order: StorageOrder, cropped: bool
) -> None:
    assert type(shared_view._protocol) is _native._SharedView
    data = np.arange(12)
    shape = Shape2(3, 4, order)
    source = storage(shape, data)
    view = MultiArrayView(source, offsets=(1, 1) if cropped else (0, 0))
    references = [weakref.ref(value) for value in (data, source, view)]
    result = view.materialize().unwrap()
    del data, source, view, shape
    gc.collect()
    assert all(reference() is None for reference in references)
    assert result._data.flags.owndata and result._data.base is None
    assert result.shape.dims == ((2, 3) if cropped else (3, 4))


@pytest.mark.parametrize(
    "field", ["shape_types", "row_major", "column_major", "success", "failure"]
)
def test_every_protocol_configuration_edge_is_gc_visible(field: str) -> None:
    class Configuration:
        protocol: Any

    configured: Any = Configuration if field == "shape_types" else Configuration()
    kwargs: dict[str, Any] = dict(
        shape_types=shared_view._SHAPE_TYPES,
        row_major=StorageOrder.ROW_MAJOR,
        column_major=StorageOrder.COLUMN_MAJOR,
        success=Ok,
        failure=shared_view._native_failure,
    )
    kwargs[field] = (configured,) if field == "shape_types" else configured
    protocol = _native._SharedView(**kwargs)
    configured.protocol = protocol
    configured_ref, protocol_ref = weakref.ref(configured), weakref.ref(protocol)
    assert gc.is_tracked(protocol)
    del protocol, configured, kwargs, Configuration
    gc.collect()
    assert configured_ref() is None and protocol_ref() is None


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("cropped", [False, True])
@pytest.mark.parametrize("outcome", ["none", "object", "failed"])
def test_constructor_return_values_are_wrapped_once_without_interpretation(
    *, order: StorageOrder, cropped: bool, outcome: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ospf_python.multiarray.multi_array_view as module

    sentinel = {
        "none": None,
        "object": object(),
        "failed": Failed(Err(ErrorCode.NOT_FOUND, "值 / Value")),
    }[outcome]
    source: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4, order), np.arange(12))
    view = MultiArrayView(source, offsets=(1, 1) if cropped else (0, 0))
    monkeypatch.setattr(module, "MultiArray", lambda shape, data: sentinel)
    actual = view.materialize()
    assert isinstance(actual, Ok) and actual.value is sentinel


@pytest.mark.parametrize("stage", ["success", "failure"])
@pytest.mark.parametrize(
    "kind",
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
def test_factory_exceptions_keep_identity_and_baseexceptions_propagate(
    *, stage: str, kind: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    error = kind("工厂失败 / Factory failed")

    def fail(value: Any) -> Any:
        raise error

    protocol = _native._SharedView(
        shape_types=shared_view._SHAPE_TYPES,
        row_major=StorageOrder.ROW_MAJOR,
        column_major=StorageOrder.COLUMN_MAJOR,
        success=fail if stage == "success" else Ok,
        failure=fail if stage == "failure" else shared_view._native_failure,
    )
    monkeypatch.setattr(shared_view, "_protocol", protocol)
    shape = DynShape((3, 4))
    if stage == "failure":
        object.__setattr__(shape, "dims", (0, 4))
    source: MultiArray[int, DynShape] = MultiArray(shape, np.arange(12))
    view = MultiArrayView(source, offsets=(0, 0))
    if issubclass(kind, Exception):
        actual = view.materialize()
        assert isinstance(actual, Failed)
        assert actual.error.code is ErrorCode.APPLICATION_ERROR
        assert actual.error.value.callback_exception is error
        assert actual.error.value.error_class == "EXTERNAL_VIEW_MATERIALIZATION"
        assert error.__traceback__ is not None
    else:
        with pytest.raises(kind) as caught:
            view.materialize()
        assert caught.value is error


@pytest.mark.parametrize("order", list(StorageOrder))
def test_result_factory_can_wait_for_another_thread_reentering_the_same_protocol(
    order: StorageOrder, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[bool] = []
    active = False
    source: MultiArray[int, Shape2] = MultiArray(Shape2(3, 4, order), np.arange(12))
    view = MultiArrayView(source, offsets=(1, 1))

    def success(value: Any) -> Any:
        nonlocal active
        calls.append(active)
        if not active:
            active = True
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    nested = pool.submit(view.materialize).result(timeout=5).unwrap()
                np.testing.assert_array_equal(nested._data, value._data)
            finally:
                active = False
        return Ok(value)

    protocol = _native._SharedView(
        shape_types=shared_view._SHAPE_TYPES,
        row_major=StorageOrder.ROW_MAJOR,
        column_major=StorageOrder.COLUMN_MAJOR,
        success=success,
        failure=shared_view._native_failure,
    )
    monkeypatch.setattr(shared_view, "_protocol", protocol)
    actual = view.materialize().unwrap()
    assert actual.shape.dims == (2, 3) and calls == [False, True]
