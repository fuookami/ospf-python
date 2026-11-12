"""公共嵌套导出的完整调用基准 / Full-call public nested-export benchmarks."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from ospf_python.multiarray import (
    DynShape,
    MultiArray,
    MutableMultiArray,
    Shape2,
    StorageOrder,
)
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


def _data(count: int, domain: str) -> np.ndarray[Any, Any]:
    if domain == "int16":
        return (np.arange(count) % 17).astype(np.int16)
    if domain == "float64":
        return (np.arange(count) % 17).astype(np.float64) / 8
    data = np.empty(count, dtype=object)
    for index in range(count):
        fraction = Fraction(index % 17, 8)
        data[index] = fraction if domain == "object" else Quantity(fraction, METER)
    return data


@pytest.mark.benchmark
@pytest.mark.parametrize("count", [8, 10_000, 100_000])
@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("domain", ["int16", "float64", "object", "quantity"])
def test_public_nested_complete_operation(
    *,
    benchmark: BenchmarkFixture,
    count: int,
    cls: type[Any],
    order: StorageOrder,
    domain: str,
) -> None:
    data = _data(count, domain)
    source = cls(Shape2(2, count // 2, order), data)

    def operation() -> Any:
        return source.to_list().unwrap()

    actual = benchmark(operation)
    for row in range(2):
        for col in range(count // 2):
            offset = (
                row * (count // 2) + col
                if order is StorageOrder.ROW_MAJOR
                else row + col * 2
            )
            value = Fraction(offset % 17, 8) if domain != "int16" else offset % 17
            expected: Any = Quantity(value, METER) if domain == "quantity" else value
            assert actual[row][col] == expected


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "dims",
    [
        (10_000,),
        (100, 100),
        (5_000, 2),
        (10_000, 1),
        (10, 10, 100),
        (10, 10, 100, 1),
        (100_000,),
        (100, 1_000),
        (50_000, 2),
        (100_000, 1),
        (10, 10, 1_000),
        (10, 10, 1_000, 1),
    ],
)
@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("domain", ["int16", "float64", "object", "quantity"])
def test_public_nested_shape_distribution(
    *,
    benchmark: BenchmarkFixture,
    dims: tuple[int, ...],
    cls: type[Any],
    order: StorageOrder,
    domain: str,
) -> None:
    data = _data(int(np.prod(dims)), domain)
    source = cls(DynShape(dims, order), data)
    expected = data.reshape(
        dims, order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    ).tolist()

    def operation() -> Any:
        return source.to_list().unwrap()

    actual = benchmark(operation)
    assert actual == expected
    if domain in ("object", "quantity"):
        leaf = actual
        for _ in dims:
            leaf = leaf[0]
        assert leaf is data[0]
