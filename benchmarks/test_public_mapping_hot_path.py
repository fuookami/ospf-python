"""公共映射完整操作基准 / Full-operation public mapping benchmarks."""

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
@pytest.mark.parametrize("method", ["map", "flat_map"])
def test_public_mapping_complete_operation(
    *,
    benchmark: BenchmarkFixture,
    count: int,
    cls: type[Any],
    order: StorageOrder,
    domain: str,
    method: str,
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

    def double(value: Any) -> Any:
        return (value * 2).unwrap() if domain == "quantity" else value * 2

    callback = double if method == "map" else (lambda value: (value, double(value)))

    def operation() -> Any:
        return getattr(source, method)(callback).unwrap()

    result = benchmark(operation)
    expected = []
    # 独立整数/精确单位 oracle，不以新旧一致替代正确性。 / Independent integer/exact-unit oracle, not merely new/old agreement.
    for index in range(count):
        value: Any = (
            Fraction(index % 17, 8) if domain in {"float64", "quantity"} else index % 17
        )
        if domain == "quantity":
            value = Quantity(value, METER)
        doubled = (
            Quantity(value.value * 2, METER) if domain == "quantity" else value * 2
        )
        expected.extend([doubled] if method == "map" else [value, doubled])
    assert result._data.tolist() == expected
    assert result.shape is source.shape
