"""数组逻辑比较、快照及扩展点合同 / Logical array comparison, snapshots and extension-point contracts."""

from __future__ import annotations

import copy
import gc
import os
import subprocess
import sys
import threading
import weakref
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.multiarray import (
    MappedMultiArrayView,
    MultiArray,
    MutableMultiArray,
)
from ospf_python._binding.numeric import Rational
from ospf_python.multiarray.shape import DynShape, Shape2, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Success, Warn

_KINDS = ["immutable", "mutable", "immutable-view", "mutable-view"]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


def _subject(
    *, kind: str, data: Any, dims: tuple[int, ...], order: StorageOrder
) -> Any:
    cls = MutableMultiArray if kind.startswith("mutable") else MultiArray
    subject = cls.from_list(data=data, shape=DynShape(dims, order)).unwrap()
    if kind.endswith("view"):
        return subject.view(offsets=(0,) * len(dims), shape=subject.shape).unwrap()
    return subject


class _Payload:
    owner: Any = None


class _Truthy:
    def __bool__(self) -> bool:
        raise AssertionError(
            "不得隐式判断非布尔结果 / Must not truth-test non-boolean output"
        )


@pytest.mark.parametrize("left_kind", _KINDS)
@pytest.mark.parametrize("right_kind", _KINDS)
@pytest.mark.parametrize("left_order", _ORDERS)
@pytest.mark.parametrize("right_order", _ORDERS)
def test_logical_equality_crosses_storage_kinds_and_layouts(
    *,
    left_kind: str,
    right_kind: str,
    left_order: StorageOrder,
    right_order: StorageOrder,
) -> None:
    left = _subject(
        kind=left_kind, data=[[0, 1, 2], [3, 4, 5]], dims=(2, 3), order=left_order
    )
    right = _subject(
        kind=right_kind,
        data=[[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]],
        dims=(2, 3),
        order=right_order,
    )
    assert left.equals(right).unwrap() is True
    assert right.equals(left).unwrap() is True
    assert left is not right and left != right


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("order", _ORDERS)
def test_storage_byte_order_is_not_logical_equality(
    kind: str, order: StorageOrder
) -> None:
    cls = MutableMultiArray if kind.startswith("mutable") else MultiArray
    left = cls.create(
        values=list(range(6)), shape=Shape2(2, 3, order), access_order=order
    ).unwrap()
    other_order = _ORDERS[1] if order is _ORDERS[0] else _ORDERS[0]
    right = cls.create(
        values=list(range(6)), shape=Shape2(2, 3, other_order), access_order=other_order
    ).unwrap()
    if kind.endswith("view"):
        left = left.view(offsets=(0, 0), shape=left.shape).unwrap()
        right = right.view(offsets=(0, 0), shape=right.shape).unwrap()
    assert left.equals(right).unwrap() is False


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("leaf", [None, 1, "text", np.int16(1)])
def test_scalar_has_one_comparison_not_a_zero_iteration_shortcut(
    kind: str, leaf: Any
) -> None:
    left = _subject(kind=kind, data=leaf, dims=(), order=_ORDERS[0])
    calls = []
    assert left.equals(
        left, comparator=lambda a, b: calls.append((a, b)) or True
    ).unwrap()
    assert len(calls) == 1 and calls[0][0] is leaf and calls[0][1] is leaf


@pytest.mark.parametrize("kind", _KINDS)
def test_nan_nonreflexivity_and_signed_zero_follow_value_protocol(kind: str) -> None:
    nan = float("nan")
    subject = _subject(kind=kind, data=[nan], dims=(1,), order=_ORDERS[0])
    assert subject.equals(subject).unwrap() is False
    positive = _subject(kind=kind, data=[0.0], dims=(1,), order=_ORDERS[0])
    negative = _subject(kind=kind, data=[-0.0], dims=(1,), order=_ORDERS[1])
    assert positive.equals(negative).unwrap() is True
    assert hash(positive) == object.__hash__(positive)


@pytest.mark.parametrize("kind", _KINDS)
def test_shape_mismatch_never_calls_user_code_but_comparator_is_validated(
    kind: str,
) -> None:
    left = _subject(kind=kind, data=[[1, 2]], dims=(1, 2), order=_ORDERS[0])
    right = MultiArray.from_list(data=[1, 2], shape=DynShape((2,))).unwrap()

    def forbidden(a: Any, b: Any) -> Any:
        raise AssertionError("不应比较不同形状 / Must not compare different shapes")

    assert left.equals(right, comparator=forbidden).unwrap() is False
    assert left.equals(right, comparator=None).is_failed()


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("variant", ["failed", "fatal", "warn"])
def test_original_result_and_callback_ordinal_survive_short_circuit(
    kind: str, variant: str
) -> None:
    left = _subject(kind=kind, data=[1, 2, 3], dims=(3,), order=_ORDERS[0])
    result = {
        "failed": Failed(Err(ErrorCode.NOT_FOUND, "domain")),
        "fatal": Fatal((Err(ErrorCode.APPLICATION_ERROR, "fatal"),)),
        "warn": Warn(True, Err(ErrorCode.APPLICATION_ERROR, "warn")),
    }[variant]
    calls = []

    def comparator(a: Any, b: Any) -> Any:
        calls.append((a, b))
        return result if len(calls) == 2 else Ok(np.bool_(True))

    failed = left.equals(left, comparator=comparator)
    assert isinstance(failed, Failed)
    assert len(calls) == 2
    assert failed.error.value.callback_result is result
    assert failed.error.value.callback_index == 1
    assert failed.error.value.error_class == "CALLBACK"


@pytest.mark.parametrize(
    "value", [None, 1, [], _Truthy(), np.array([True]), Ok(Ok(True)), Success()]
)
def test_non_boolean_results_are_not_coerced_by_truthiness(value: Any) -> None:
    subject = MultiArray.from_list(data=[1], shape=DynShape((1,))).unwrap()
    result = subject.equals(subject, comparator=lambda a, b: value)
    assert isinstance(result, Failed)
    assert result.error.value.callback_index == 0
    assert result.error.value.callback_exception is None


def test_exceptions_preserve_identity_without_stringifying_and_stop_comparison() -> (
    None
):
    class Error(ValueError):
        def __str__(self) -> str:
            raise AssertionError(
                "不得格式化用户异常 / Must not stringify user exception"
            )

    error = Error("comparison")
    subject = MultiArray.from_list(data=[0, 1, 2], shape=DynShape((3,))).unwrap()
    calls = []

    def comparator(a: Any, b: Any) -> bool:
        calls.append(a)
        if a == 1:
            raise error
        return True

    failed = subject.equals(subject, comparator=comparator)
    assert isinstance(failed, Failed)
    assert failed.error.value.callback_exception is error
    assert failed.error.value.callback_index == 1
    assert calls == [0, 1]


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit(7)])
def test_process_control_exceptions_propagate(error: BaseException) -> None:
    subject = MultiArray.from_list(data=[1], shape=DynShape((1,))).unwrap()

    def comparator(a: Any, b: Any) -> bool:
        raise error

    with pytest.raises(type(error)):
        subject.equals(subject, comparator=comparator)


@pytest.mark.parametrize("order", _ORDERS)
def test_offset_same_source_snapshots_precede_reentrant_writes(
    order: StorageOrder,
) -> None:
    source = MutableMultiArray.from_list(
        data=[[9, 1, 2], [9, 1, 2]], shape=Shape2(2, 3, order)
    ).unwrap()
    left = source.view(offsets=(0, 1), shape=Shape2(1, 2, order)).unwrap()
    right = source.view(offsets=(1, 1), shape=Shape2(1, 2, order)).unwrap()
    calls = []

    def comparator(a: Any, b: Any) -> bool:
        calls.append((a, b))
        source.set_many([((0, 2), 40), ((1, 2), 50)]).unwrap()
        assert source.at((1, 2)).unwrap() == 50
        return a == b

    assert left.equals(right, comparator=comparator).unwrap() is True
    assert calls == [(1, 1), (2, 2)]
    assert left.equals(right).unwrap() is False


def test_callback_can_wait_for_other_thread_to_write_source_without_deadlock() -> None:
    source = MutableMultiArray.from_list(data=[0, 0], shape=DynShape((2,))).unwrap()
    start = threading.Event()
    finished = threading.Event()

    def update() -> None:
        assert start.wait(5)
        source.set_many([((0,), 1), ((1,), 2)]).unwrap()
        finished.set()

    worker = threading.Thread(target=update)
    worker.start()

    def comparator(a: Any, b: Any) -> bool:
        start.set()
        assert finished.wait(5)
        return a == b

    try:
        assert source.equals(copy.copy(source), comparator=comparator).unwrap() is True
    finally:
        start.set()
        worker.join(5)
    assert not worker.is_alive() and source.flatten().unwrap() == [1, 2]


def test_callback_closure_and_duplicate_leaves_are_not_retained_by_native_operation() -> (
    None
):
    def operation() -> tuple[Any, Any]:
        payload = _Payload()
        subject = MutableMultiArray.full(shape=DynShape((2,)), value=payload).unwrap()
        payload.owner = subject

        def comparator(a: Any, b: Any) -> bool:
            assert subject.at((0,)).unwrap() is a
            return a is b

        assert subject.equals(subject, comparator=comparator).unwrap()
        return weakref.ref(payload), weakref.ref(comparator)

    payload, callback = operation()
    gc.collect()
    assert payload() is None and callback() is None


def test_native_exact_values_can_use_checked_domain_comparator_without_float_conversion() -> (
    None
):
    left = MultiArray.from_list(
        data=[Rational.from_value(1).unwrap()], shape=DynShape((1,))
    ).unwrap()
    right = MutableMultiArray.from_list(
        data=[Rational.from_value(1).unwrap()], shape=DynShape((1,))
    ).unwrap()
    assert left.equals(
        right, comparator=lambda a, b: a.compare(b).map(lambda value: value == 0)
    ).unwrap()


def test_wrong_kinds_and_lazy_views_are_not_silently_materialized() -> None:
    subject = MultiArray.from_list(data=[1], shape=DynShape((1,))).unwrap()
    lazy = MappedMultiArrayView.create(
        source=subject, callback=lambda value: 1 / 0
    ).unwrap()
    result = subject.equals(lazy)
    assert isinstance(result, Failed) and result.error.code is ErrorCode.NOT_SUPPORTED
    assert subject.equals([1]).is_failed()


def test_pending_storage_is_not_treated_as_equal_even_if_shapes_differ() -> None:
    pending = MultiArray(_native._unpickle_multiarray((1, [2], False)))
    other = MultiArray.from_list(data=[1], shape=DynShape((1,))).unwrap()
    result = pending.equals(other)
    assert (
        isinstance(result, Failed)
        and result.error.code is ErrorCode.FAILED_PRECONDITION
    )


def test_raw_transport_checks_callback_output_and_source_region() -> None:
    source = MultiArray.from_list(data=[1], shape=DynShape((1,))).unwrap()
    value, failure = _native._compare_reference_arrays(
        left=source._handle, right=source._handle, callback=lambda pair: (True, 1)
    )
    assert value is None and failure.error_class == "CALLBACK"
    foreign = (
        MultiArray.from_list(data=[1, 2], shape=DynShape((2,)))
        .unwrap()
        .view(offsets=(0,), shape=DynShape((1,)))
        .unwrap()
    )
    value, failure = _native._compare_reference_arrays(
        left=source._handle,
        right=source._handle,
        left_region=foreign._handle,
        callback=lambda pair: (True, True),
    )
    assert value is None and failure.category == "ILLEGAL_ARGUMENT"


def test_exact_builtin_fast_path_matches_python_value_equality_without_callback() -> (
    None
):
    def forbidden(request: Any) -> Any:
        raise AssertionError(
            "内置值不应调用 Python adapter / Builtins should not call the Python adapter"
        )

    nan = float("nan")
    for left, right in [
        (1, 1.0),
        (True, 1),
        (False, None),
        (None, None),
        ("abc", "abc"),
        (b"abc", b"abc"),
        (0.0, -0.0),
        (nan, nan),
        (1 << 10000, float("inf")),
        (complex(1, 0), 1),
        (complex(nan, 0), complex(nan, 0)),
    ]:
        a = MultiArray.from_list(data=[left], shape=DynShape((1,))).unwrap()
        b = MultiArray.from_list(data=[right], shape=DynShape((1,))).unwrap()
        value, failure = _native._compare_reference_arrays(
            left=a._handle, right=b._handle, callback=forbidden, builtin_equality=True
        )
        assert failure is None and value is (left == right)


@pytest.mark.parametrize("variant", ["exception", "failed", "invalid"])
def test_default_failure_keeps_full_logical_ordinal_after_fast_builtin_prefix(
    variant: str,
) -> None:
    error = ValueError("leaf equality")
    original = Failed(Err(ErrorCode.NOT_FOUND, "leaf failure"))

    class Leaf:
        def __eq__(self, other: object) -> Any:
            if variant == "exception":
                raise error
            return original if variant == "failed" else _Truthy()

    leaf = Leaf()
    subject = MultiArray.from_list(
        data=[1, np.int16(2), 3, leaf], shape=DynShape((4,))
    ).unwrap()
    result = subject.equals(subject)
    assert isinstance(result, Failed)
    assert result.error.value.callback_index == 3
    if variant == "exception":
        assert result.error.value.callback_exception is error
    elif variant == "failed":
        assert result.error.value.callback_result is original
    else:
        assert result.error.value.callback_exception is None


def test_builtin_subclasses_still_execute_their_equality_protocol() -> None:
    calls = []

    class Integer(int):
        def __eq__(self, other: object) -> bool:
            calls.append(other)
            return False

    left = MultiArray.from_list(data=[1, Integer(1)], shape=DynShape((2,))).unwrap()
    right = MultiArray.from_list(data=[1, 1], shape=DynShape((2,))).unwrap()
    assert left.equals(right).unwrap() is False
    assert calls == [1]


def test_bytes_warning_error_preserves_context_after_builtin_prefix() -> None:
    code = """
import os
directories = [os.add_dll_directory(path) for path in
    os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path] if os.name == 'nt' else []
from ospf_python._binding.multiarray import MultiArray
from ospf_python.multiarray.shape import DynShape
from ospf_python.utils.functional.result import Failed
left = MultiArray.from_list(data=[1, b'text'], shape=DynShape((2,))).unwrap()
right = MultiArray.from_list(data=[1, 'text'], shape=DynShape((2,))).unwrap()
result = left.equals(right)
assert isinstance(result, Failed)
assert isinstance(result.error.value.callback_exception, BytesWarning)
assert result.error.value.callback_index == 1
print('bytes-warning-context-ok')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-bb", "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
        env=os.environ.copy(),
    )
    assert "bytes-warning-context-ok" in result.stdout
