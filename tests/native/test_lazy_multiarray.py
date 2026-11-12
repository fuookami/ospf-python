"""惰性元素映射、源更新与生命周期合同 / Lazy element mapping, source updates and lifecycle contracts."""

from __future__ import annotations

import gc
import itertools
import os
import subprocess
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
import pytest

from ospf_python._binding.multiarray import (
    MappedMultiArrayView,
    MultiArray,
    MutableMultiArray,
)
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Success, Warn

_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]
_KINDS = ["array", "mutable", "view", "mutable-view"]


class _Payload:
    owner: Any = None


def _source(*, kind: str, order: StorageOrder, scalar: bool = False) -> Any:
    dims = () if scalar else (4, 5) if "view" in kind else (2, 3)
    values = list(range(1 if scalar else 20 if "view" in kind else 6))
    cls = MutableMultiArray if "mutable" in kind else MultiArray
    source = cls.create(values=values, shape=DynShape(dims, order)).unwrap()
    if "view" in kind:
        return source.view(
            offsets=() if scalar else (1, 1),
            shape=DynShape(() if scalar else (2, 3), order),
        ).unwrap()
    return source


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("scalar", [False, True])
def test_creation_is_lazy_and_each_access_recomputes(
    *, kind: str, order: StorageOrder, scalar: bool
) -> None:
    source = _source(kind=kind, order=order, scalar=scalar)
    calls = []

    def callback(value: int) -> list[int]:
        calls.append(value)
        return [value]

    mapped = MappedMultiArrayView.create(source=source, callback=callback).unwrap()
    assert mapped.shape.dims == source.shape.dims
    assert mapped.shape.storage_order is order
    assert len(mapped) == len(source)
    assert calls == []
    coordinate = () if scalar else (1, 2)
    first = mapped.at(coordinate).unwrap()
    second = mapped.at(coordinate).unwrap()
    assert first == second == [source.at(coordinate).unwrap()]
    assert first is not second
    assert len(calls) == 2


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("order", _ORDERS)
@pytest.mark.parametrize("access", _ORDERS)
def test_materialization_uses_coordinates_and_preserves_layout(
    *, kind: str, order: StorageOrder, access: StorageOrder
) -> None:
    source = _source(kind=kind, order=order)
    calls = []

    def callback(value: int) -> dict[str, int]:
        calls.append(value)
        return {"input": value}

    mapped = MappedMultiArrayView.create(source=source, callback=callback).unwrap()
    result = mapped.materialize(access_order=access).unwrap()
    assert result.shape.dims == (2, 3)
    assert result.shape.storage_order is order
    assert calls == source.flatten(access_order=access).unwrap()
    for coordinate in itertools.product(range(2), range(3)):
        assert result.at(coordinate).unwrap() == {
            "input": source.at(coordinate).unwrap()
        }
    assert len(calls) == 6


@pytest.mark.parametrize("kind", ["mutable", "mutable-view"])
@pytest.mark.parametrize("order", _ORDERS)
def test_source_updates_are_live_but_materialized_container_is_independent(
    kind: str, order: StorageOrder
) -> None:
    source = _source(kind=kind, order=order)
    mapped = MappedMultiArrayView.create(
        source=source, callback=lambda value: Ok(value * 10)
    ).unwrap()
    snapshot = mapped.materialize().unwrap()
    old = snapshot.at((0, 0)).unwrap()
    source.set(indices=(0, 0), value=99).unwrap()
    assert mapped.at((0, 0)).unwrap() == 990
    assert snapshot.at((0, 0)).unwrap() == old


@pytest.mark.parametrize("operation", ["at", "materialize"])
@pytest.mark.parametrize("stage", [0, 1, 2])
@pytest.mark.parametrize("variant", ["failed", "fatal", "warn", "exception"])
def test_chains_stop_at_original_failure_and_can_retry(
    *, operation: str, stage: int, variant: str
) -> None:
    source = _source(kind="mutable", order=_ORDERS[0])
    original = {
        "failed": Failed(Err(ErrorCode.NOT_FOUND, "领域失败 / Domain failure")),
        "fatal": Fatal((Err(ErrorCode.APPLICATION_ERROR, "致命 / Fatal"),)),
        "warn": Warn(123, Err(ErrorCode.APPLICATION_ERROR, "警告 / Warning")),
    }.get(variant)
    error = ValueError("回调异常 / Callback exception")
    calls: list[int] = []
    failing = True

    def callback(*, position: int, value: int) -> Any:
        calls.append(position)
        if failing and position == stage:
            if variant == "exception":
                raise error
            return original
        return Ok(value + 1)

    mapped: Any = source
    for position in range(3):
        mapped = MappedMultiArrayView.create(
            source=mapped,
            callback=lambda value, position=position: callback(
                position=position, value=value
            ),
        ).unwrap()
    assert mapped._source is source
    assert len(mapped._callbacks) == 3
    assert calls == []
    result = mapped.at((0, 0)) if operation == "at" else mapped.materialize()
    assert isinstance(result, Failed)
    assert calls == list(range(stage + 1))
    context = result.error.value
    assert context.callback_index == 0
    assert context.error_class == "CALLBACK"
    if variant == "exception":
        assert context.callback_exception is error
        assert context.callback_result is None
    else:
        assert context.callback_result is original
        assert context.callback_exception is None
    failing = False
    calls.clear()
    assert mapped.at((0, 0)).unwrap() == 3
    assert calls == [0, 1, 2]


@pytest.mark.parametrize("kind", _KINDS)
def test_result_as_data_none_success_and_mutable_element_identity(kind: str) -> None:
    source = _source(kind=kind, order=_ORDERS[0], scalar=True)
    for value in [None, Ok(None), Success()]:
        mapped = MappedMultiArrayView.create(
            source=source, callback=lambda item, value=value: value
        ).unwrap()
        assert mapped.at(()).is_ok()
        assert mapped.at(()).unwrap() is None
        assert mapped.materialize().unwrap().at(()).unwrap() is None
    payload = Failed(Err(ErrorCode.NOT_FOUND, "元素 / Element"))
    first = MappedMultiArrayView.create(
        source=source, callback=lambda item: Ok(payload)
    ).unwrap()
    seen = []

    def identity(value: Any) -> Any:
        seen.append(value)
        return Ok(value)

    chained = MappedMultiArrayView.create(source=first, callback=identity).unwrap()
    assert chained.at(()).unwrap() is payload
    assert chained.materialize().unwrap().at(()).unwrap() is payload
    assert seen == [payload, payload]


def test_materialization_reports_nonzero_element_ordinal_not_chain_stage() -> None:
    source = _source(kind="array", order=_ORDERS[0])
    first = MappedMultiArrayView.create(
        source=source, callback=lambda value: value + 10
    ).unwrap()
    original = Failed(Err(ErrorCode.NOT_FOUND, "领域失败 / Domain failure"))
    calls = []

    def callback(value: int) -> Any:
        calls.append(value)
        return original if value == 11 else value

    mapped = MappedMultiArrayView.create(source=first, callback=callback).unwrap()
    result = mapped.materialize()
    assert isinstance(result, Failed)
    assert result.error.value.callback_result is original
    assert result.error.value.callback_index == 1
    assert calls == [10, 11]


@pytest.mark.parametrize("kind", _KINDS)
def test_invalid_reads_do_not_invoke_retained_callbacks(kind: str) -> None:
    source = _source(kind=kind, order=_ORDERS[0])
    calls = []
    mapped = MappedMultiArrayView.create(source=source, callback=calls.append).unwrap()
    for coordinate in [(), (0,), (0, 0, 0), (-1, 0), (2, 0), (0, 3), [0, 0]]:
        result = mapped.at(coordinate)
        assert isinstance(result, Failed)
        assert result.error.value.callback_index is None
    assert mapped.materialize(access_order="C").is_failed()
    assert calls == []
    assert MappedMultiArrayView.create(
        source=object(), callback=calls.append
    ).is_failed()
    assert MappedMultiArrayView.create(source=source, callback=None).is_failed()


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("operation", ["at", "materialize"])
def test_process_control_exceptions_remain_protocol_exceptions(
    *, kind: str, exception_type: type[BaseException], operation: str
) -> None:
    source = _source(kind=kind, order=_ORDERS[0])
    error = exception_type("control")

    def callback(value: Any) -> Any:
        raise error

    mapped = MappedMultiArrayView.create(source=source, callback=callback).unwrap()
    with pytest.raises(exception_type) as raised:
        if operation == "at":
            mapped.at((0, 0))
        else:
            mapped.materialize()
    assert raised.value is error
    assert len(source.flatten().unwrap()) == 6


def test_callbacks_are_retained_until_the_last_lazy_view_is_released() -> None:
    class Callback:
        def __call__(self, value: Any) -> Any:
            return value

    payload = _Payload()
    source = MultiArray.create(values=[payload], shape=DynShape((1,))).unwrap()
    callback = Callback()
    references = weakref.ref(payload), weakref.ref(callback)
    mapped = MappedMultiArrayView.create(source=source, callback=callback).unwrap()
    del source, payload, callback
    gc.collect()
    assert all(reference() is not None for reference in references)
    assert mapped.at((0,)).unwrap() is references[0]()
    del mapped
    gc.collect()
    assert all(reference() is None for reference in references)


@pytest.mark.parametrize("retain_error", [False, True])
def test_lazy_callback_source_output_and_traceback_cycles_are_gc_visible(
    retain_error: bool,
) -> None:
    class Callback:
        owner: Any = None

        def __call__(self, value: Any) -> Any:
            if retain_error:
                raise ValueError("外部失败 / External failure")
            return value

    def exercise() -> tuple[weakref.ReferenceType[Any], weakref.ReferenceType[Any]]:
        payload = _Payload()
        source = MutableMultiArray.create(
            values=[payload], shape=DynShape((1,))
        ).unwrap()
        region = source.view(offsets=(0,), shape=DynShape((1,))).unwrap()
        callback = Callback()
        first = MappedMultiArrayView.create(source=region, callback=callback).unwrap()
        mapped = MappedMultiArrayView.create(
            source=first, callback=lambda value: value
        ).unwrap()
        callback.owner = mapped
        payload.owner = mapped.at((0,)) if retain_error else mapped
        return weakref.ref(payload), weakref.ref(callback)

    references = exercise()
    gc.collect()
    assert all(reference() is None for reference in references)


def test_long_chain_is_iterative_without_materializing_intermediate_arrays() -> None:
    source = _source(kind="array", order=_ORDERS[0], scalar=True)
    mapped: Any = source
    for _ in range(1100):
        mapped = MappedMultiArrayView.create(
            source=mapped, callback=lambda value: value + 1
        ).unwrap()
    assert mapped._source is source
    assert mapped.at(()).unwrap() == 1100
    assert mapped.materialize().unwrap().at(()).unwrap() == 1100


def test_batch_materialization_and_at_callbacks_can_reenter_source_without_deadlock() -> (
    None
):
    code = """
import gc, os
directories = []
if os.name == 'nt':
    directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p]
from ospf_python._binding.multiarray import MappedMultiArrayView, MutableMultiArray
from ospf_python.multiarray.shape import DynShape
source = MutableMultiArray.create(values=list(range(6)), shape=DynShape((2, 3))).unwrap()
view = source.view(offsets=(1, 0), shape=DynShape((1, 3))).unwrap()
def callback(value):
    source.set_many([((r,c), 99) for r in range(2) for c in range(3)]).unwrap()
    assert view.at((0,0)).unwrap() == 99
    assert source.map(lambda item: item + 1).unwrap().at((0,0)).unwrap() == 100
    gc.collect()
    return value
mapped = MappedMultiArrayView.create(source=view, callback=callback).unwrap()
assert mapped.materialize().unwrap().flatten().unwrap() == [3,4,5]
assert mapped.at((0,0)).unwrap() == 99
assert source.flatten().unwrap() == [99]*6
print('lazy-reentry-ok')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-X", "dev", "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
        env={**os.environ, "PYTHONMALLOC": "debug"},
    )
    assert "lazy-reentry-ok" in completed.stdout
    assert "Exception ignored" not in completed.stderr


def test_concurrent_materializations_observe_complete_source_slot_batches() -> None:
    source = MutableMultiArray.create(values=[0] * 16, shape=DynShape((4, 4))).unwrap()
    mapped = MappedMultiArrayView.create(
        source=source, callback=lambda value: value
    ).unwrap()

    def exercise(index: int) -> None:
        source.set_many(
            [
                (coordinate, index)
                for coordinate in itertools.product(range(4), repeat=2)
            ]
        ).unwrap()
        values = mapped.materialize().unwrap().flatten().unwrap()
        assert values == [values[0]] * 16

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(exercise, range(100)))


def test_numpy_scalar_inputs_are_not_coerced_by_lazy_mapping() -> None:
    source = MultiArray.from_numpy(
        values=np.array([1, 2], dtype=np.int16), copy=True
    ).unwrap()
    seen = []

    def callback(value: Any) -> Any:
        seen.append(type(value))
        return value

    mapped = MappedMultiArrayView.create(source=source, callback=callback).unwrap()
    assert isinstance(mapped.at((0,)).unwrap(), np.int16)
    assert all(
        isinstance(value, np.int16)
        for value in mapped.materialize().unwrap().flatten().unwrap()
    )
    assert seen == [np.int16] * 3


def test_raw_native_single_mapping_transport_is_structured_and_index_checked() -> None:
    source = _source(kind="array", order=_ORDERS[0])
    value, error = source._handle.mapped_at(
        indices=[0, 0], callback=lambda value: (True, None)
    )
    assert value is None and error is None
    for callback in [lambda value: None, lambda value: (True, 1 / 0)]:
        value, error = source._handle.mapped_at(indices=[0, 0], callback=callback)
        assert value is None and error.error_class == "CALLBACK"
    value, error = source._handle.mapped_at(
        indices=[2, 0], callback=lambda value: (True, 1 / 0)
    )
    assert value is None and error.category == "OUT_OF_RANGE"
