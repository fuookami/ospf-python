"""Rust 数组转置与 Python 回调合同 / Rust array transpose and Python callback contracts."""

from __future__ import annotations

import gc
import itertools
import math
import os
import subprocess
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
import pytest

from ospf_python._binding.multiarray import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Success, Warn

_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]
_KINDS = ["array", "mutable", "view", "mutable-view"]


class _Payload:
    def __init__(self, index: int = 0) -> None:
        self.index = index
        self.owner: object = None


def _subject(
    *, kind: str, dims: tuple[int, ...], order: StorageOrder
) -> tuple[Any, Any, np.ndarray[Any, Any]]:
    source_dims = tuple(d + 2 for d in dims) if "view" in kind else dims
    values = [_Payload(i) for i in range(math.prod(source_dims))]
    array_type = MutableMultiArray if "mutable" in kind else MultiArray
    source = array_type.create(
        values=values, shape=DynShape(source_dims, order)
    ).unwrap()
    oracle = np.empty(len(values), dtype=object)
    oracle[:] = values
    oracle = oracle.reshape(source_dims)
    if "view" in kind:
        subject = source.view(
            offsets=(1,) * len(dims), shape=DynShape(dims, order)
        ).unwrap()
        if dims:
            oracle = oracle[tuple(slice(1, d + 1) for d in dims)]
    else:
        subject = source
    return subject, source, oracle


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("dims", [(), (1,), (5,), (2, 3), (2, 1, 3), (2, 3, 2, 1)])
def test_transpose_reverses_axes_and_layout_preserving_identity(
    *, kind: str, order: StorageOrder, dims: tuple[int, ...]
) -> None:
    subject, source, oracle = _subject(kind=kind, dims=dims, order=order)
    transposed = subject.transpose().unwrap()
    assert isinstance(transposed, MultiArray)
    assert transposed.shape.dims == tuple(reversed(dims))
    assert transposed.shape.storage_order is not order
    expected = oracle.transpose()
    for vector in itertools.product(*(range(d) for d in expected.shape)):
        assert transposed.at(vector).unwrap() is expected[vector]
    twice = transposed.transpose().unwrap()
    assert twice.shape.dims == dims
    assert twice.shape.storage_order is order
    assert all(
        a is b
        for a, b in zip(
            twice.flatten().unwrap(), subject.flatten().unwrap(), strict=True
        )
    )
    if isinstance(source, MutableMultiArray):
        assert source.set_many(
            [
                (v, None)
                for v in itertools.product(*(range(d) for d in source.shape.dims))
            ]
        ).is_ok()
        assert all(
            isinstance(value, _Payload) for value in transposed.flatten().unwrap()
        )
    del source, subject, oracle
    gc.collect()
    assert len(transposed.flatten().unwrap()) == math.prod(dims)


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("storage", _ORDERS)
@pytest.mark.parametrize("access", _ORDERS)
def test_map_order_coordinate_correspondence_and_distinct_output_types(
    *, kind: str, storage: StorageOrder, access: StorageOrder
) -> None:
    subject, _, oracle = _subject(kind=kind, dims=(2, 3), order=storage)
    calls = []

    def callback(value: _Payload) -> dict[str, _Payload]:
        calls.append(value)
        return {"source": value}

    output = subject.map(callback, access_order=access).unwrap()
    expected_calls = oracle.flatten(order="C" if access is _ORDERS[0] else "F")
    assert all(a is b for a, b in zip(calls, expected_calls, strict=True))
    assert output.shape.dims == subject.shape.dims
    assert output.shape.storage_order is storage
    for vector in itertools.product(range(2), range(3)):
        assert output.at(vector).unwrap()["source"] is oracle[vector]
    assert all(isinstance(value, _Payload) for value in subject.flatten().unwrap())


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("storage", _ORDERS)
@pytest.mark.parametrize("access", _ORDERS)
def test_flat_map_uses_explicit_output_shape_and_preserves_duplicate_elements(
    *, kind: str, storage: StorageOrder, access: StorageOrder
) -> None:
    subject, _, oracle = _subject(kind=kind, dims=(2, 3), order=storage)
    calls = []

    def callback(value: _Payload) -> Any:
        calls.append(value)
        return Ok(iter((value, value)))

    output = subject.flat_map(
        callback, shape=DynShape((3, 4), storage), access_order=access
    ).unwrap()
    expected = [
        value
        for item in oracle.flatten(order="C" if access is _ORDERS[0] else "F")
        for value in (item, item)
    ]
    assert output.shape.dims == (3, 4)
    assert output.shape.storage_order is storage
    assert len(calls) == 6
    assert all(
        a is b
        for a, b in zip(
            output.flatten(access_order=access).unwrap(), expected, strict=True
        )
    )
    assert sum(item is expected[0] for item in gc.get_referents(output._handle)) == 2


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("flat", [False, True])
@pytest.mark.parametrize("variant", ["failed", "fatal", "warn"])
def test_callback_results_are_preserved_with_ordinal_and_stop_immediately(
    *, kind: str, flat: bool, variant: str
) -> None:
    subject, _, _ = _subject(kind=kind, dims=(3,), order=_ORDERS[0])
    original = {
        "failed": Failed(Err(ErrorCode.NOT_FOUND, "领域失败 / Domain failure")),
        "fatal": Fatal((Err(ErrorCode.APPLICATION_ERROR, "致命 / Fatal"),)),
        "warn": Warn(
            [None] if flat else None,
            Err(ErrorCode.APPLICATION_ERROR, "警告 / Warning"),
        ),
    }[variant]
    calls = []

    def callback(value: Any) -> Any:
        calls.append(value)
        return original if len(calls) == 2 else ([value] if flat else value)

    result = (
        subject.flat_map(callback, shape=DynShape((3,)))
        if flat
        else subject.map(callback)
    )
    assert isinstance(result, Failed)
    assert len(calls) == 2
    assert result.error.code is ErrorCode.APPLICATION_ERROR
    context = result.error.value
    assert context.callback_result is original
    assert context.callback_index == 1
    assert context.callback_exception is None
    assert context.error_class == "CALLBACK"
    assert context.source == "ospf-python-native"


@pytest.mark.parametrize("kind", _KINDS)
def test_none_success_and_result_payload_escape_are_not_failure_sentinels(
    kind: str,
) -> None:
    subject, _, _ = _subject(kind=kind, dims=(), order=_ORDERS[0])
    for value in (None, Ok(None), Success()):
        output = subject.map(lambda item, value=value: value).unwrap()
        assert output.at(()).is_ok() and output.at(()).unwrap() is None
    payload = Failed(Err(ErrorCode.NOT_FOUND, "作为数据 / As data"))
    output = subject.map(lambda item: Ok(payload)).unwrap()
    assert output.at(()).unwrap() is payload
    assert (
        subject.flat_map(lambda item: Ok([None, payload]), shape=DynShape((2,)))
        .unwrap()
        .at((1,))
        .unwrap()
        is payload
    )


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("flat", [False, True])
def test_callback_exception_preserves_original_and_partial_outputs_are_released(
    *, kind: str, flat: bool
) -> None:
    class CallbackError(ValueError):
        def __str__(self) -> str:
            raise AssertionError("must not format user exception")

    subject, _, _ = _subject(kind=kind, dims=(3,), order=_ORDERS[0])
    error = CallbackError("callback")
    references = []
    calls = []

    def callback(value: Any) -> Any:
        calls.append(value)
        if len(calls) == 2:
            raise error
        payload = _Payload()
        references.append(weakref.ref(payload))
        return [payload] if flat else payload

    result = (
        subject.flat_map(callback, shape=DynShape((3,)))
        if flat
        else subject.map(callback)
    )
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error
    assert result.error.value.callback_index == 1
    assert result.error.value.error_class == "CALLBACK"
    assert len(calls) == 2
    gc.collect()
    assert all(reference() is None for reference in references)


@pytest.mark.parametrize("kind", _KINDS)
def test_flat_map_iterator_failures_and_count_mismatches_are_atomic(kind: str) -> None:
    subject, _, _ = _subject(kind=kind, dims=(3,), order=_ORDERS[0])
    error = RuntimeError("iterator failed")

    def broken() -> Any:
        yield _Payload()
        raise error

    original = Ok(broken())
    result = subject.flat_map(lambda item: original, shape=DynShape((3,)))
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error
    assert result.error.value.callback_result is original
    assert result.error.value.callback_index == 0
    calls = []

    def too_many(value: Any) -> list[Any]:
        calls.append(value)
        return [value, value]

    assert subject.flat_map(too_many, shape=DynShape((1,))).is_failed()
    assert len(calls) == 1
    for part in [[], [None]]:
        result = subject.flat_map(lambda item, part=part: part, shape=DynShape((4,)))
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert result.error.value.callback_index is None
    assert len(subject.flatten().unwrap()) == 3


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("flat", [False, True])
def test_process_control_exceptions_propagate_without_business_wrapping(
    *, kind: str, exception_type: type[BaseException], flat: bool
) -> None:
    subject, _, _ = _subject(kind=kind, dims=(2,), order=_ORDERS[0])
    error = exception_type("control")

    def callback(value: Any) -> Any:
        raise error

    with pytest.raises(exception_type) as raised:
        if flat:
            subject.flat_map(callback, shape=DynShape((2,)))
        else:
            subject.map(callback)
    assert raised.value is error
    assert len(subject.flatten().unwrap()) == 2


@pytest.mark.parametrize("kind", _KINDS)
def test_preflight_failures_do_not_invoke_callbacks(kind: str) -> None:
    subject, _, _ = _subject(kind=kind, dims=(2,), order=_ORDERS[0])
    calls = []

    def callback(value: Any) -> list[Any]:
        calls.append(value)
        return [value]

    for shape in [None, object(), DynShape((sys.maxsize + 1,))]:
        assert subject.flat_map(callback, shape=shape).is_failed()
    assert subject.map(callback, access_order="C").is_failed()
    assert subject.flat_map(
        callback, shape=DynShape((2,)), access_order=None
    ).is_failed()
    assert subject.map(None).is_failed()
    assert subject.flat_map(None, shape=DynShape((2,))).is_failed()
    assert calls == []


def test_native_callback_transport_errors_are_structured_but_interrupts_propagate() -> (
    None
):
    source = MultiArray.create(values=[1, 2], shape=DynShape((2,))).unwrap()
    for callback in (
        lambda value: None,
        lambda value: (False, None),
        lambda value: (True, 1 / 0),
    ):
        value, error = source._handle.mapped(callback=callback, column_major=False)
        assert value is None and error.error_class == "CALLBACK"
    value, error = source._handle.mapped(
        callback=lambda value: (True, (1,)),
        column_major=False,
        output_shape=source.shape._handle,
    )
    assert value is None and error.error_class == "CALLBACK"


def test_callback_lifetime_and_output_cycles_are_gc_visible() -> None:
    class Callback:
        def __call__(self, value: Any) -> _Payload:
            return _Payload()

    source = MultiArray.create(values=[None], shape=DynShape((1,))).unwrap()
    callback = Callback()
    reference = weakref.ref(callback)
    output = source.map(callback).unwrap()
    payload = output.at((0,)).unwrap()
    payload_reference = weakref.ref(payload)
    payload.owner = output
    del callback, source, payload, output
    gc.collect()
    assert reference() is None
    assert payload_reference() is None


@pytest.mark.parametrize("flat", [False, True])
def test_retained_callback_traceback_cycles_can_be_collected(flat: bool) -> None:
    def exercise() -> tuple[weakref.ReferenceType[Any], weakref.ReferenceType[Any]]:
        payload = _Payload()
        source = MultiArray.create(values=[payload], shape=DynShape((1,))).unwrap()

        def callback(value: Any) -> Any:
            assert source.at((0,)).unwrap() is value
            raise ValueError("外部回调失败 / External callback failure")

        result = (
            source.flat_map(callback, shape=DynShape((1,)))
            if flat
            else source.map(callback)
        )
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception.__traceback__ is not None
        payload.owner = result
        return weakref.ref(payload), weakref.ref(callback)

    references = exercise()
    gc.collect()
    assert all(reference() is None for reference in references)


def test_reentrant_callbacks_mutate_sources_but_outer_maps_use_slot_snapshots() -> None:
    code = """
import gc, os
directories = []
if os.name == 'nt':
    directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p]
from ospf_python._binding.multiarray import MutableMultiArray
from ospf_python.multiarray.shape import DynShape
source = MutableMultiArray.create(values=list(range(6)), shape=DynShape((2, 3))).unwrap()
view = source.view(offsets=(1, 0), shape=DynShape((1, 3))).unwrap()
def callback(value):
    assert source.set_many([((r, c), 99) for r in range(2) for c in range(3)]).is_ok()
    assert source.map(lambda item: item + 1).unwrap().flatten().unwrap() == [100] * 6
    assert view.transpose().unwrap().flatten().unwrap() == [99] * 3
    gc.collect()
    return value
assert view.map(callback).unwrap().flatten().unwrap() == [3, 4, 5]
assert source.flatten().unwrap() == [99] * 6
source.set_many([((r, c), r * 3 + c) for r in range(2) for c in range(3)]).unwrap()
assert view.flat_map(lambda value: [callback(value), value], shape=DynShape((2, 3))).unwrap().flatten().unwrap() == [3, 3, 4, 4, 5, 5]
print('mapping-reentry-ok')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-X", "dev", "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
        env={**os.environ, "PYTHONMALLOC": "debug"},
    )
    assert "mapping-reentry-ok" in completed.stdout
    assert "Exception ignored" not in completed.stderr


def test_concurrent_mapping_and_batch_writes_keep_consistent_slot_snapshots() -> None:
    source = MutableMultiArray.create(values=[0] * 16, shape=DynShape((4, 4))).unwrap()

    def run(index: int) -> None:
        assert source.set_many(
            [(v, index) for v in itertools.product(range(4), repeat=2)]
        ).is_ok()
        output = source.map(lambda value: value).unwrap().flatten().unwrap()
        assert all(value == output[0] for value in output)
        if index % 20 == 0:
            gc.collect()

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(run, range(200)))
