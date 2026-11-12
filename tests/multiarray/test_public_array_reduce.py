"""公共 live 归约的完整边界合同 / Boundary contracts for public live reduction."""

from __future__ import annotations

import gc
import inspect
import pickle
import weakref
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from typing import Any, get_type_hints

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape, Shape1, Shape2, StorageOrder
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok

_TYPES = (MultiArray, MutableMultiArray)


def _objects(values: list[Any]) -> np.ndarray[Any, Any]:
    data = np.empty(len(values), dtype=object)
    for i, value in enumerate(values):
        data[i] = value
    return data


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", list(StorageOrder))
def test_exact_left_fold_uses_physical_not_logical_order(
    cls: type[Any], order: StorageOrder
) -> None:
    source = cls(Shape2(2, 3, order), np.arange(1, 7))
    calls = []

    def subtract(left: int, right: int) -> int:
        calls.append((left, right))
        return left - right

    assert source.reduce(subtract).unwrap() == -19
    assert calls == [(1, 2), (-1, 3), (-4, 4), (-8, 5), (-13, 6)]
    assert get_type_hints(cls.reduce)["return"] is not int
    assert "for " not in inspect.getsource(cls.reduce)


@pytest.mark.parametrize("cls", _TYPES)
def test_natural_method_delegates_once_without_using_override_iterator(
    cls: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _native._reduce_shared_array
    calls = []

    def native(**kwargs: Any) -> Any:
        calls.append(kwargs)
        return original(**kwargs)

    class Derived(cls):  # type: ignore[misc]
        def __iter__(self) -> Any:
            raise AssertionError(
                "归约不经过迭代覆盖 / Reduction must not use iterator overrides"
            )

    monkeypatch.setattr(_native, "_reduce_shared_array", native)
    source = Derived(Shape1(3), np.array([1, 2, 3]))
    callback = lambda left, right: left + right
    assert source.reduce(callback).unwrap() == 6
    assert len(calls) == 1
    assert calls[0]["owner"] is source and calls[0]["callback"] is callback


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("stride", [1, -1, 2, 0])
def test_strided_views_alias_writes_and_storage_replacement_stay_live(
    cls: type[Any], stride: int
) -> None:
    backing = np.arange(9)
    data = (
        np.lib.stride_tricks.as_strided(backing, shape=(4,), strides=(0,))
        if stride == 0
        else backing[::stride][:4]
    )
    source = cls(Shape1(4), data)
    seen = []

    def callback(left: int, right: int) -> int:
        seen.append(right)
        if len(seen) == 1:
            data[2] = 23
        if len(seen) == 2:
            source._data = np.array([10, 11, 12, 101])
            source._shape = Shape1(1)
        return left + right

    first, second = int(data[0]), int(data[1])
    assert source.reduce(callback).unwrap() == first + second + 23 + 101
    assert seen == [second, 23, 101]


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "values",
    [
        [1 << 300, 1 << 301, -(1 << 299)],
        [Fraction(1, 3), Fraction(2, 7), Fraction(5, 11)],
        [Decimal("0.12"), Decimal("0.34"), Decimal("0.56")],
        [1 + 2j, 3 - 4j, -5j],
        [Quantity(Fraction(i, 7), METER) for i in (1, 2, 3)],
    ],
)
def test_generic_exact_numeric_and_unit_domains_are_not_float_coerced(
    cls: type[Any], values: list[Any]
) -> None:
    source = cls(Shape1(3), _objects(values))

    def add(left: Any, right: Any) -> Any:
        return (left + right).unwrap() if isinstance(left, Quantity) else left + right

    result = source.reduce(add).unwrap()
    assert type(result) is type(values[0])
    assert result == add(add(values[0], values[1]), values[2])


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "leaf",
    [
        None,
        Ok(None),
        Failed(Err(ErrorCode.APPLICATION_ERROR, "叶 / Leaf")),
        np.array([1, 2]),
    ],
)
def test_singleton_and_rank_zero_do_not_call_callback_or_unwrap_data(
    cls: type[Any], leaf: Any
) -> None:
    source = cls(DynShape(()), _objects([leaf]))
    result = source.reduce(None)
    assert isinstance(result, Ok) and result.value is leaf
    source = cls(Shape1(3), _objects([object(), None, leaf]))
    assert source.reduce(lambda left, right: right).unwrap() is leaf


@pytest.mark.parametrize("cls", _TYPES)
def test_opaque_leaf_protocols_do_not_execute(cls: type[Any]) -> None:
    def spoof_class(self: object) -> type:
        raise AssertionError("不读取伪装类型 / Do not read spoofed type")

    class Leaf:
        def item(self) -> Any:
            raise AssertionError("不转换普通叶 / Do not convert opaque leaves")

        def __float__(self) -> float:
            raise AssertionError("不转浮点 / Do not coerce to float")

    leaf = type("PretendScalar", (Leaf,), {"__class__": property(spoof_class)})()
    source = cls(Shape1(2), _objects([leaf, leaf]))
    assert source.reduce(lambda left, right: left).unwrap() is leaf


@pytest.mark.parametrize("cls", _TYPES)
def test_first_scalar_conversion_precedes_size_and_size_is_captured_once(
    cls: type[Any],
) -> None:
    events = []

    class First(np.float64):
        def item(self, *args: Any) -> int:
            events.append("first")
            source._shape = Shape1(2)
            return 7

    class Derived(cls):  # type: ignore[misc]
        @property
        def size(self) -> Any:
            events.append("size")
            return self._shape.size

    source = Derived(Shape1(3), _objects([First(1), 3, 99]))
    assert source.reduce(lambda left, right: left + right).unwrap() == 10
    assert events == ["first", "size"]


def test_replaced_storage_is_not_retained_through_scalar_conversion() -> None:
    events = []

    class Scalar(np.float64):
        def item(self, *args: Any) -> int:
            source._data = np.array([7, 8])
            events.append("converted")
            return 1

    class Data:
        def __getitem__(self, index: int) -> Any:
            return Scalar(1)

        def __del__(self) -> None:
            events.append("released")

    source: MultiArray[int, Shape1] = MultiArray(Shape1(2), np.arange(2))
    source._data = Data()  # type: ignore[assignment]
    assert source.reduce(lambda left, right: left + right).unwrap() == 9
    assert events == ["released", "converted"]


@pytest.mark.parametrize("kind", [ValueError, TypeError, OverflowError, StopIteration])
@pytest.mark.parametrize("phase", ["callback", "read", "size", "scalar"])
def test_external_failures_keep_identity_traceback_and_do_not_format(
    kind: type[Exception], phase: str
) -> None:
    def bad_string(self: object) -> str:
        raise AssertionError("不得格式化外部异常 / Do not format external errors")

    error = type("External", (kind,), {"__str__": bad_string})()
    events = []

    class Scalar(np.float64):
        def item(self, *args: Any) -> Any:
            raise error

    class Data:
        def __getitem__(self, index: int) -> Any:
            events.append(index)
            if phase == "read" and index == 1:
                raise error
            return Scalar(1) if phase == "scalar" else index

    class Derived(MultiArray[Any, Any]):
        @property
        def size(self) -> Any:
            if phase == "size":
                raise error
            return 3

    source = Derived(Shape1(3), np.arange(3))
    source._data = Data()  # type: ignore[assignment]

    def callback(left: Any, right: Any) -> Any:
        raise error

    result = source.reduce(callback)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.APPLICATION_ERROR
    assert result.error.value.error_class == "EXTERNAL_REDUCTION"
    assert result.error.value.callback_exception is error
    assert error.__traceback__ is not None
    assert events == ([0, 1] if phase in ("read", "callback") else [0])


@pytest.mark.parametrize("kind", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_process_control_exceptions_are_not_failed(kind: type[BaseException]) -> None:
    error = kind()

    def callback(left: Any, right: Any) -> Any:
        raise error

    with pytest.raises(kind) as caught:
        MultiArray(Shape1(2), np.arange(2)).reduce(callback)
    assert caught.value is error


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "scalar",
    [
        np.int16(3),
        np.float32(0.5),
        np.clongdouble(1 + 2j),
        np.longdouble("0.1"),
        np.datetime64("2026-10-25"),
        np.timedelta64(3, "D"),
        np.void(b"ab"),
    ],
)
def test_real_numpy_scalar_item_output_type_is_preserved(
    cls: type[Any], scalar: np.generic
) -> None:
    source = cls(Shape1(1), _objects([scalar]))
    actual = source.reduce(None).unwrap()
    expected = scalar.item()
    assert type(actual) is type(expected) and actual == expected


def test_index_protocol_is_called_once_and_empty_storage_is_a_failure() -> None:
    events = []

    class Count:
        def __index__(self) -> int:
            events.append("index")
            return 3

    class Derived(MultiArray[Any, Any]):
        @property
        def size(self) -> Any:
            return Count()

    source = Derived(Shape1(3), np.arange(3))
    assert source.reduce(lambda left, right: left + right).unwrap() == 3
    assert events == ["index"]
    source._data = np.array([])
    failure = source.reduce(lambda left, right: left)
    assert isinstance(failure, Failed)
    assert isinstance(failure.error.value.callback_exception, IndexError)
    assert events == ["index"]


def test_callback_can_wait_for_other_thread_reduction_on_same_source() -> None:
    source: MultiArray[int, Shape1] = MultiArray(Shape1(3), np.array([1, 2, 3]))
    with ThreadPoolExecutor(max_workers=1) as pool:

        def callback(left: int, right: int) -> int:
            assert (
                pool.submit(source.reduce, lambda a, b: a + b)
                .result(timeout=5)
                .unwrap()
                == 6
            )
            return left + right

        assert source.reduce(callback).unwrap() == 6


@pytest.mark.parametrize("count", [-5, 0, 1, True, 1 << 100])
def test_custom_count_contract_and_checked_native_capacity(count: int) -> None:
    class Derived(MultiArray[Any, Any]):
        @property
        def size(self) -> int:
            return count

    source = Derived(Shape1(1), _objects([None]))
    result = source.reduce(None)  # type: ignore[arg-type]
    if count > (1 << 64):
        assert isinstance(result, Failed) and result.error.code is ErrorCode.OVERFLOW
    else:
        assert isinstance(result, Ok) and result.value is None


@pytest.mark.parametrize("cls", _TYPES)
def test_recursive_reentry_and_source_mutation_do_not_deadlock(cls: type[Any]) -> None:
    source = cls(Shape1(3), np.array([1, 2, 3]))
    called = False

    def callback(left: int, right: int) -> int:
        nonlocal called
        if not called:
            called = True
            assert source.reduce(lambda a, b: a + b).unwrap() == 6
            source._data[-1] = 9
        return left + right

    assert source.reduce(callback).unwrap() == 12


@pytest.mark.parametrize("cls", _TYPES)
def test_no_persistent_owner_callback_or_leaf_cache(cls: type[Any]) -> None:
    class Leaf:
        pass

    class Callback:
        def __call__(self, left: Any, right: Any) -> Any:
            return right

    source = cls(Shape1(3), _objects([Leaf(), Leaf(), Leaf()]))
    callback = Callback()
    refs = [weakref.ref(source), weakref.ref(callback), weakref.ref(source._data[0])]
    result = source.reduce(callback)
    del source, callback
    gc.collect()
    assert all(ref() is None for ref in refs)
    assert isinstance(result, Ok) and isinstance(result.value, Leaf)


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_restored_legacy_array_uses_native_reduction(
    cls: type[Any], protocol: int
) -> None:
    source = cls(Shape1(3), np.array([1, 2, 3]))
    restored = pickle.loads(pickle.dumps(source, protocol=protocol))
    assert restored.reduce(lambda left, right: left + right).unwrap() == 6
