"""完整自然选择路径的独立位置 oracle。 / Independent positional oracle for natural selection calls."""

from __future__ import annotations

import itertools
from collections.abc import Callable
from fractions import Fraction
from typing import Any

import pytest

from ospf_python._binding.result import BindingResult
from ospf_python.math.combinatorics.combinations import combinations
from ospf_python.math.combinatorics.permutations import permutations
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER

Selection = Callable[[Any, int], BindingResult[list[list[Any]]]]
"""自然 Result 入口类型。 / Natural Result entry-point type."""

SHAPES = {
    "thin": ((4, 1), (64, 1), (4096, 1)),
    "partial": ((4, 2), (8, 3), (10, 4)),
    "dense-combinations": ((4, 4), (12, 11), (16, 15)),
    "dense-permutations": ((4, 4), (7, 6), (8, 7)),
}


class Indexed:
    """无迭代快照的索引源。 / Indexed source without an iterable snapshot."""

    def __init__(self, values: list[Any]) -> None:
        self.values = values

    def __len__(self) -> int:
        return len(self.values)

    def __getitem__(self, index: int) -> Any:
        return self.values[index]

    def __iter__(self) -> Any:
        raise AssertionError("must not snapshot external input")


@pytest.mark.parametrize("name", ["combinations", "permutations"])
@pytest.mark.parametrize("protocol", ["exact-list", "live-indexed"])
@pytest.mark.parametrize("profile", ["thin", "partial", "dense"])
@pytest.mark.parametrize("scale", [0, 1, 2])
@pytest.mark.parametrize("domain", ["integer", "fraction", "quantity", "opaque"])
def test_complete_public_selection(
    *, benchmark: Any, name: str, protocol: str, profile: str, scale: int, domain: str
) -> None:
    key = "dense-" + name if profile == "dense" else profile
    n, k = SHAPES[key][scale]
    leaves: list[Any]
    if domain == "integer":
        leaves = list(range(n))
    elif domain == "fraction":
        leaves = [Fraction(index, 17) for index in range(n)]
    elif domain == "quantity":
        leaves = [Quantity(Fraction(index, 17), METER) for index in range(n)]
    else:
        leaves = [object() for _ in range(n)]
    source = Indexed(leaves) if protocol == "live-indexed" else leaves
    operation: Selection = combinations if name == "combinations" else permutations
    oracle = (
        itertools.combinations if name == "combinations" else itertools.permutations
    )
    actual: list[list[Any]] = benchmark(lambda: operation(source, k).unwrap())
    expected = list(oracle(range(n), k))
    assert len(actual) == len(expected)
    for row, indices in zip(actual, expected, strict=True):
        assert type(row) is list
        assert len(row) == k
        assert all(
            leaf is leaves[index] for leaf, index in zip(row, indices, strict=True)
        )
