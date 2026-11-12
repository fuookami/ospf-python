"""组合和排列的公共合同，不代表完整原生验收。

Public selection contracts, not full native acceptance.
"""

from __future__ import annotations

import asyncio
import importlib
import itertools
import threading
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from ospf_python._binding.result import BindingResult
from ospf_python.math.combinatorics.combinations import combinations
from ospf_python.math.combinatorics.combinatorics_async import (
    combinations_async,
    permutations_async,
)
from ospf_python.math.combinatorics.permutations import permutations
from ospf_python.utils.functional.result import Failed

Selection = Callable[[Any, Any], BindingResult[list[list[Any]]]]
"""自然 Result 入口类型。 / Natural Result entry-point type."""

FUNCTIONS = (combinations, permutations)
SIZES = [(n, k) for n in range(7) for k in range(-1, n + 2)]


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize(("n", "k"), SIZES)
def test_complete_order_matches_positional_itertools(
    *, function: Selection, n: int, k: int
) -> None:
    """逐行顺序而非排序后的集合必须一致。 / Compare order, not sorted sets."""
    source = list(range(n))
    oracle = (
        itertools.combinations if function is combinations else itertools.permutations
    )
    expected = [] if k < 0 else [list(row) for row in oracle(source, k)]
    assert function(source, k).unwrap() == expected


@pytest.mark.parametrize("function", FUNCTIONS)
def test_duplicate_positions_and_opaque_leaves(function: Selection) -> None:
    """叶不比较、不转换，重复槽不去重。 / Opaque duplicate slots are not deduplicated."""

    class Opaque:
        def __eq__(self, other: object) -> bool:
            raise AssertionError("must not compare leaves")

        def __repr__(self) -> str:
            raise AssertionError("must not format leaves")

        def __int__(self) -> int:
            raise AssertionError("must not coerce leaves")

    a, b = Opaque(), Opaque()
    source = [a, a, b]
    oracle = (
        itertools.combinations if function is combinations else itertools.permutations
    )
    expected = list(oracle(range(3), 2))
    result = function(source, 2).unwrap()
    assert len(result) == len(expected)
    assert len({id(row) for row in result}) == len(result)
    for row, positions in zip(result, expected, strict=True):
        assert all(
            value is source[index] for value, index in zip(row, positions, strict=True)
        )
    result[0].append(None)
    assert len(source) == 3
    assert all(len(row) == 2 for row in result[1:])


class ObservedSequence:
    """区分原索引协议与快照迭代。 / Distinguish indexed reads from snapshot iteration."""

    def __init__(self) -> None:
        self.values = [0, 1, 2]
        self.events: list[tuple[str, ...] | tuple[str, int]] = []

    def __len__(self) -> int:
        self.events.append(("len",))
        return len(self.values)

    def __getitem__(self, index: int) -> int:
        self.events.append(("get", index))
        return self.values[index]

    def __iter__(self) -> Iterator[int]:
        raise AssertionError("legacy selection does not iterate the input")


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("k", [-1, 0, 4])
def test_degenerate_calls_do_not_consume_items(function: Selection, k: int) -> None:
    """负值、零值和过大值保留短路读取。 / Preserve degenerate-call read short circuits."""
    source = ObservedSequence()
    assert function(source, k).unwrap() == ([[]] if k == 0 else [])
    expected_reads = 0 if k < 0 else 2 if function is permutations and k == 0 else 1
    assert source.events == [("len",)] * expected_reads


@pytest.mark.parametrize("function", FUNCTIONS)
def test_legacy_external_read_trace(function: Selection) -> None:
    """记录旧扩展点求值顺序，不能冒充最终合同已决定。

    Record legacy extension evaluation order without claiming a final cutover decision.
    """
    source = ObservedSequence()
    function(source, 2).unwrap()
    if function is combinations:
        expected: list[tuple[str, ...] | tuple[str, int]] = [
            ("len",),
            ("len",),
            ("get", 0),
            ("len",),
            ("get", 1),
            ("get", 2),
            ("get", 1),
            ("len",),
            ("get", 2),
            ("get", 2),
            ("len",),
        ]
    else:
        expected = [
            ("len",),
            ("len",),
            ("len",),
            ("get", 0),
            ("len",),
            ("get", 1),
            ("get", 2),
            ("get", 1),
            ("len",),
            ("get", 0),
            ("get", 2),
            ("get", 2),
            ("len",),
            ("get", 0),
            ("get", 1),
        ]
    assert source.events == expected


@pytest.mark.parametrize("function", FUNCTIONS)
def test_legacy_getter_mutation_affects_later_reads(function: Selection) -> None:
    """不能无声明地用输入快照隐藏写入。 / Do not silently hide writes with a snapshot."""

    class ReplacingSequence(ObservedSequence):
        def __getitem__(self, index: int) -> int:
            value = super().__getitem__(index)
            if index == 0:
                self.values[2] = 9
            return value

    source = ReplacingSequence()
    result = function(source, 2).unwrap()
    assert [0, 9] in result
    assert not any(2 in row for row in result)


@pytest.mark.parametrize("function", FUNCTIONS)
def test_legacy_prefix_reuses_value_but_other_visits_reread(
    function: Selection,
) -> None:
    """前缀内复用与跨前缀重读不同于快照。 / Prefix reuse differs from snapshotting."""

    class FreshSequence(ObservedSequence):
        def __init__(self) -> None:
            super().__init__()
            self.references: list[object] = []

        def __getitem__(self, index: int) -> Any:
            super().__getitem__(index)
            value = object()
            self.references.append(value)
            return value

    source = FreshSequence()
    result = function(source, 2).unwrap()
    visits = (
        [(0, 1), (0, 2), (3, 4)]
        if function is combinations
        else [(0, 1), (0, 2), (3, 4), (3, 5), (6, 7), (6, 8)]
    )
    assert len(source.references) == (6 if function is combinations else 9)
    for row, indices in zip(result, visits, strict=True):
        assert all(
            value is source.references[index]
            for value, index in zip(row, indices, strict=True)
        )


def test_legacy_combination_growth_is_observable() -> None:
    """记录动态长度的实际能力。 / Record the observable dynamic-length capability."""

    class GrowingSequence(ObservedSequence):
        def __getitem__(self, index: int) -> int:
            if len(self.values) == 3:
                self.values.append(3)
            return super().__getitem__(index)

    operation: Selection = combinations
    assert operation(GrowingSequence(), 2).unwrap() == [
        [0, 1],
        [0, 2],
        [0, 3],
        [1, 2],
        [1, 3],
        [2, 3],
    ]


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize(
    "exception_type", [RuntimeError, KeyboardInterrupt, SystemExit]
)
def test_external_exception_identity_before_result_upgrade(
    function: Selection, exception_type: type[BaseException]
) -> None:
    """记录原异常对象，未来 Result 必须保留它。 / Future Result must retain this exception."""
    error = exception_type("external selection failure")

    class FailingSequence(ObservedSequence):
        def __getitem__(self, index: int) -> int:
            raise error

    if isinstance(error, Exception):
        result = function(FailingSequence(), 1)
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
    else:
        with pytest.raises(exception_type) as caught:
            function(FailingSequence(), 1)
        assert caught.value is error


@pytest.mark.parametrize("function", FUNCTIONS)
def test_external_exception_is_not_formatted(function: Selection) -> None:
    """错误的 str/repr 也可能运行外部代码。 / Error str/repr can execute external code."""

    class UnprintableError(Exception):
        def __str__(self) -> str:
            raise AssertionError("must not stringify external errors")

        def __repr__(self) -> str:
            raise AssertionError("must not format external errors")

    error = UnprintableError()

    class FailingSequence(ObservedSequence):
        def __getitem__(self, index: int) -> int:
            raise error

    result = function(FailingSequence(), 1)
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("k", [False, True, 2.0, 1.5])
def test_legacy_noninteger_count_is_characterized(function: Selection, k: Any) -> None:
    """记录 bool/float 历史行为，不擅自宣称整数域已收窄。

    Characterize bool/float behavior without silently narrowing the accepted domain.
    """
    expected: list[list[Any]] = (
        [[]]
        if k is False
        else [[0], [1], [2]]
        if k is True
        else function([0, 1, 2], 2).unwrap()
        if k == 2.0
        else []
    )
    assert function([0, 1, 2], k).unwrap() == expected


@pytest.mark.parametrize("function", FUNCTIONS)
def test_package_exports_keep_natural_identity(function: Selection) -> None:
    """包导出不能创建平行函数身份。 / Package exports keep the natural function identity."""
    package = importlib.import_module("ospf_python.math.combinatorics")
    assert getattr(package, function.__name__) is function


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["combinations", "permutations"])
async def test_async_runs_same_natural_function_in_executor(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """异步不引入第二内核，返回同一载荷。 / Async uses one kernel and returns its payload."""
    module = importlib.import_module(
        "ospf_python.math.combinatorics.combinatorics_async"
    )
    main_thread = threading.get_ident()
    source, sentinel = [object()], [[object()]]
    seen: list[tuple[object, int, int]] = []

    def operation(items: Any, k: int) -> list[list[Any]]:
        seen.append((items, k, threading.get_ident()))
        return sentinel

    monkeypatch.setattr(module, name, operation)
    result = await getattr(module, name + "_async")(source, 1)
    assert result is sentinel
    assert len(seen) == 1 and seen[0][0] is source and seen[0][1] == 1
    assert seen[0][2] != main_thread


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["combinations", "permutations"])
async def test_async_cancellation_does_not_claim_to_stop_started_work(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """取消等待不等于停止工作，测试结束前释放线程。

    Cancelling a waiter does not stop work; release the worker before finishing.
    """
    module = importlib.import_module(
        "ospf_python.math.combinatorics.combinatorics_async"
    )
    started, release, completed = (
        threading.Event(),
        threading.Event(),
        threading.Event(),
    )

    def operation(items: Any, k: int) -> list[list[Any]]:
        started.set()
        if release.wait(timeout=10):
            completed.set()
        return []

    monkeypatch.setattr(module, name, operation)
    task = asyncio.create_task(getattr(module, name + "_async")([], 0))
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not completed.is_set()
    finally:
        release.set()
        assert await asyncio.to_thread(completed.wait, 5)
        if not task.done():
            await task


@pytest.mark.asyncio
@pytest.mark.parametrize("function", [combinations_async, permutations_async])
async def test_async_leaf_identity_and_exception_provenance(function: Any) -> None:
    """真实异步入口保留叶与异常对象。 / Real async calls retain leaves and exception identity."""
    leaf = object()
    assert ((await function([leaf], 1)).unwrap())[0][0] is leaf
    error = RuntimeError("async external failure")

    class FailingSequence(ObservedSequence):
        def __getitem__(self, index: int) -> int:
            raise error

    result = await function(FailingSequence(), 1)
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error
    await asyncio.sleep(0)
