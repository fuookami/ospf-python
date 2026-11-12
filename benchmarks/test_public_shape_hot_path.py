"""公开形状含构造的完整计算基准 / Complete public shape arithmetic including construction."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import pytest

from ospf_python.multiarray import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
)

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

_CASES = [
    (Shape1, (2,)),
    (Shape2, (2, 3)),
    (Shape3, (2, 3, 4)),
    (Shape4, (2, 3, 4, 5)),
    (DynShape, (2, 3, 2, 3, 2, 3, 2, 3)),
]


@pytest.mark.benchmark
@pytest.mark.parametrize(("storage", "dims"), _CASES)
@pytest.mark.parametrize("count", [8, 256, 2048])
@pytest.mark.parametrize("order", list(StorageOrder))
def test_public_shape_complete_pipeline(
    *,
    benchmark: BenchmarkFixture,
    storage: type[Any],
    dims: tuple[int, ...],
    count: int,
    order: StorageOrder,
) -> None:
    rng = random.Random(20261025)
    vectors = [tuple(rng.randrange(dim) for dim in dims) for _ in range(count)]
    layout: Literal["C", "F"] = "C" if order is StorageOrder.ROW_MAJOR else "F"
    offsets = np.ravel_multi_index(
        tuple(zip(*vectors, strict=True)), dims, order=layout
    ).tolist()
    strides = np.empty(dims, dtype=np.int8, order=layout).strides

    def operation() -> Any:
        shape = storage(dims, order) if storage is DynShape else storage(*dims, order)
        return (
            shape.size,
            shape.strides(),
            [shape.flat_index(*indices) for indices in vectors],
        )

    assert benchmark(operation) == (int(np.prod(dims)), strides, offsets)
