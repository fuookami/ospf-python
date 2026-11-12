"""形状构造、标量/批量索引和含构造流程基准 / Shape construction, scalar/batch indexing and full-pipeline benchmarks."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np
import pytest

from ospf_python._binding.multiarray import Shape
from ospf_python.multiarray.shape import DynShape, StorageOrder

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

_SIZES = {"small": 32, "medium": 256, "large": 2048}


@pytest.mark.benchmark
@pytest.mark.parametrize("size", ["small", "medium", "large"])
@pytest.mark.parametrize("order_name", ["ROW_MAJOR", "COLUMN_MAJOR"])
@pytest.mark.parametrize(
    "path",
    [
        "create-public",
        "create-native",
        "create-from-public",
        "strides-public",
        "strides-native",
        "scalar-public",
        "scalar-native",
        "batch-public",
        "batch-native",
        "pipeline-public",
        "pipeline-native",
    ],
)
def test_shape_hot_path(
    *, benchmark: BenchmarkFixture, size: str, order_name: str, path: str
) -> None:
    """分离相同输入的不同边界成本并独立复验 / Separate boundary costs on identical inputs and verify independently.

    Args:
        benchmark: pytest-benchmark 计时器 / Pytest-benchmark timer.
        size: 坐标批次三档大小 / Three coordinate-batch sizes.
        order_name: 行或列存储顺序名称 / Row or column storage-order name.
        path: 构造、步长、标量、批量或含构造流程 / Construction, strides, scalar, batch or full pipeline.
    """
    dims = (8, 9, 10)
    order = StorageOrder[order_name]
    rng = random.Random(20261030)
    vectors = [tuple(rng.randrange(dim) for dim in dims) for _ in range(_SIZES[size])]
    expected = np.ravel_multi_index(
        tuple(zip(*vectors, strict=True)),
        dims,
        order="C" if order is StorageOrder.ROW_MAJOR else "F",
    ).tolist()
    source = DynShape(dims, order)
    native = Shape.from_shape(source).unwrap()
    benchmark.extra_info.update(
        {"coordinates": len(vectors), "dims": dims, "storage_order": order.name}
    )
    if path == "create-public":
        assert benchmark(lambda: DynShape(dims, order)) == source
    elif path == "create-native":
        assert (
            benchmark(
                lambda: Shape.create(dims=dims, storage_order=order).unwrap()
            ).dims
            == dims
        )
    elif path == "create-from-public":
        assert benchmark(lambda: Shape.from_shape(source).unwrap()).dims == dims
    elif path == "strides-public":
        assert benchmark(source.strides) == native.strides()
    elif path == "strides-native":
        assert benchmark(native.strides) == source.strides()
    elif path == "scalar-public":
        assert benchmark(lambda: source.flat_index(*vectors[0])) == expected[0]
    elif path == "scalar-native":
        assert benchmark(lambda: native.index_of(vectors[0]).unwrap()) == expected[0]
    elif path == "batch-public":
        assert benchmark(lambda: [source.flat_index(*v) for v in vectors]) == expected
    elif path == "batch-native":
        assert benchmark(lambda: native.indices_of(vectors).unwrap()) == expected
    elif path == "pipeline-public":

        def public_pipeline() -> list[int]:
            shape = DynShape(dims, order)
            return [shape.flat_index(*v) for v in vectors]

        assert benchmark(public_pipeline) == expected
    else:
        assert (
            benchmark(
                lambda: (
                    Shape.from_shape(DynShape(dims, order))
                    .unwrap()
                    .indices_of(vectors)
                    .unwrap()
                )
            )
            == expected
        )
