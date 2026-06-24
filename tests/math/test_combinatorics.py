"""组合数学模块测试。

Combinatorics module tests.

测试组合、排列、笛卡尔积及异步变体。
Tests combinations, permutations, Cartesian product,
and their async variants.
"""

from __future__ import annotations

import pytest

from ospf_python.math.combinatorics.combinations import (
    combinations,
)
from ospf_python.math.combinatorics.combinatorics_async import (
    combinations_async,
    permutations_async,
)
from ospf_python.math.combinatorics.cross import cross
from ospf_python.math.combinatorics.permutations import (
    permutations,
)

# ── combinations ────────────────────────────────────────────────


class TestCombinations:
    """组合测试。"""

    def test_basic(self) -> None:
        """基本组合。/ Basic combinations."""
        result = combinations([1, 2, 3], 2)
        assert sorted(result) == [[1, 2], [1, 3], [2, 3]]

    def test_k_zero(self) -> None:
        """k=0 返回空集。/ k=0 returns empty set."""
        result = combinations([1, 2, 3], 0)
        assert result == [[]]

    def test_k_equals_n(self) -> None:
        """k=n 返回全部。/ k=n returns all."""
        result = combinations([1, 2, 3], 3)
        assert result == [[1, 2, 3]]

    def test_k_greater_than_n(self) -> None:
        """k>n 返回空。/ k>n returns empty."""
        result = combinations([1, 2], 5)
        assert result == []

    def test_negative_k(self) -> None:
        """负 k 返回空。/ Negative k returns empty."""
        result = combinations([1, 2, 3], -1)
        assert result == []

    def test_count(self) -> None:
        """组合数 C(5,2)=10。/ Combination count C(5,2)=10."""
        result = combinations([1, 2, 3, 4, 5], 2)
        assert len(result) == 10

    def test_strings(self) -> None:
        """字符串组合。/ String combinations."""
        result = combinations(["a", "b", "c"], 2)
        assert len(result) == 3


# ── permutations ────────────────────────────────────────────────


class TestPermutations:
    """排列测试。"""

    def test_basic(self) -> None:
        """基本排列。/ Basic permutations."""
        result = permutations([1, 2, 3], 2)
        expected = [[1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2]]
        assert sorted(result) == sorted(expected)

    def test_k_zero(self) -> None:
        """k=0 返回空集。/ k=0 returns empty set."""
        result = permutations([1, 2, 3], 0)
        assert result == [[]]

    def test_k_equals_n(self) -> None:
        """k=n 返回全排列。/ k=n returns full permutations."""
        result = permutations([1, 2, 3], 3)
        assert len(result) == 6

    def test_k_greater_than_n(self) -> None:
        """k>n 返回空。/ k>n returns empty."""
        result = permutations([1, 2], 5)
        assert result == []

    def test_negative_k(self) -> None:
        """负 k 返回空。/ Negative k returns empty."""
        result = permutations([1, 2, 3], -1)
        assert result == []

    def test_count(self) -> None:
        """排列数 P(4,2)=12。/ Permutation count P(4,2)=12."""
        result = permutations([1, 2, 3, 4], 2)
        assert len(result) == 12

    def test_single_element(self) -> None:
        """单元素排列。/ Single element permutation."""
        result = permutations([42], 1)
        assert result == [[42]]


# ── cross ───────────────────────────────────────────────────────


class TestCross:
    """笛卡尔积测试。"""

    def test_basic(self) -> None:
        """基本笛卡尔积。/ Basic Cartesian product."""
        result = cross([1, 2], ["a", "b"])
        expected = [(1, "a"), (1, "b"), (2, "a"), (2, "b")]
        assert result == expected

    def test_three_iterables(self) -> None:
        """三组笛卡尔积。/ Three-way Cartesian product."""
        result = cross([1], [2], [3])
        assert result == [(1, 2, 3)]

    def test_empty_iterable(self) -> None:
        """含空可迭代对象。/ With empty iterable."""
        result = cross([1, 2], [])
        assert result == []

    def test_no_iterables(self) -> None:
        """无可迭代对象。/ No iterables."""
        result = cross()
        assert result == [()]

    def test_single_iterable(self) -> None:
        """单个可迭代对象。/ Single iterable."""
        result = cross([1, 2, 3])
        assert result == [(1,), (2,), (3,)]

    def test_count(self) -> None:
        """笛卡尔积大小。/ Cartesian product size."""
        result = cross([1, 2, 3], [4, 5])
        assert len(result) == 6


# ── async ───────────────────────────────────────────────────────


class TestCombinationsAsync:
    """异步组合测试。"""

    @pytest.mark.asyncio
    async def test_basic(self) -> None:
        """异步基本组合。/ Async basic combinations."""
        result = await combinations_async([1, 2, 3], 2)
        assert sorted(result) == [[1, 2], [1, 3], [2, 3]]

    @pytest.mark.asyncio
    async def test_k_zero(self) -> None:
        """异步 k=0。/ Async k=0."""
        result = await combinations_async([1, 2], 0)
        assert result == [[]]


class TestPermutationsAsync:
    """异步排列测试。"""

    @pytest.mark.asyncio
    async def test_basic(self) -> None:
        """异步基本排列。/ Async basic permutations."""
        result = await permutations_async([1, 2, 3], 2)
        assert len(result) == 6

    @pytest.mark.asyncio
    async def test_full_permutation(self) -> None:
        """异步全排列。/ Async full permutation."""
        result = await permutations_async([1, 2], 2)
        expected = [[1, 2], [2, 1]]
        assert sorted(result) == sorted(expected)
