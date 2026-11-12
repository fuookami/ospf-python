"""Rust 归约、嵌套转换与显式快照迭代合同 / Rust fold, nested conversion and explicit snapshot iterator contracts."""

from __future__ import annotations

import gc
import itertools
import math
import os
import subprocess
import sys
import weakref
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from typing import Any

import numpy as np
import pytest

from ospf_python._binding.multiarray import MultiArray, MutableMultiArray, Shape
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Success, Warn

_KINDS = ["array", "mutable", "view", "mutable-view"]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


class _Payload:
    owner: Any = None


def _subject(
    *, kind: str, dims: tuple[int, ...], order: StorageOrder
) -> tuple[Any, Any, np.ndarray[Any, Any]]:
    source_dims = tuple(dim + 2 for dim in dims) if "view" in kind else dims
    values = list(range(math.prod(source_dims)))
    cls = MutableMultiArray if "mutable" in kind else MultiArray
    owner = cls.create(values=values, shape=DynShape(source_dims, order)).unwrap()
    oracle = np.array(values, dtype=object).reshape(source_dims)
    if "view" not in kind:
        return owner, owner, oracle
    subject = owner.view(offsets=(1,) * len(dims), shape=DynShape(dims, order)).unwrap()
    if dims:
        oracle = oracle[tuple(slice(1, dim + 1) for dim in dims)]
    return subject, owner, oracle


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (5,), (2, 3), (2, 1, 3), (2, 1, 2, 3)])
def test_nested_conversion_matches_logical_coordinates_not_physical_storage(
    *, kind: str, order: StorageOrder, dims: tuple[int, ...]
) -> None:
    subject, _, oracle = _subject(kind=kind, dims=dims, order=order)
    result = subject.to_list().unwrap()
    assert result == oracle.tolist()
    if dims:
        assert type(result) is list
        result[0] = "only-change-returned-container"
        assert subject.at((0,) * len(dims)).unwrap() == oracle[(0,) * len(dims)]
        assert subject.to_list().unwrap() == oracle.tolist()


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("storage", _ORDERS)
@pytest.mark.parametrize("access", _ORDERS)
def test_reduction_is_left_associative_in_explicit_access_order(
    *, kind: str, storage: StorageOrder, access: StorageOrder
) -> None:
    subject, _, oracle = _subject(kind=kind, dims=(2, 3), order=storage)
    values = list(oracle.flatten(order="C" if access is _ORDERS[0] else "F"))
    calls = []

    def operation(left: int, right: int) -> Any:
        calls.append((left, right))
        return Ok(left * 31 + right)

    result = subject.reduce(operation, access_order=access).unwrap()
    assert result == reduce(lambda left, right: left * 31 + right, values)
    assert len(calls) == len(values) - 1
    assert [right for _, right in calls] == values[1:]
    assert calls[0][0] == values[0]


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("order", _ORDERS)
def test_singleton_reduction_returns_original_data_without_callback(
    kind: str, order: StorageOrder
) -> None:
    original_failure = Failed(Err(ErrorCode.NOT_FOUND, "作为数据 / As data"))
    for value in [None, original_failure, Ok(None), Success(), [], _Payload()]:
        cls = MutableMultiArray if "mutable" in kind else MultiArray
        owner = cls.create(values=[value], shape=DynShape((), order)).unwrap()
        subject = (
            owner.view(offsets=(), shape=DynShape((), order)).unwrap()
            if "view" in kind
            else owner
        )
        calls = []
        assert (
            subject.reduce(
                lambda left, right, *, calls=calls: calls.append(right)
            ).unwrap()
            is value
        )
        assert subject.to_list().unwrap() is value
        assert list(subject.iter_snapshot().unwrap())[0] is value
        assert calls == []
        assert subject.reduce(None).is_failed()


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("variant", ["failed", "fatal", "warn", "exception"])
def test_failed_reduction_preserves_identity_and_never_publishes_partial_accumulator(
    kind: str, variant: str
) -> None:
    subject, _, _ = _subject(kind=kind, dims=(2, 3), order=_ORDERS[0])
    originals = {
        "failed": Failed(Err(ErrorCode.NOT_FOUND, "领域失败 / Domain failure")),
        "fatal": Fatal((Err(ErrorCode.APPLICATION_ERROR, "致命 / Fatal"),)),
        "warn": Warn(123, Err(ErrorCode.APPLICATION_ERROR, "警告 / Warning")),
    }

    class CallbackError(ValueError):
        def __str__(self) -> str:
            raise AssertionError("must not format external exception")

    error = CallbackError("reduction")
    calls = []
    references = []

    def operation(left: Any, right: Any) -> Any:
        calls.append(right)
        if len(calls) == 1:
            provisional = _Payload()
            references.append(weakref.ref(provisional))
            return provisional
        if variant == "exception":
            raise error
        return originals[variant]

    result = subject.reduce(operation)
    assert isinstance(result, Failed)
    assert len(calls) == 2
    assert result.error.value.callback_index == 1
    assert result.error.value.error_class == "CALLBACK"
    if variant == "exception":
        assert result.error.value.callback_exception is error
        assert result.error.value.callback_result is None
        # 失败调用的参数按 Python traceback 规则保留，显式解除后应释放。 / Failed call arguments follow Python traceback retention and release when cleared.
        error.__traceback__ = None
    else:
        assert result.error.value.callback_result is originals[variant]
        assert result.error.value.callback_exception is None
    gc.collect()
    assert all(reference() is None for reference in references)


def test_none_accumulator_and_single_layer_result_escape() -> None:
    source = MultiArray.create(values=[None, 1, 2], shape=DynShape((3,))).unwrap()
    assert source.reduce(lambda left, right: None).is_ok()
    assert source.reduce(lambda left, right: None).unwrap() is None
    payload = Failed(Err(ErrorCode.NOT_FOUND, "作为数据 / As data"))
    calls = []

    def callback(left: Any, right: Any) -> Any:
        calls.append(left)
        return Ok(payload)

    assert source.reduce(callback).unwrap() is payload
    assert calls[0] is None and calls[1] is payload


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_process_control_exceptions_are_not_business_results(
    *, kind: str, exception_type: type[BaseException]
) -> None:
    subject, _, _ = _subject(kind=kind, dims=(2, 3), order=_ORDERS[0])
    error = exception_type("control")

    def callback(left: Any, right: Any) -> Any:
        raise error

    with pytest.raises(exception_type) as raised:
        subject.reduce(callback)
    assert raised.value is error
    assert len(subject.flatten().unwrap()) == 6


@pytest.mark.parametrize("kind", _KINDS)
def test_preflight_failures_do_not_invoke_callbacks(kind: str) -> None:
    subject, _, _ = _subject(kind=kind, dims=(2, 3), order=_ORDERS[0])
    calls = []
    assert subject.reduce(
        lambda left, right: calls.append(right), access_order="C"
    ).is_failed()
    assert subject.reduce(None).is_failed()
    assert subject.iter_snapshot(access_order="C").is_failed()
    assert calls == []


def test_nested_containers_preserve_hostile_leaf_identity_without_protocol_calls() -> (
    None
):
    class Hostile:
        def __iter__(self) -> Any:
            raise AssertionError("must not iterate a leaf")

        def __len__(self) -> int:
            raise AssertionError("must not measure a leaf")

        def item(self) -> Any:
            raise AssertionError("must not coerce a leaf")

    payload = Hostile()
    leaf_list = [payload]
    source = MutableMultiArray.create(
        values=[payload, leaf_list, None, payload],
        shape=DynShape((2, 2), _ORDERS[1]),
    ).unwrap()
    result = source.to_list().unwrap()
    assert result[0][0] is payload and result[0][1] is leaf_list
    assert result[1][0] is None and result[1][1] is payload
    assert result[0] is not result[1]
    source.set(indices=(0, 0), value=None).unwrap()
    assert result[0][0] is payload


@pytest.mark.parametrize("dtype", [np.int16, np.float32, np.complex64])
def test_nested_output_does_not_coerce_numpy_scalars(dtype: Any) -> None:
    source = MultiArray.from_numpy(
        values=np.arange(6).reshape(2, 3).astype(dtype),
        copy=True,
        storage_order=_ORDERS[1],
    ).unwrap()
    result = source.to_list().unwrap()
    for coordinate in itertools.product(range(2), range(3)):
        row, col = coordinate
        assert type(result[row][col]) is dtype
        assert result[row][col] is source.at(coordinate).unwrap()


def test_deep_singleton_axes_are_converted_iteratively() -> None:
    payload = _Payload()
    source = MultiArray.create(
        values=[payload], shape=Shape.create(dims=(1,) * 1100).unwrap()
    ).unwrap()
    nested = source.to_list().unwrap()
    for _ in range(1100):
        assert type(nested) is list and len(nested) == 1
        nested = nested[0]
    assert nested is payload


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("storage", _ORDERS)
@pytest.mark.parametrize("access", _ORDERS)
def test_iterators_are_explicit_independent_slot_snapshots(
    *, kind: str, storage: StorageOrder, access: StorageOrder
) -> None:
    subject, owner, oracle = _subject(kind=kind, dims=(2, 3), order=storage)
    iterator = subject.iter_snapshot(access_order=access).unwrap()
    assert iter(iterator) is iterator
    if isinstance(owner, MutableMultiArray):
        owner.set_many(
            [
                (coordinate, 99)
                for coordinate in itertools.product(
                    *(range(dim) for dim in owner.shape.dims)
                )
            ]
        ).unwrap()
    assert list(iterator) == list(
        oracle.flatten(order="C" if access is _ORDERS[0] else "F")
    )
    with pytest.raises(StopIteration):
        next(iterator)


def test_snapshot_iterator_keeps_elements_only_until_exhaustion_and_cycles_collect() -> (
    None
):
    def exercise(*, cycle: bool) -> tuple[Any, weakref.ReferenceType[Any]]:
        payload = _Payload()
        source = MultiArray.create(values=[payload], shape=DynShape((1,))).unwrap()
        iterator = source.iter_snapshot().unwrap()
        if cycle:
            payload.owner = iterator
        return iterator, weakref.ref(payload)

    iterator, reference = exercise(cycle=False)
    gc.collect()
    assert reference() is not None
    deque(iterator, maxlen=0)
    gc.collect()
    assert reference() is None
    iterator, reference = exercise(cycle=True)
    del iterator
    gc.collect()
    assert reference() is None


def test_reduction_exception_traceback_and_accumulator_cycles_collect() -> None:
    def exercise() -> weakref.ReferenceType[Any]:
        payload = _Payload()
        source = MultiArray.create(
            values=[payload, None], shape=DynShape((2,))
        ).unwrap()

        def callback(left: Any, right: Any) -> Any:
            assert source.at((0,)).unwrap() is left
            raise ValueError("外部失败 / External failure")

        payload.owner = source.reduce(callback)
        return weakref.ref(payload)

    reference = exercise()
    gc.collect()
    assert reference() is None


def test_reentrant_reduction_and_failed_accumulator_finalizer_do_not_hold_source_lock() -> (
    None
):
    code = """
import gc, os
directories = []
if os.name == 'nt':
    directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p]
from ospf_python._binding.multiarray import MutableMultiArray
from ospf_python.multiarray.shape import DynShape
from ospf_python.utils.functional.result import Failed
from ospf_python.utils.error.error import Err
from ospf_python.utils.error.code import ErrorCode
source = MutableMultiArray.create(values=list(range(6)),shape=DynShape((2,3))).unwrap()
view = source.view(offsets=(1,0),shape=DynShape((1,3))).unwrap()
before = view.iter_snapshot().unwrap()
def callback(left,right):
    source.set_many([((r,c),99) for r in range(2) for c in range(3)]).unwrap()
    assert source.to_list().unwrap() == [[99]*3,[99]*3]
    assert view.reduce(lambda a,b:a+b).unwrap() == 297
    gc.collect()
    return left*10+right
assert view.reduce(callback).unwrap() == 345
assert list(before) == [3,4,5]
events=[]
class Accumulator:
    def __del__(self):
        source.set(indices=(0,0),value=88).unwrap()
        assert source.to_list().unwrap()[0][0] == 88
        assert source.reduce(lambda a,b:a+b).unwrap() == 88+99*5
        events.append('released-unlocked')
count=0
def failing(left,right):
    global count
    count+=1
    return Accumulator() if count==1 else Failed(Err(ErrorCode.NOT_FOUND,'failure'))
assert source.reduce(failing).is_failed()
gc.collect()
assert events == ['released-unlocked']
print('fold-reentry-ok')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-X", "dev", "-c", code],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env={**os.environ, "PYTHONMALLOC": "debug"},
    )
    assert "fold-reentry-ok" in completed.stdout
    assert "Exception ignored" not in completed.stderr


def test_concurrent_folds_nested_conversion_and_iterators_observe_atomic_slot_batches() -> (
    None
):
    source = MutableMultiArray.create(values=[0] * 16, shape=DynShape((4, 4))).unwrap()

    def exercise(index: int) -> None:
        source.set_many(
            [
                (coordinate, index)
                for coordinate in itertools.product(range(4), repeat=2)
            ]
        ).unwrap()
        assert source.reduce(lambda a, b: a + b).unwrap() % 16 == 0
        nested = list(itertools.chain.from_iterable(source.to_list().unwrap()))
        assert nested == [nested[0]] * 16
        values = list(source.iter_snapshot().unwrap())
        assert values == [values[0]] * 16

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(exercise, range(100)))


def test_raw_native_reduction_transport_failure_is_structured() -> None:
    source = MultiArray.create(values=[1, 2], shape=DynShape((2,))).unwrap()
    for callback in [
        lambda pair: None,
        lambda pair: (False, None),
        lambda pair: (True, 1 / 0),
    ]:
        value, error = source._handle.reduced(callback=callback, column_major=False)
        assert value is None and error.error_class == "CALLBACK"
