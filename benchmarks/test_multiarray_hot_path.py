"""MultiArray 运算热路径基准 / MultiArray ops hot path benchmark.

对齐 Kotlin MultiArrayHotPathBenchmark: 多维数组创建/运算/规约性能。
Aligned to Kotlin MultiArrayHotPathBenchmark: multi-dimensional array
creation/operation/reduction performance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


@pytest.mark.benchmark
class TestMultiArrayHotPath:
    """MultiArray 运算热路径基准。

    MultiArray ops hot path benchmarks.
    """

    def test_array_creation(
        self,
        benchmark: BenchmarkFixture,
        multiarray_dataset: dict[str, int | tuple[int, ...]],
    ) -> None:
        """数组创建热路径 / Array creation hot path.

        对齐 Kotlin MultiArrayHotPathBenchmark.arrayCreation。
        Aligned to Kotlin MultiArrayHotPathBenchmark.arrayCreation.

        Args:
            benchmark: pytest-benchmark fixture.
            multiarray_dataset: 数据集规模 / Dataset scale.
        """
        dims = multiarray_dataset["dims"]
        assert isinstance(dims, tuple)
        shape = DynShape(dims=dims)

        def _run() -> MultiArray[float, DynShape]:
            return MultiArray.zeros(shape)

        benchmark(_run)

    def test_map_operation(
        self,
        benchmark: BenchmarkFixture,
        multiarray_dataset: dict[str, int | tuple[int, ...]],
    ) -> None:
        """map 运算热路径 / Map operation hot path.

        对齐 Kotlin MultiArrayHotPathBenchmark.mapOperation。
        Aligned to Kotlin MultiArrayHotPathBenchmark.mapOperation.

        Args:
            benchmark: pytest-benchmark fixture.
            multiarray_dataset: 数据集规模 / Dataset scale.
        """
        dims = multiarray_dataset["dims"]
        assert isinstance(dims, tuple)
        shape = DynShape(dims=dims)
        arr = MultiArray.ones(shape)

        def _run() -> MultiArray[float, DynShape]:
            return arr.map(lambda x: x * 2.0 + 1.0)

        benchmark(_run)

    def test_reduce_operation(
        self,
        benchmark: BenchmarkFixture,
        multiarray_dataset: dict[str, int | tuple[int, ...]],
    ) -> None:
        """reduce 运算热路径 / Reduce operation hot path.

        对齐 Kotlin MultiArrayHotPathBenchmark.reduceOperation。
        Aligned to Kotlin MultiArrayHotPathBenchmark.reduceOperation.

        Args:
            benchmark: pytest-benchmark fixture.
            multiarray_dataset: 数据集规模 / Dataset scale.
        """
        dims = multiarray_dataset["dims"]
        assert isinstance(dims, tuple)
        shape = DynShape(dims=dims)
        arr = MultiArray.ones(shape)

        def _run() -> float:
            return arr.reduce(lambda a, b: a + b)

        benchmark(_run)
