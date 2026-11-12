"""公共物理归约完整调用基准 / Full-call public physical reduction benchmarks."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from ospf_python.multiarray import MultiArray, MutableMultiArray, Shape2, StorageOrder
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


@pytest.mark.benchmark
@pytest.mark.parametrize("count", [8, 10_000, 100_000])
@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("domain", ["int16", "float64", "object", "quantity"])
def test_public_reduce_complete_operation(
    *,
    benchmark: BenchmarkFixture,
    count: int,
    cls: type[Any],
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
    source = cls(Shape2(2, count // 2, order), data)

    def add(left: Any, right: Any) -> Any:
        return (left + right).unwrap() if domain == "quantity" else left + right

    def operation() -> Any:
        return source.reduce(add).unwrap()

    result = benchmark(operation)
    # 独立整数 oracle，不以新/旧路径互相证明正确。 / Use an independent integer oracle, not mutual new/old agreement.
    total = sum(index % 17 for index in range(count))
    if domain == "quantity":
        assert result == Quantity(Fraction(total, 8), METER)
    elif domain == "float64":
        assert result == Fraction(total, 8)
    else:
        assert result == total
