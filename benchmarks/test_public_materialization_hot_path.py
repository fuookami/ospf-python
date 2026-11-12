"""公共 mapped 物化完整调用基准 / Full-call public mapped materialization benchmarks."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

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
@pytest.mark.parametrize("count", [8, 10_000, 100_000])
@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("domain", ["int16", "float64", "object", "quantity"])
def test_public_materialization_complete_operation(
    *,
    benchmark: BenchmarkFixture,
    count: int,
    storage: type[Any],
    order: StorageOrder,
    domain: str,
) -> None:
    data: np.ndarray[Any, Any]
    if domain == "int16":
        data = (np.arange(count) % 17).astype(np.int16)
    elif domain == "float64":
        data = (np.arange(count) % 17).astype(np.float64) / 8
    else:
        data = np.empty(count, dtype=object)
        for index in range(count):
            data[index] = (
                index % 17
                if domain == "object"
                else Quantity(Fraction(index % 17, 8), METER)
            )
    shape = Shape2(2, count // 2, order)

    def double(value: Any) -> Any:
        return (value * 2).unwrap() if domain == "quantity" else value * 2

    mapped = MultiArrayView(storage(shape, data)).map(double)

    def operation() -> Any:
        return mapped.materialize().unwrap()

    actual = benchmark(operation)
    expected: list[Any] = []
    for index in range(count):
        value: Any = (
            Fraction(index % 17, 8) if domain in {"float64", "quantity"} else index % 17
        )
        if domain == "quantity":
            value = Quantity(value, METER)
        expected.append(
            Quantity(value.value * 2, METER) if domain == "quantity" else value * 2
        )
    assert actual._data.tolist() == expected
    assert actual.shape is shape
