"""受检数组描述的预算、回调和所有权合同 / Checked description budgets, callbacks and ownership contracts."""

from __future__ import annotations

import copy
import gc
import subprocess
import sys
import threading
import weakref
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.multiarray import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Success, Warn

_KINDS = ["immutable", "mutable", "immutable-view", "mutable-view"]
_ORDERS = [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR]


def _subject(
    *, kind: str, order: StorageOrder, data: Any, dims: tuple[int, ...]
) -> Any:
    cls = MutableMultiArray if kind.startswith("mutable") else MultiArray
    source = cls.from_list(data=data, shape=DynShape(dims, order)).unwrap()
    if kind.endswith("view"):
        return source.view(offsets=(0,) * len(dims), shape=source.shape).unwrap()
    return source


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("order", _ORDERS)
def test_metadata_distinguishes_storage_from_logical_data(
    kind: str, order: StorageOrder
) -> None:
    subject = _subject(kind=kind, order=order, data=[[0, 1, 2], [3, 4, 5]], dims=(2, 3))
    offsets = "(0, 0)" if kind.endswith("view") else "None"
    assert subject.describe().unwrap() == (
        f"Array(shape=(2, 3), storage_order={order.name}, offsets={offsets}, "
        "access_order=ROW_MAJOR, data=[0, 1, 2, 3, 4, 5])"
    )
    assert "_handle=" in repr(subject)
    assert hash(subject) == object.__hash__(subject)


@pytest.mark.parametrize("order", _ORDERS)
def test_offset_nested_view_describes_only_its_logical_region(
    order: StorageOrder,
) -> None:
    source = MutableMultiArray.from_list(
        data=[[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]],
        shape=DynShape((3, 4), order),
    ).unwrap()
    view = source.view(offsets=(1, 1), shape=DynShape((2, 3), order)).unwrap()
    nested = view.view(offsets=(0, 1), shape=DynShape((2, 2), order)).unwrap()
    assert nested.describe().unwrap() == (
        f"Array(shape=(2, 2), storage_order={order.name}, offsets=(1, 2), "
        "access_order=ROW_MAJOR, data=[6, 7, 10, 11])"
    )


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("value", [None, "text", np.int16(3), [1, 2]])
def test_scalar_preserves_the_opaque_leaf_and_calls_formatter_once(
    kind: str, value: Any
) -> None:
    subject = _subject(kind=kind, order=_ORDERS[0], data=value, dims=())
    calls = []
    text = subject.describe(
        formatter=lambda item: calls.append(item) or "leaf"
    ).unwrap()
    assert "shape=()" in text and text.endswith("data=[leaf])")
    assert len(calls) == 1 and calls[0] is value


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("limit", [0, 1, 2, 3, 10, sys.maxsize])
def test_max_items_limits_snapshot_and_user_calls(kind: str, limit: int) -> None:
    subject = _subject(kind=kind, order=_ORDERS[1], data=[0, 1, 2], dims=(3,))
    calls = []
    text = subject.describe(
        formatter=lambda item: calls.append(item) or str(item), max_items=limit
    ).unwrap()
    assert calls == list(range(min(limit, 3)))
    expected = {0: "...", 1: "0, ...", 2: "0, 1, ..."}.get(limit, "0, 1, 2")
    assert text.endswith(f"data=[{expected}])")


def test_prefix_snapshot_does_not_incref_unvisited_leaves() -> None:
    marker = object()
    subject = MultiArray.from_list(data=[0, marker], shape=DynShape((2,))).unwrap()
    count = sys.getrefcount(marker)
    seen = []
    subject.describe(
        max_items=1, formatter=lambda _: seen.append(sys.getrefcount(marker)) or "0"
    ).unwrap()
    assert seen == [count]


@pytest.mark.parametrize("kind", _KINDS)
def test_character_budget_caps_entire_output_and_never_formats_hidden_leaves(
    kind: str,
) -> None:
    subject = _subject(kind=kind, order=_ORDERS[0], data=[0, 1, 2], dims=(3,))
    calls = []

    def formatter(item: Any) -> str:
        calls.append(item)
        return "\U0001f431\ud800\u4e2d" * 100

    full = subject.describe(formatter=formatter, max_chars=2000).unwrap()
    assert "\ud800" in full
    for budget in range(3, min(len(full), 180)):
        calls.clear()
        text = subject.describe(formatter=formatter, max_chars=budget).unwrap()
        assert len(text) == budget and text.endswith("...")
        assert text == full[: budget - 3] + "..."
        assert len(calls) <= 1
    calls.clear()
    assert subject.describe(formatter=formatter, max_chars=3).unwrap() == "..."
    assert calls == []


def test_high_rank_metadata_uses_no_python_recursion_and_skips_formatter() -> None:
    subject = MultiArray.full(shape=DynShape((1,) * 2500), value=None).unwrap()

    def forbidden(_: Any) -> str:
        raise AssertionError("元数据已超预算 / Metadata already exceeds the budget")

    text = subject.describe(formatter=forbidden, max_chars=80).unwrap()
    assert len(text) == 80 and text.endswith("...")


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("variant", ["failed", "fatal", "warn"])
def test_result_failure_identity_and_logical_position_are_preserved(
    kind: str, variant: str
) -> None:
    subject = _subject(kind=kind, order=_ORDERS[1], data=[[0, 1], [2, 3]], dims=(2, 2))
    original = {
        "failed": Failed(Err(ErrorCode.NOT_FOUND, "domain")),
        "fatal": Fatal((Err(ErrorCode.APPLICATION_ERROR, "fatal"),)),
        "warn": Warn("text", Err(ErrorCode.APPLICATION_ERROR, "warn")),
    }[variant]
    calls = []

    def formatter(item: Any) -> Any:
        calls.append(item)
        return original if item == 2 else Ok(str(item))

    result = subject.describe(formatter=formatter)
    assert isinstance(result, Failed)
    assert calls == [0, 1, 2]
    assert result.error.value.callback_result is original
    assert result.error.value.callback_index == 2
    assert result.error.value.error_class == "CALLBACK"


@pytest.mark.parametrize(
    "value", [None, 1, b"text", np.str_("text"), Ok(Ok("text")), Success()]
)
def test_non_string_formatter_outputs_are_not_implicitly_stringified(
    value: Any,
) -> None:
    subject = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    result = subject.describe(formatter=lambda _: value)
    assert isinstance(result, Failed)
    assert result.error.value.callback_index == 0
    assert result.error.value.callback_exception is None


def test_default_repr_errors_are_captured_without_formatting_the_exception() -> None:
    class Error(ValueError):
        def __str__(self) -> str:
            raise AssertionError(
                "不得格式化用户异常 / Must not stringify user exceptions"
            )

    error = Error("repr")

    class Leaf:
        def __repr__(self) -> str:
            raise error

    subject = MultiArray.from_list(data=[0, Leaf()], shape=DynShape((2,))).unwrap()
    result = subject.describe()
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error
    assert result.error.value.callback_index == 1
    assert error.__traceback__ is not None
    assert subject.describe(max_items=1).is_ok()


def test_default_repr_can_reenter_and_builtin_recursive_leaves_remain_opaque() -> None:
    class Leaf:
        owner: Any = None

        def __repr__(self) -> str:
            return self.owner.describe().unwrap()

    leaf = Leaf()
    cycle: list[Any] = []
    cycle.append(cycle)
    subject = MultiArray.from_list(data=[leaf, cycle], shape=DynShape((2,))).unwrap()
    leaf.owner = subject
    assert subject.describe().unwrap().endswith("data=[<recursive array>, [[...]]])")
    del subject, leaf, cycle
    gc.collect()


def test_hostile_string_subclass_is_rejected_without_running_string_protocols() -> None:
    class Text(str):
        def __len__(self) -> int:
            raise AssertionError(
                "不得调用子类协议 / Must not invoke subclass protocols"
            )

        def __str__(self) -> str:
            raise AssertionError(
                "不得隐式转换字符串 / Must not implicitly coerce strings"
            )

    subject = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    result = subject.describe(formatter=lambda _: Text("text"))
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize("control", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_base_exception_propagates_and_recursion_guard_is_always_removed(
    control: type[BaseException],
) -> None:
    subject = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()

    def formatter(_: Any) -> str:
        raise control()

    with pytest.raises(control):
        subject.describe(formatter=formatter)
    assert subject.describe().unwrap().endswith("data=[0])")


@pytest.mark.parametrize("order", _ORDERS)
def test_formatter_can_wait_for_cross_thread_mutation_without_locking(
    order: StorageOrder,
) -> None:
    source = MutableMultiArray.from_list(
        data=[[0, 1], [2, 3]], shape=DynShape((2, 2), order)
    ).unwrap()
    calls = []
    errors = []

    def formatter(item: Any) -> str:
        calls.append(item)
        if item == 0:
            thread = threading.Thread(
                target=lambda: errors.append(
                    source.set_many([((0, 1), 99), ((1, 0), 98)])
                )
            )
            thread.start()
            thread.join(timeout=5)
            assert not thread.is_alive(), (
                "格式化不得持有源锁 / Formatting must not hold the source lock"
            )
        return str(item)

    text = source.describe(formatter=formatter).unwrap()
    assert calls == [0, 1, 2, 3] and errors[0].is_ok()
    assert text.endswith("data=[0, 1, 2, 3])")
    assert source.at((0, 1)).unwrap() == 99


def test_recursion_guard_uses_native_source_identity_across_aliases_and_views() -> None:
    subject = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    alias = copy.copy(subject)
    view = subject.view(offsets=(0,), shape=subject.shape).unwrap()
    calls = []

    def formatter(_: Any) -> str:
        calls.append(1)
        assert alias.describe().unwrap() == "<recursive array>"
        assert view.describe(max_chars=3).unwrap() == "..."
        return subject.describe(formatter=formatter).unwrap()

    assert (
        subject.describe(formatter=formatter)
        .unwrap()
        .endswith("data=[<recursive array>])")
    )
    assert calls == [1]
    assert alias.describe().unwrap().endswith("data=[0])")


def test_recursion_guard_is_thread_local_not_a_global_busy_state() -> None:
    subject = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    output = []

    def formatter(_: Any) -> str:
        thread = threading.Thread(
            target=lambda: output.append(subject.describe().unwrap())
        )
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
        return "outer"

    assert subject.describe(formatter=formatter).unwrap().endswith("data=[outer])")
    assert len(output) == 1 and output[0].endswith("data=[0])")


@pytest.mark.parametrize("argument", ["max_items", "max_chars"])
@pytest.mark.parametrize("value", [True, 1.0, None, -1, sys.maxsize + 1])
def test_invalid_budgets_fail_before_formatter_calls(argument: str, value: Any) -> None:
    subject = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    result = subject.describe(**{argument: value}, formatter=lambda _: 1 / 0)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )


@pytest.mark.parametrize("budget", [0, 1, 2])
def test_character_budget_has_space_for_the_truncation_marker(budget: int) -> None:
    subject = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    assert subject.describe(max_chars=budget).is_failed()


def test_pending_source_and_foreign_region_fail_even_for_metadata_only_output() -> None:
    pending = MultiArray(_native._unpickle_multiarray((1, [2], False)))
    result = pending.describe(max_chars=3)
    assert (
        isinstance(result, Failed)
        and result.error.code is ErrorCode.FAILED_PRECONDITION
    )
    source = MultiArray.from_list(data=[0], shape=DynShape((1,))).unwrap()
    foreign = (
        MultiArray.from_list(data=[0, 1], shape=DynShape((2,)))
        .unwrap()
        .view(offsets=(0,), shape=DynShape((1,)))
        .unwrap()
    )
    value, error = _native._describe_reference_array(
        source=source._handle,
        region=foreign._handle,
        callback=lambda _: (True, "x"),
        max_items=0,
        max_chars=3,
    )
    assert value is None and error.category == "ILLEGAL_ARGUMENT"
    value, error = _native._describe_reference_array(
        source=source._handle, callback=lambda _: (True, 1), max_items=1, max_chars=1000
    )
    assert value is None and error.error_class == "CALLBACK"
    assert source.describe(formatter=None).is_failed()


def test_formatter_and_source_cycles_are_collectible_after_success_and_failure() -> (
    None
):
    class Leaf:
        owner: Any = None

    def operation(fail: bool) -> tuple[Any, Any, Any]:
        leaf = Leaf()
        subject = MultiArray.from_list(data=[leaf], shape=DynShape((1,))).unwrap()
        leaf.owner = subject

        def formatter(item: Any) -> str:
            assert subject.at((0,)).unwrap() is item
            if fail:
                raise ValueError("formatter")
            return "leaf"

        result = subject.describe(formatter=formatter)
        assert result.is_failed() if fail else result.is_ok()
        return weakref.ref(leaf), weakref.ref(formatter), result

    for fail in (False, True):
        leaf, formatter, result = operation(fail)
        gc.collect()
        if fail:
            assert leaf() is not None and formatter() is not None
        else:
            assert leaf() is None and formatter() is None
        del result
        gc.collect()
        assert leaf() is None and formatter() is None


def test_unpublished_preview_cleanup_allows_destructor_reentry() -> None:
    code = """
import os
directories = [os.add_dll_directory(path) for path in
    os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path] if os.name == 'nt' else []
from ospf_python._binding.multiarray import MutableMultiArray
from ospf_python.multiarray.shape import DynShape
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed
events = []
class Leaf:
    def __del__(self):
        events.append(source.at((0,)).unwrap())
source = MutableMultiArray.from_list(data=[Leaf(), Leaf()], shape=DynShape((2,))).unwrap()
failure = Failed(Err(ErrorCode.NOT_FOUND, 'formatter'))
def formatter(item):
    source.set_many([((0,), 10), ((1,), 11)]).unwrap()
    return failure
result = source.describe(formatter=formatter)
assert result.error.value.callback_result is failure
assert events == [10, 10], events
assert source.describe().unwrap().endswith('data=[10, 11])')
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=15
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
