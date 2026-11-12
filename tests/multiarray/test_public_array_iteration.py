"""公共迭代切换与 scalar 边界合同 / Public iteration cutover and scalar boundary contracts."""

from __future__ import annotations

import copy
import gc
import pickle
import subprocess
import sys
import threading
import types
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape, Shape1, Shape2, StorageOrder
from ospf_python.utils.functional.result import Ok

_TYPES = [MultiArray, MutableMultiArray]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


class _Opaque:
    @property
    def item(self) -> Any:
        raise AssertionError("不得访问普通叶的 item / Do not access ordinary leaf item")

    def __iter__(self) -> Any:
        raise AssertionError("不得遍历普通叶 / Do not iterate ordinary leaves")


def _object_data(values: list[Any]) -> np.ndarray:
    data = np.empty(len(values), dtype=object)
    for i, value in enumerate(values):
        data[i] = value
    return data


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("stride", [1, -2])
def test_public_generator_uses_native_position_and_shared_physical_live_reads(
    *, cls: type[Any], order: StorageOrder, stride: int
) -> None:
    data = np.arange(12)[::stride][:6]
    source = cls(Shape2(2, 3, order), data)
    cursor = iter(source)
    assert isinstance(cursor, types.GeneratorType)
    assert cursor.gi_yieldfrom is None
    assert next(cursor) == data[0]
    assert isinstance(cursor.gi_yieldfrom, _native.SharedArrayIterator)
    data[1] = 101
    assert cursor.send("ignored") == 101
    replacement = np.array([10, 11, 12, 13, 14, 15])
    source._data = replacement
    assert list(cursor) == [12, 13, 14, 15]
    assert cursor.gi_frame is None


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("dims", [(), (1,), (0,), (2, 1, 3)])
def test_scalar_empty_and_rank_follow_public_generator_contract(
    cls: type[Any], dims: tuple[int, ...]
) -> None:
    if dims == (0,):

        class Empty(cls):
            @property
            def size(self) -> int:
                return 0

        source = Empty(Shape1(1), np.array([]))
        expected: list[int] = []
    else:
        shape = DynShape(dims)
        source = cls(shape, np.arange(shape.size))
        expected = list(range(shape.size))
    assert list(source) == expected
    cursor = iter(source)
    cursor.close()
    assert list(cursor) == []


@pytest.mark.parametrize("cls", _TYPES)
def test_count_is_lazy_then_fixed_but_storage_is_reloaded_each_step(
    cls: type[Any],
) -> None:
    source = cls(Shape1(2), np.arange(4))
    cursor = iter(source)
    source._shape = Shape1(3)
    assert next(cursor) == 0
    source._shape = Shape1(1)
    assert list(cursor) == [1, 2]

    class Negative(cls):
        @property
        def size(self) -> int:
            return -1

    assert list(iter(Negative(Shape1(1), np.array([])))) == []


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "scalar",
    [
        np.int8(-1),
        np.uint64(2**63),
        np.float32(1.25),
        np.float64(-0.0),
        np.longdouble("1.5"),
        np.complex128(1 + 2j),
        np.bool_(True),
        np.str_("value"),
        np.bytes_(b"value"),
        np.datetime64("2026-10-25", "D"),
        np.timedelta64(3, "h"),
        np.void(b"ab"),
    ],
)
def test_only_numpy_scalars_use_item_conversion(
    cls: type[Any], scalar: np.generic
) -> None:
    source = cls(Shape1(1), _object_data([scalar]))
    expected = scalar.item()
    from_get = source.get(0)
    from_iter = next(iter(source))
    assert type(from_get) is type(expected) and type(from_iter) is type(expected)
    assert from_get == expected and from_iter == expected


@pytest.mark.parametrize("cls", _TYPES)
def test_opaque_item_objects_and_result_are_data_not_conversion_hooks(
    cls: type[Any],
) -> None:
    leaf, result = _Opaque(), Ok(None)
    source = cls(Shape1(4), _object_data([leaf, None, result, leaf]))
    assert source.get(0) is leaf and source.get(2) is result
    assert all(a is b for a, b in zip(source, [leaf, None, result, leaf], strict=True))
    seen: list[Any] = []
    assert source.reduce(lambda a, b: seen.append(b) or a).unwrap() is leaf
    assert seen == [None, result, leaf]


@pytest.mark.parametrize("cls", _TYPES)
def test_ndarray_leaf_with_item_method_is_not_implicitly_unwrapped(
    cls: type[Any],
) -> None:
    leaf = np.array([7])
    source = cls(Shape1(1), _object_data([leaf]))
    assert source.get(0) is leaf
    assert next(iter(source)) is leaf


@pytest.mark.parametrize("cls", _TYPES)
def test_spoofed_class_is_not_a_numpy_scalar_or_executed_protocol(
    cls: type[Any],
) -> None:
    calls: list[str] = []

    class Pretend:
        @property
        def __class__(self) -> type[Any]:
            calls.append("class")
            return np.float64

        def item(self) -> int:
            calls.append("item")
            return 7

    leaf = Pretend()
    source = cls(Shape1(1), _object_data([leaf]))
    calls.clear()
    assert source.get(0) is leaf and next(iter(source)) is leaf
    assert calls == []


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize("mode", ["exhaust", "close", "throw", "abandon"])
def test_generator_preserves_source_subclass_and_final_yield_lifetime(
    cls: type[Any], mode: str
) -> None:
    class Source(cls):
        pass

    source = Source(Shape1(1), np.array([7]))
    source.extra = _Opaque()
    reference = weakref.ref(source)
    cursor = iter(source)
    del source
    assert reference() is not None
    assert next(cursor) == 7
    assert reference() is not None
    if mode == "exhaust":
        assert list(cursor) == []
    elif mode == "close":
        cursor.close()
    elif mode == "throw":
        error = ValueError("domain error")
        with pytest.raises(ValueError) as caught:
            cursor.throw(error)
        assert caught.value is error
        del caught, error
    else:
        del cursor
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("cls", _TYPES)
def test_resize_or_storage_failure_exhausts_generator_without_stale_pointer(
    cls: type[Any],
) -> None:
    source = cls(Shape1(3), np.arange(3))
    cursor = iter(source)
    assert next(cursor) == 0
    source._data.resize((1,), refcheck=False)
    with pytest.raises(IndexError):
        next(cursor)
    assert list(cursor) == []
    source._data = np.arange(3)
    assert list(cursor) == []
    assert list(source) == [0, 1, 2]


@pytest.mark.parametrize(
    "exception",
    [ValueError("ordinary"), StopIteration("leaf"), KeyboardInterrupt(), SystemExit(7)],
)
def test_native_failure_preserves_original_exception_or_pep479_cause(
    exception: BaseException,
) -> None:
    class Source:
        @property
        def _data(self) -> Any:
            raise exception

    cursor = _native._iterate_shared_array(
        owner=Source(), scalar_type=np.generic, count=1
    )
    with pytest.raises(
        RuntimeError if isinstance(exception, StopIteration) else type(exception)
    ) as caught:
        next(cursor)
    if isinstance(exception, StopIteration):
        assert caught.value.__cause__ is exception
    else:
        assert caught.value is exception
    assert list(cursor) == []


@pytest.mark.parametrize("cls", _TYPES)
@pytest.mark.parametrize(
    "error", [ValueError("scalar error"), StopIteration("scalar stop")]
)
def test_numpy_scalar_subclass_item_retains_exception_and_pep479_contract(
    cls: type[Any], error: Exception
) -> None:
    class Scalar(np.float64):
        def item(self, *args: Any) -> Any:
            raise error

    source = cls(Shape1(1), _object_data([Scalar(1)]))
    cursor = iter(source)
    with pytest.raises(
        RuntimeError if isinstance(error, StopIteration) else ValueError
    ) as caught:
        next(cursor)
    assert (
        caught.value.__cause__ if isinstance(error, StopIteration) else caught.value
    ) is error
    assert list(cursor) == []


def test_reentrant_or_concurrent_native_consumer_fails_busy_without_holding_lock() -> (
    None
):
    entered, release = threading.Event(), threading.Event()

    class Source:
        @property
        def _data(self) -> list[int]:
            entered.set()
            assert release.wait(5)
            with pytest.raises(ValueError, match="executing"):
                next(cursor)
            with pytest.raises(ValueError, match="executing"):
                cursor.close()
            return [7, 8]

    cursor = _native._iterate_shared_array(
        owner=Source(), scalar_type=np.generic, count=2
    )
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(next, cursor)
        assert entered.wait(5)
        try:
            with pytest.raises(ValueError, match="executing"):
                next(cursor)
        finally:
            release.set()
        assert future.result(5) == 7
    assert next(cursor) == 8
    assert list(cursor) == []


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_raw_cursor_and_public_generator_reject_all_pickle_protocols(
    protocol: int,
) -> None:
    source = MultiArray(Shape1(2), np.arange(2))
    public = iter(source)
    assert next(public) == 0
    raw = public.gi_yieldfrom
    for cursor in (public, raw):
        with pytest.raises(TypeError):
            pickle.dumps(cursor, protocol=protocol)
        with pytest.raises(TypeError):
            copy.deepcopy(cursor)
    assert next(public) == 1
    public.close()


def test_direct_owner_generator_cycle_is_collectable() -> None:
    source = MultiArray(Shape1(1), np.array([7]))
    cursor = iter(source)
    assert next(cursor) == 7
    source.cursor = cursor  # type: ignore[attr-defined]
    reference = weakref.ref(source)
    del source, cursor
    gc.collect()
    assert reference() is None


def test_repeated_exhaustion_close_and_abandon_leave_no_live_source_instances() -> None:
    class Source(MultiArray[Any, Any]):
        pass

    references = []
    for index in range(1000):
        source = Source(Shape1(2), np.arange(2))
        references.append(weakref.ref(source))
        cursor = iter(source)
        next(cursor)
        if index % 3 == 0:
            list(cursor)
        elif index % 3 == 1:
            cursor.close()
        del cursor, source
    gc.collect()
    assert all(reference() is None for reference in references)


@pytest.mark.parametrize("mode", ["close", "exhaust", "failure"])
def test_native_owner_destructor_can_wait_for_another_consumer(mode: str) -> None:
    code = """
import os
import threading
directories = [os.add_dll_directory(path) for path in
    os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path] if os.name == 'nt' else []
from ospf_python import _native
import numpy as np
events = []
class Source:
    _data = [7]
    def __del__(self):
        worker = threading.Thread(target=lambda: events.append(next(cursor, 'done')))
        worker.start()
        worker.join(3)
        assert not worker.is_alive()
cursor = _native._iterate_shared_array(owner=Source(), scalar_type=np.generic, count=2 if MODE == 'failure' else 1)
assert next(cursor) == 7
if MODE == 'close':
    cursor.close()
elif MODE == 'exhaust':
    assert next(cursor, 'done') == 'done'
else:
    try:
        next(cursor)
    except IndexError as error:
        error.__traceback__ = None
assert events == ['done'], events
""".replace("MODE", repr(mode))
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code], text=True, capture_output=True, timeout=15
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
