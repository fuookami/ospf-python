"""公共笛卡尔积完整调用基准 / Complete public Cartesian-product call benchmarks."""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Any

import pytest

from ospf_python.math.combinatorics import cross
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER


@pytest.mark.parametrize(
    "dims",
    [
        (4, 5),
        (100, 100),
        (100, 1000),
        (10, 10, 100),
        (10,) * 4,
        (10,) * 5,
        (4,) * 6,
        (2,) * 13,
        (10000,),
        (1,) * 256,
    ],
)
@pytest.mark.parametrize("domain", ["integer", "exact-quantity"])
def test_public_cartesian_product(
    *, benchmark: Any, dims: tuple[int, ...], domain: str
) -> None:
    pools = [
        list(range(size))
        if domain == "integer"
        else [Quantity(Fraction(index, 3), METER) for index in range(size)]
        for size in dims
    ]
    expected = list(itertools.product(*pools))

    def invoke() -> list[tuple[Any, ...]]:
        return cross(*pools).unwrap()

    result = benchmark(invoke)
    assert result == expected
    assert len(result) == len(expected)
