"""公共存储变换候选的协议合同 / Protocol contracts for candidate public storage transforms."""

from __future__ import annotations

import gc
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal, cast

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.multiarray import (
    DynShape,
    MultiArray,
    MutableMultiArray,
    Shape1,
    Shape2,
    StorageOrder,
)
from ospf_python.multiarray import multi_array as array_module
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", ["C", "F"])
@pytest.mark.parametrize("shape", [(), (6,), (2, 3), (1, 2, 3)])
def test_native_reshape_c_publication_owns_data_and_retains_target(
    *, storage: type[Any], order: Literal["C", "F"], shape: tuple[int, ...]
) -> None:
    count = int(np.prod(shape)) if shape else 1
    data = np.array(np.arange(count).reshape(shape), order=order, dtype=">i2")
    target = DynShape((count,), StorageOrder.COLUMN_MAJOR)
    actual = storage(Shape1(7), data).reshape(target).unwrap()
    assert actual.shape is target and actual._data.flags.owndata
    assert actual._data.flags.c_contiguous and actual._data.base is None
    np.testing.assert_array_equal(actual._data, data.ravel(order="C"))
    assert actual._data.dtype == data.dtype and not np.shares_memory(actual._data, data)


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("count", [True, np.int64(2), 1 << 200])
def test_flatten_sparse_metadata_never_allocates_logical_count(
    storage: type[Any], count: Any
) -> None:
    source = storage(Shape1(count), np.arange(6).reshape(2, 3))
    result = source.flatten().unwrap()
    assert result.shape.dims == (count,) and type(result.shape.dims[0]) is type(count)
    assert result._data.shape == (2, 3)
    np.testing.assert_array_equal(result._data, source._data)


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("d0", [0, -1])
def test_standard_shape2_flatten_keeps_nonpositive_failure(
    storage: type[Any], d0: int
) -> None:
    shape = Shape2(2, 3)
    vars(shape)["d0"] = d0
    result = storage(shape, np.arange(6)).flatten()
    assert isinstance(result, Failed)
    assert result.error.code == ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("method", ["reshape", "flatten"])
def test_custom_failures_preserve_original_object_without_formatting(
    *, storage: type[Any], method: str
) -> None:
    class External(ValueError):
        def __str__(self) -> str:
            raise AssertionError("不得格式化 / Must not format")

    error = External()

    class Data:
        def copy(self) -> Any:
            raise error

        def reshape(self, dims: Any) -> Any:
            raise error

    source: Any = storage(Shape1(2), Data())
    result = source.reshape(DynShape((2,))) if method == "reshape" else source.flatten()
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error
    assert result.error.value.error_class == "EXTERNAL_STORAGE_TRANSFORM"
    assert error.__traceback__ is not None


@pytest.mark.parametrize(
    "error_type", [KeyboardInterrupt, SystemExit, GeneratorExit, StopIteration]
)
def test_baseexception_and_direct_stopiteration(
    error_type: type[BaseException],
) -> None:
    error = error_type()

    class Data:
        def copy(self) -> Any:
            raise error

    source: Any = MultiArray(Shape1(1), cast("Any", Data()))
    if error_type is StopIteration:
        result = source.flatten()
        assert (
            isinstance(result, Failed)
            and result.error.value.callback_exception is error
        )
    else:
        with pytest.raises(error_type) as caught:
            source.flatten()
        assert caught.value is error


def test_native_count_and_capacity_fail_before_copy() -> None:
    source: MultiArray[int, Shape1] = MultiArray(Shape1(2), np.arange(6))
    mismatch = source.reshape(DynShape((2,)))
    assert (
        isinstance(mismatch, Failed)
        and mismatch.error.code == ErrorCode.ILLEGAL_ARGUMENT
    )
    overflow = source.reshape(DynShape((1 << 100,)))
    assert isinstance(overflow, Failed) and overflow.error.value.category == "OVERFLOW"


def test_custom_shape_retains_numpy_inference_protocol() -> None:
    class Target:
        dims = (-1, 2)

    source: Any = MultiArray(Shape1(6), np.arange(6))
    target = Target()
    result = source.reshape(target).unwrap()
    assert result.shape is target and result._data.tolist() == list(range(6))


def test_external_shape_never_reads_irrelevant_storage_order() -> None:
    class Target:
        dims = (3, 2)

        @property
        def storage_order(self) -> Any:
            pytest.fail("重塑不读取目标布局 / Reshape must not read target layout")

    source: Any = MultiArray(Shape2(2, 3), np.arange(6))
    assert source.reshape(Target()).unwrap()._data.tolist() == list(range(6))


def test_thread_reentrancy_and_no_persistent_native_owner() -> None:
    class Data:
        def copy(self) -> Any:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future: Any = pool.submit(
                    lambda: (
                        MultiArray(Shape1(2), np.arange(2))
                        .reshape(DynShape((1, 2)))
                        .unwrap()
                    )
                )
                assert future.result(timeout=5)._data.tolist() == [0, 1]
            return np.array([7, 8])

    source: Any = MultiArray(Shape1(2), cast("Any", Data()))
    reference = weakref.ref(source)
    result = source.flatten().unwrap()
    del source
    gc.collect()
    assert reference() is None and result._data.tolist() == [7, 8]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("method", ["reshape", "flatten"])
@pytest.mark.parametrize("domain", ["structured", "strings", "unaligned"])
def test_numpy_c_copy_preserves_descriptors_references_and_unaligned_input(
    *, storage: type[Any], method: str, domain: str
) -> None:
    leaf = object()
    if domain == "structured":
        dtype = np.dtype(
            [("leaf", object), ("number", ">i2"), ("nested", object, (2,))],
            metadata={"marker": leaf},
        )
        data = np.empty((2, 3), dtype=dtype, order="F")
        data["leaf"] = leaf
        data["number"] = np.arange(6).reshape(2, 3)
        data["nested"] = leaf
        data = data[::-1, ::-1]
    elif domain == "strings":
        data = np.array(
            [["first", None, ""], ["longer than inline storage", "last", None]],
            dtype=np.dtypes.StringDType(na_object=None),
            order="F",
        )
    else:
        data = np.ndarray((2, 3), dtype=">i2", buffer=bytearray(13), offset=1)
        data[:] = np.arange(6).reshape(2, 3)
        assert not data.flags.aligned
    data.flags.writeable = False
    source = storage(Shape1(6), data)
    result = (
        source.reshape(DynShape((3, 2))) if method == "reshape" else source.flatten()
    ).unwrap()
    expected = data.ravel(order="C") if method == "reshape" else data
    if domain == "structured":
        np.testing.assert_array_equal(result._data["number"], expected["number"])
    else:
        assert result._data.tolist() == expected.tolist()
    assert result._data.dtype == data.dtype
    assert result._data.flags.owndata and result._data.flags.writeable
    assert result._data.base is None and not np.shares_memory(result._data, data)
    if domain == "structured":
        assert result._data.dtype.metadata is not None
        assert result._data.dtype.metadata["marker"] is leaf
        assert all(value is leaf for value in result._data["leaf"].flat)
        assert all(value is leaf for value in result._data["nested"].flat)


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
def test_flatten_retains_keyword_shape_construction(
    storage: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = DynShape.__init__
    calls: list[tuple[int, ...]] = []

    def construct(self: DynShape, *, dims: tuple[int, ...]) -> None:
        calls.append(dims)
        original(self, dims)

    monkeypatch.setattr(DynShape, "__init__", construct)
    source = storage(Shape1(6), np.arange(6))
    assert source.flatten().unwrap()._data.tolist() == list(range(6))
    assert calls == [(6,)]


def test_c_api_checks_actual_type_independently_of_supplied_type() -> None:
    events: list[str] = []

    class Data:
        def reshape(self, dims: Any) -> Data:
            events.append("reshape")
            return self

        def flatten(self) -> Data:
            events.append("flatten")
            return self

        def copy(self) -> Any:
            events.append("copy")
            return np.arange(2)

    source: Any = MultiArray(Shape1(2), cast("Any", Data()))
    value, failure = _native._transform_storage(
        owner=source,
        target=DynShape((2,)),
        flatten=False,
        types=(Data, DynShape),
        resolve=lambda: MultiArray,
    )
    assert failure is None and value is not None
    assert value._data.tolist() == [0, 1]
    assert events == ["reshape", "flatten", "copy"]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("method", ["reshape", "flatten"])
def test_c_api_copies_release_object_references(
    *, storage: type[Any], method: str
) -> None:
    class Leaf:
        pass

    leaf = Leaf()
    reference = weakref.ref(leaf)
    data: np.ndarray[Any, Any] = np.empty((2, 3), dtype=object, order="F")
    data[:] = leaf
    source = storage(Shape1(6), data)
    target = DynShape((3, 2))
    for _ in range(100):
        result = (
            source.reshape(target) if method == "reshape" else source.flatten()
        ).unwrap()
        assert all(value is leaf for value in result._data.flat)
        del result
    del source, data, leaf
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("method", ["reshape", "flatten"])
@pytest.mark.parametrize("implementation", ["legacy-expression", "native"])
def test_constructor_capture_precedes_copy_argument_evaluation(
    *,
    storage: type[Any],
    method: str,
    implementation: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def captured(shape: Any, data: Any) -> Any:
        events.append("captured")
        return MultiArray(shape, data)

    def late(shape: Any, data: Any) -> Any:
        events.append("late")
        return MultiArray(shape, data)

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            monkeypatch.setattr(array_module, "MultiArray", late)
            return np.arange(2)

        def reshape(self, dims: Any) -> Any:
            events.append("reshape")
            return self

        def flatten(self) -> Any:
            events.append("flatten")
            return self

    source: Any = storage(Shape1(2), cast("Any", Data()))
    target = DynShape((1, 2))
    monkeypatch.setattr(array_module, "MultiArray", captured)
    if implementation == "native":
        result = source.reshape(target) if method == "reshape" else source.flatten()
    elif method == "flatten":
        shape = DynShape(dims=(source.size,))
        result = array_module.MultiArray(shape, source._data.copy())
    elif storage is MutableMultiArray:
        result = array_module.MultiArray(source._shape, source._data.copy()).reshape(
            target
        )
    else:
        data = source._data.reshape(target.dims).flatten()
        result = array_module.MultiArray(target, data.copy())
    value = result.unwrap() if isinstance(result, Result) else result
    assert type(value) is MultiArray and value._data.tolist() == [0, 1]
    assert events == (
        ["copy", "captured"]
        if method == "flatten"
        else ["copy", "captured", "late"]
        if storage is MutableMultiArray
        else ["reshape", "flatten", "copy", "captured"]
    )


@pytest.mark.parametrize("implementation", ["legacy-expression", "native"])
def test_reshape_captures_constructor_after_flatten_but_before_final_copy(
    implementation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []

    def selected(shape: Any, data: Any) -> Any:
        events.append("selected")
        return MultiArray(shape, data)

    def forbidden(shape: Any, data: Any) -> Any:
        pytest.fail(
            "不能在最终copy后重新解析构造器 / Must not resolve constructor after final copy"
        )

    class Data:
        def reshape(self, dims: Any) -> Any:
            return self

        def flatten(self) -> Any:
            monkeypatch.setattr(array_module, "MultiArray", selected)
            return self

        def copy(self) -> Any:
            monkeypatch.setattr(array_module, "MultiArray", forbidden)
            return np.arange(2)

    source: Any = MultiArray(Shape1(2), cast("Any", Data()))
    target = DynShape((2,))
    if implementation == "native":
        value = source.reshape(target).unwrap()
    else:
        data = source._data.reshape(target.dims).flatten()
        value = array_module.MultiArray(target, data.copy())
    assert value._data.tolist() == [0, 1] and events == ["selected"]


def test_protocol_factories_are_gc_visible_without_retaining_call_owners() -> None:
    class Factory:
        protocol: Any

    factory = Factory()
    protocol = _native._StorageTransform(
        types=(np.ndarray, DynShape), success=factory, failure=factory
    )
    factory.protocol = protocol
    factory_ref = weakref.ref(factory)
    protocol_ref = weakref.ref(protocol)
    assert gc.is_tracked(protocol)
    del protocol, factory
    gc.collect()
    assert factory_ref() is None and protocol_ref() is None


def test_flatten_native_failure_keeps_existing_result_and_provenance() -> None:
    class Shape:
        size = 0

    source: Any = MultiArray(cast("Any", Shape()), np.arange(2))
    result = source.flatten()
    assert isinstance(result, Failed)
    assert result.error.code == ErrorCode.ILLEGAL_ARGUMENT
    assert result.error.value.source == "ospf-python-native"
    assert result.error.value.rust_code == 0x34
    assert result.error.value.error_class == "BOUNDARY"


def test_protocol_type_configuration_is_gc_visible() -> None:
    class Shape(DynShape):
        protocol: Any

    protocol = _native._StorageTransform(
        types=(np.ndarray, Shape), success=object, failure=object
    )
    Shape.protocol = protocol
    shape_ref = weakref.ref(Shape)
    protocol_ref = weakref.ref(protocol)
    del Shape, protocol
    gc.collect()
    assert shape_ref() is None and protocol_ref() is None


@pytest.mark.parametrize("outcome", ["ok", "failed", "exception", "interrupt"])
def test_mutable_precopy_dispatches_temporary_owner_reshape(
    outcome: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = DynShape((1, 2))
    reference: MultiArray[int, Shape1] = MultiArray(Shape1(2), np.array([17, 18]))
    expected = reference.reshape(DynShape((3,)) if outcome == "failed" else target)
    error: BaseException = (
        KeyboardInterrupt() if outcome == "interrupt" else ValueError()
    )
    calls: list[Any] = []

    class Temporary(MultiArray[int, Any]):
        def reshape(self, new_shape: DynShape) -> Any:
            calls.append(new_shape)
            assert self._data.tolist() == [0, 1]
            if outcome in ("exception", "interrupt"):
                raise error
            return expected

    source: MutableMultiArray[int, Shape1] = MutableMultiArray(Shape1(2), np.arange(2))
    monkeypatch.setattr(array_module, "MultiArray", Temporary)
    if outcome == "interrupt":
        with pytest.raises(KeyboardInterrupt) as caught:
            source.reshape(target)
        assert caught.value is error
    else:
        result = source.reshape(target)
        if outcome == "exception":
            assert isinstance(result, Failed)
            assert result.error.value.callback_exception is error
        else:
            assert result is expected
    assert calls == [target]


@pytest.mark.parametrize("implementation", ["legacy-expression", "native"])
def test_precopy_releases_captured_callable_before_temporary_reshape(
    implementation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    target = DynShape((1, 2))

    class Temporary(MultiArray[int, Any]):
        def reshape(self, new_shape: DynShape) -> Any:
            assert new_shape is target
            events.append("reshape")
            assert constructor_ref() is None
            return Ok(self)

    class Constructor:
        def __call__(self, shape: Any, data: Any) -> Any:
            events.append("construct")
            return Temporary(shape, data)

        def __del__(self) -> None:
            events.append("release-constructor")

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            # 直接替换避免夹具保活旧 callable。 / Replace directly so the fixture cannot retain the old callable.
            cast("Any", array_module).MultiArray = MultiArray
            return np.arange(2)

    source: Any = MutableMultiArray(Shape1(2), cast("Any", Data()))
    monkeypatch.setattr(array_module, "MultiArray", Constructor())
    constructor_ref = weakref.ref(array_module.MultiArray)
    result = (
        source.reshape(target)
        if implementation == "native"
        else array_module.MultiArray(source._shape, source._data.copy()).reshape(target)
    )
    assert isinstance(result, Ok) and isinstance(result.unwrap(), Temporary)
    assert events == ["copy", "construct", "release-constructor", "reshape"]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("implementation", ["legacy-expression", "native"])
def test_flatten_local_shape_outlives_captured_callable(
    *,
    storage: type[Any],
    implementation: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    sentinel = object()

    class Constructor:
        def __call__(self, shape: Any, data: Any) -> Any:
            events.append("construct")
            return sentinel

        def __del__(self) -> None:
            events.append("release-constructor")

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            cast("Any", array_module).MultiArray = MultiArray
            return np.arange(2)

    def release_shape(self: DynShape) -> None:
        events.append("release-shape")

    def legacy_flatten(owner: Any) -> Any:
        shape = DynShape(dims=(owner.size,))
        return array_module.MultiArray(shape, owner._data.copy())

    source: Any = storage(Shape1(2), cast("Any", Data()))
    monkeypatch.setattr(DynShape, "__del__", release_shape, raising=False)
    monkeypatch.setattr(array_module, "MultiArray", Constructor())
    value = (
        source.flatten().unwrap()
        if implementation == "native"
        else legacy_flatten(source)
    )
    assert value is sentinel
    assert events == ["copy", "construct", "release-constructor", "release-shape"]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("method", ["reshape", "flatten"])
@pytest.mark.parametrize("implementation", ["legacy-expression", "native"])
def test_constructor_and_copy_are_both_released_after_construction(
    *,
    storage: type[Any],
    method: str,
    implementation: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    target = DynShape((1, 2))

    class Copied:
        def __del__(self) -> None:
            events.append("release-copy")

    class Temporary:
        def reshape(self, shape: Any) -> Any:
            assert shape is target
            events.append("reshape")
            return Ok(self)

    class Constructor:
        def __call__(self, shape: Any, data: Any) -> Any:
            events.append("construct")
            return Temporary()

        def __del__(self) -> None:
            events.append("release-constructor")

    class Data:
        def copy(self) -> Any:
            cast("Any", array_module).MultiArray = MultiArray
            return Copied()

        def reshape(self, dims: Any) -> Any:
            return self

        def flatten(self) -> Any:
            return self

    def legacy_transform(owner: Any) -> Any:
        if method == "flatten":
            shape = DynShape(dims=(owner.size,))
            return array_module.MultiArray(shape, owner._data.copy())
        if storage is MutableMultiArray:
            return array_module.MultiArray(owner._shape, owner._data.copy()).reshape(
                target
            )
        data = owner._data.reshape(target.dims).flatten()
        return array_module.MultiArray(target, data.copy())

    source: Any = storage(Shape1(2), cast("Any", Data()))
    monkeypatch.setattr(array_module, "MultiArray", Constructor())
    result = (
        source.reshape(target)
        if implementation == "native" and method == "reshape"
        else source.flatten()
        if implementation == "native"
        else legacy_transform(source)
    )
    value = result.unwrap() if isinstance(result, Result) else result
    assert isinstance(value, Temporary)
    # CPython 3.13 与 3.15 对两个临时对象的销毁次序不同（3.15 先释放 copy 再释放 constructor），
    # 那是解释器实现细节，不是本契约的一部分。这里只断言跨版本成立的不变量：
    # 构造先发生、两个临时对象都被释放、reshape（若适用）发生在最后。
    # The relative order of the two temporaries changed between CPython 3.13 and 3.15 and is an
    # interpreter detail, not part of this contract. Assert only the version-independent
    # invariants: construction first, both temporaries released, reshape last when applicable.
    assert events[0] == "construct"
    releases = sorted(event for event in events if event.startswith("release-"))
    assert releases == ["release-constructor", "release-copy"]
    expects_reshape = method == "reshape" and storage is MutableMultiArray
    assert events.count("reshape") == (1 if expects_reshape else 0)
    if expects_reshape:
        assert events[-1] == "reshape"


@pytest.mark.parametrize("implementation", ["legacy-expression", "native"])
def test_precopy_temporary_arguments_release_after_construction(
    implementation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    target = DynShape((1, 2))

    class Shape:
        def __del__(self) -> None:
            events.append("release-shape")

    class Copied:
        def __del__(self) -> None:
            events.append("release-copy")

    class Temporary:
        def reshape(self, shape: Any) -> Any:
            assert shape is target
            events.append("reshape")
            return Ok(self)

    class Constructor:
        def __call__(self, shape: Any, data: Any) -> Any:
            events.append("construct")
            return Temporary()

        def __del__(self) -> None:
            events.append("release-constructor")

    class Data:
        def copy(self) -> Any:
            cast("Any", array_module).MultiArray = MultiArray
            return Copied()

    class Owner:
        _data = Data()

        @property
        def _shape(self) -> Any:
            return Shape()

    source = Owner()
    monkeypatch.setattr(array_module, "MultiArray", Constructor())
    result = (
        MutableMultiArray.reshape(cast("Any", source), target)
        if implementation == "native"
        else array_module.MultiArray(source._shape, source._data.copy()).reshape(target)
    )
    assert isinstance(result, Ok) and isinstance(result.unwrap(), Temporary)
    # 同上：constructor 与 copy 的相对次序随解释器版本变化，不在此断言。
    # Same as above: the constructor/copy order varies by interpreter version.
    assert events[0] == "construct"
    releases = sorted(event for event in events if event.startswith("release-"))
    assert releases == ["release-constructor", "release-copy", "release-shape"]
    assert events.count("reshape") == 1
    assert events[-1] == "reshape"
