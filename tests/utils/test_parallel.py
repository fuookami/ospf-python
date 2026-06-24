"""Parallel 模块测试 / Tests for parallel utilities.

覆盖 all_any_none、associate、channel_guard、common、count、filter、
find、flat_map、fold、map、max_min、min_max、thread_guard。
Covers all_any_none, associate, channel_guard, common, count, filter,
find, flat_map, fold, map, max_min, min_max, thread_guard.
"""

from __future__ import annotations

import asyncio
import contextlib

from ospf_python.utils.parallel.all_any_none import (
    all_parallel,
    any_parallel,
    none_parallel,
)
from ospf_python.utils.parallel.associate import associate_parallel
from ospf_python.utils.parallel.channel_guard import ChannelGuard
from ospf_python.utils.parallel.common import WorkerPoolResult, WorkerPoolTask
from ospf_python.utils.parallel.count import count_parallel
from ospf_python.utils.parallel.filter import filter_parallel
from ospf_python.utils.parallel.find import find_parallel
from ospf_python.utils.parallel.flat_map import flat_map_parallel
from ospf_python.utils.parallel.fold import fold_parallel
from ospf_python.utils.parallel.map import map_parallel
from ospf_python.utils.parallel.max_min import max_parallel, min_parallel
from ospf_python.utils.parallel.min_max import MinMaxResult, min_max_parallel
from ospf_python.utils.parallel.thread_guard import Async

# -- all_parallel / any_parallel / none_parallel --


class TestAllParallel:
    """all_parallel 测试。"""

    async def test_all_true(self) -> None:
        """所有元素满足谓词时返回 True。"""
        result = await all_parallel([2, 4, 6], lambda x: x % 2 == 0)
        assert result is True

    async def test_all_false(self) -> None:
        """存在不满足谓词的元素时返回 False。"""
        result = await all_parallel([1, 2, 3], lambda x: x % 2 == 0)
        assert result is False

    async def test_all_empty(self) -> None:
        """空序列返回 True。"""
        result = await all_parallel([], lambda x: True)
        assert result is True

    async def test_all_async_predicate(self) -> None:
        """支持异步谓词函数。"""

        async def pred(x: int) -> bool:
            return x > 0

        result = await all_parallel([1, 2, 3], pred)
        assert result is True


class TestAnyParallel:
    """any_parallel 测试。"""

    async def test_any_true(self) -> None:
        """存在满足谓词的元素时返回 True。"""
        result = await any_parallel([1, 2, 3], lambda x: x == 2)
        assert result is True

    async def test_any_false(self) -> None:
        """无元素满足谓词时返回 False。"""
        result = await any_parallel([1, 3, 5], lambda x: x % 2 == 0)
        assert result is False

    async def test_any_empty(self) -> None:
        """空序列返回 False。"""
        result = await any_parallel([], lambda x: True)
        assert result is False


class TestNoneParallel:
    """none_parallel 测试。"""

    async def test_none_true(self) -> None:
        """无元素满足谓词时返回 True。"""
        result = await none_parallel([1, 3, 5], lambda x: x % 2 == 0)
        assert result is True

    async def test_none_false(self) -> None:
        """存在满足谓词的元素时返回 False。"""
        result = await none_parallel([1, 2, 3], lambda x: x == 2)
        assert result is False

    async def test_none_empty(self) -> None:
        """空序列返回 True。"""
        result = await none_parallel([], lambda x: True)
        assert result is True


# -- associate_parallel --


class TestAssociateParallel:
    """associate_parallel 测试。"""

    async def test_basic(self) -> None:
        """基本关联操作。"""
        result = await associate_parallel([1, 2, 3], lambda x: (f"k{x}", x * 10))
        assert result == {"k1": 10, "k2": 20, "k3": 30}

    async def test_empty(self) -> None:
        """空序列返回空字典。"""
        result = await associate_parallel([], lambda x: ("", x))
        assert result == {}

    async def test_async_transform(self) -> None:
        """支持异步转换函数。"""

        async def transform(x: int) -> tuple[str, int]:
            return (str(x), x**2)

        result = await associate_parallel([2, 3], transform)
        assert result == {"2": 4, "3": 9}


# -- ChannelGuard --


class TestChannelGuard:
    """ChannelGuard 测试。"""

    async def test_capacity(self) -> None:
        """容量属性正确。"""
        guard: ChannelGuard[int] = ChannelGuard(5)
        assert guard.capacity == 5

    async def test_send_receive(self) -> None:
        """发送和接收值。"""
        guard: ChannelGuard[int] = ChannelGuard(3)
        await guard.send(42)
        value = await guard.receive()
        assert value == 42

    async def test_fifo_order(self) -> None:
        """保持先进先出顺序。"""
        guard: ChannelGuard[int] = ChannelGuard(10)
        for i in range(5):
            await guard.send(i)
        received = [await guard.receive() for _ in range(5)]
        assert received == [0, 1, 2, 3, 4]

    async def test_size(self) -> None:
        """大小随发送/接收变化。"""
        guard: ChannelGuard[str] = ChannelGuard(5)
        assert guard.size == 0
        await guard.send("a")
        assert guard.size == 1
        await guard.receive()
        assert guard.size == 0


# -- WorkerPoolTask / WorkerPoolResult --


class TestCommon:
    """WorkerPoolTask 和 WorkerPoolResult 测试。"""

    def test_task_fields(self) -> None:
        """WorkerPoolTask 字段正确。"""
        task = WorkerPoolTask(index=3, item="hello")
        assert task.index == 3
        assert task.item == "hello"

    def test_result_fields(self) -> None:
        """WorkerPoolResult 字段正确。"""
        result = WorkerPoolResult(index=1, result=99)
        assert result.index == 1
        assert result.result == 99

    def test_frozen(self) -> None:
        """数据类不可变。"""
        task = WorkerPoolTask(index=0, item=1)
        try:
            task.index = 1  # type: ignore[misc]
            raise AssertionError("Should raise FrozenInstanceError")
        except AttributeError:
            pass


# -- count_parallel --


class TestCountParallel:
    """count_parallel 测试。"""

    async def test_count_basic(self) -> None:
        """基本计数。"""
        result = await count_parallel([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
        assert result == 2

    async def test_count_all(self) -> None:
        """所有元素匹配。"""
        result = await count_parallel([2, 4, 6], lambda x: x % 2 == 0)
        assert result == 3

    async def test_count_none(self) -> None:
        """无元素匹配。"""
        result = await count_parallel([1, 3, 5], lambda x: x % 2 == 0)
        assert result == 0

    async def test_count_empty(self) -> None:
        """空序列返回 0。"""
        result = await count_parallel([], lambda x: True)
        assert result == 0


# -- filter_parallel --


class TestFilterParallel:
    """filter_parallel 测试。"""

    async def test_filter_basic(self) -> None:
        """基本过滤，保持顺序。"""
        result = await filter_parallel([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
        assert result == [2, 4]

    async def test_filter_all(self) -> None:
        """所有元素满足条件。"""
        result = await filter_parallel([2, 4, 6], lambda x: x > 0)
        assert result == [2, 4, 6]

    async def test_filter_none(self) -> None:
        """无元素满足条件。"""
        result = await filter_parallel([1, 3, 5], lambda x: x > 10)
        assert result == []

    async def test_filter_empty(self) -> None:
        """空序列返回空列表。"""
        result = await filter_parallel([], lambda x: True)
        assert result == []


# -- find_parallel --


class TestFindParallel:
    """find_parallel 测试。"""

    async def test_find_first(self) -> None:
        """找到第一个匹配元素。"""
        result = await find_parallel([1, 2, 3, 4], lambda x: x > 2)
        assert result == 3

    async def test_find_not_found(self) -> None:
        """未找到返回 None。"""
        result = await find_parallel([1, 2, 3], lambda x: x > 10)
        assert result is None

    async def test_find_empty(self) -> None:
        """空序列返回 None。"""
        result = await find_parallel([], lambda x: True)
        assert result is None


# -- flat_map_parallel --


class TestFlatMapParallel:
    """flat_map_parallel 测试。"""

    async def test_flat_map_basic(self) -> None:
        """基本扁平映射。"""
        result = await flat_map_parallel([1, 2, 3], lambda x: [x, x * 10])
        assert result == [1, 10, 2, 20, 3, 30]

    async def test_flat_map_empty_items(self) -> None:
        """空序列返回空列表。"""
        result = await flat_map_parallel([], lambda x: [x])
        assert result == []

    async def test_flat_map_empty_result(self) -> None:
        """转换返回空列表。"""
        result = await flat_map_parallel([1, 2], lambda x: [])
        assert result == []


# -- fold_parallel --


class TestFoldParallel:
    """fold_parallel 测试。"""

    async def test_fold_sum(self) -> None:
        """求和折叠。"""
        result = await fold_parallel([1, 2, 3, 4], 0, lambda acc, x: acc + x)
        assert result == 10

    async def test_fold_concat(self) -> None:
        """字符串拼接折叠。"""
        result = await fold_parallel(["a", "b", "c"], "", lambda acc, x: acc + x)
        assert result == "abc"

    async def test_fold_empty(self) -> None:
        """空序列返回初始值。"""
        result = await fold_parallel([], 42, lambda acc, x: acc + x)
        assert result == 42


# -- map_parallel --


class TestMapParallel:
    """map_parallel 测试。"""

    async def test_map_basic(self) -> None:
        """基本映射，保持顺序。"""
        result = await map_parallel([1, 2, 3], lambda x: x * 2)
        assert result == [2, 4, 6]

    async def test_map_empty(self) -> None:
        """空序列返回空列表。"""
        result = await map_parallel([], lambda x: x)
        assert result == []

    async def test_map_async_transform(self) -> None:
        """支持异步转换函数。"""

        async def double(x: int) -> int:
            return x * 2

        result = await map_parallel([1, 2, 3], double)
        assert result == [2, 4, 6]


# -- max_parallel / min_parallel --


class TestMaxMinParallel:
    """max_parallel 和 min_parallel 测试。"""

    async def test_max_basic(self) -> None:
        """查找最大值。"""
        cmp = lambda a, b: (a > b) - (a < b)  # noqa: E731
        result = await max_parallel([3, 1, 4, 1, 5], cmp)
        assert result == 5

    async def test_max_empty(self) -> None:
        """空序列返回 None。"""
        cmp = lambda a, b: 0  # noqa: E731
        result = await max_parallel([], cmp)
        assert result is None

    async def test_min_basic(self) -> None:
        """查找最小值。"""
        cmp = lambda a, b: (a > b) - (a < b)  # noqa: E731
        result = await min_parallel([3, 1, 4, 1, 5], cmp)
        assert result == 1

    async def test_min_empty(self) -> None:
        """空序列返回 None。"""
        cmp = lambda a, b: 0  # noqa: E731
        result = await min_parallel([], cmp)
        assert result is None


# -- min_max_parallel --


class TestMinMaxParallel:
    """min_max_parallel 测试。"""

    async def test_min_max_basic(self) -> None:
        """同时查找最小值和最大值。"""
        result = await min_max_parallel([3, 1, 4, 1, 5])
        assert result is not None
        assert result.min_value == 1
        assert result.max_value == 5

    async def test_min_max_single(self) -> None:
        """单元素列表。"""
        result = await min_max_parallel([42])
        assert result is not None
        assert result.min_value == 42
        assert result.max_value == 42

    async def test_min_max_empty(self) -> None:
        """空序列返回 None。"""
        result = await min_max_parallel([])
        assert result is None

    async def test_min_max_custom_comparator(self) -> None:
        """自定义比较器。"""

        def cmp(a: str, b: str) -> int:
            return (len(a) > len(b)) - (len(a) < len(b))

        result = await min_max_parallel(["a", "bbb", "cc"], cmp)
        assert result is not None
        assert result.min_value == "a"
        assert result.max_value == "bbb"

    def test_min_max_result_frozen(self) -> None:
        """MinMaxResult 不可变。"""
        r = MinMaxResult(min_value=1, max_value=2)
        assert r.min_value == 1
        assert r.max_value == 2
        try:
            r.min_value = 0  # type: ignore[misc]
            raise AssertionError("Should raise FrozenInstanceError")
        except AttributeError:
            pass


# -- Async (thread_guard) --


class TestAsync:
    """Async 守卫测试。"""

    async def test_run_basic(self) -> None:
        """基本异步计算。"""

        async def compute() -> int:
            return 42

        guard = Async(compute)
        result = await guard.run()
        assert result == 42

    async def test_is_done(self) -> None:
        """完成后 is_done 为 True。"""

        async def compute() -> str:
            return "done"

        guard = Async(compute)
        assert guard.is_done is False
        await guard.run()
        assert guard.is_done is True

    async def test_cancel(self) -> None:
        """取消任务。"""

        async def slow() -> None:
            await asyncio.sleep(100)

        guard = Async(slow)
        task = asyncio.create_task(guard.run())
        await asyncio.sleep(0.01)
        guard.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert guard.is_done is True

    async def test_timeout(self) -> None:
        """超时引发 CancelledError。"""

        async def slow() -> None:
            await asyncio.sleep(100)

        guard = Async(slow, timeout=0.01)
        try:
            await guard.run()
            raise AssertionError("Should raise CancelledError")
        except asyncio.CancelledError:
            pass
