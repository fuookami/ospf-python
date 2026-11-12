"""普通 view 物化完整调用基准 / Complete-call plain view materialization benchmarks."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import pytest

from ospf_python.multiarray import (
    MultiArray,
    MultiArrayView,
    MutableMultiArray,
    Shape2,
    StorageOrder,
)
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


@pytest.mark.benchmark
@pytest.mark.parametrize("dims", [(2, 4), (100, 100), (250, 400)])
@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("domain", ["int16", "float64", "object", "quantity"])
@pytest.mark.parametrize("cropped", [False, True])
def test_public_view_materialization_complete_operation(
    *,
    benchmark: BenchmarkFixture,
    dims: tuple[int, int],
    storage: type[Any],
    order: StorageOrder,
    domain: str,
    cropped: bool,
) -> None:
    count = dims[0] * dims[1]
    data: np.ndarray[Any, Any]
    if domain == "int16":
        data = (np.arange(count) % 17).astype(np.int16)
    elif domain == "float64":
        data = (np.arange(count) % 17).astype(np.float64) / 8
    else:
        data = np.empty(count, dtype=object)
        for index in range(count):
            value = Fraction(index % 17, 8)
            data[index] = value if domain == "object" else Quantity(value, METER)
    shape = Shape2(*dims, order)
    offsets = (1, 1) if cropped else (0, 0)
    view = MultiArrayView(storage(shape, data), offsets=offsets)

    def operation() -> Any:
        return view.materialize().unwrap()

    actual = benchmark(operation)
    layout: Literal["F", "C"] = "F" if order is StorageOrder.COLUMN_MAJOR else "C"
    expected = data.reshape(dims, order=layout)[offsets[0] :, offsets[1] :].ravel(
        order=layout
    )
    np.testing.assert_array_equal(actual._data, expected)
    assert actual._data.dtype == data.dtype
    assert actual.shape.dims == tuple(
        dim - offset for dim, offset in zip(dims, offsets, strict=True)
    )
    assert actual.shape.storage_order is order
    assert not np.shares_memory(actual._data, data)
