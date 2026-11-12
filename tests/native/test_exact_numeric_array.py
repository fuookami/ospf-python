"""精确批量值与单次跨语言归约合同 / Exact batches and single-crossing reduction contracts."""

from __future__ import annotations

import gc
import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.numeric import RationalArray
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


def fractions(values: RationalArray) -> list[Fraction]:
    return [Fraction(*ratio) for ratio in values.as_integer_ratios()]


def test_creation_is_rust_owned_normalized_and_detached() -> None:
    inputs = [(6, -8), (0, -3), ((1 << 20000) + 1, 1 << 17000)]
    values = RationalArray.create(inputs).unwrap()
    assert isinstance(values._handle, _native.RationalArray)
    assert len(values) == 3
    assert values.at(0).unwrap().as_integer_ratio() == (-3, 4)
    assert values.at(1).unwrap().as_integer_ratio() == (0, 1)
    assert values.at(2).unwrap().as_integer_ratio() == inputs[2]
    inputs.clear()
    snapshot = values.as_integer_ratios()
    snapshot.clear()
    assert len(values) == 3
    assert not hasattr(values, "__dict__")
    with pytest.raises(FrozenInstanceError):
        values._handle = None  # type: ignore[misc,assignment]
    with pytest.raises(TypeError):
        _native.RationalArray()


@pytest.mark.parametrize(
    "bad",
    [
        None,
        123,
        "pairs",
        ((1, 2),),
        [1],
        [(1,)],
        [(1, 2, 3)],
        [[1, 2]],
        [(1.0, 2)],
        [(True, 2)],
        [(1, False)],
    ],
)
def test_invalid_batch_is_a_result(bad: Any) -> None:
    result = RationalArray.create(bad)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_bad_late_denominator_does_not_publish_a_partial_batch() -> None:
    result = RationalArray.create([(1, 2), (3, 4), (5, 0)])
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert "index: 2" in result.error.message
    assert RationalArray.create([(1, 2)]).unwrap().sum().as_integer_ratio() == (1, 2)


def test_empty_identity_and_empty_elementwise_operations() -> None:
    empty = RationalArray.create([]).unwrap()
    assert len(empty) == 0
    assert empty.sum().as_integer_ratio() == (0, 1)
    assert empty.dot(empty).unwrap().as_integer_ratio() == (0, 1)
    for operation in (empty.add, empty.subtract, empty.multiply, empty.divide):
        assert operation(empty).unwrap().as_integer_ratios() == []


@pytest.mark.parametrize(
    "index",
    [-1, 2, 1 << 20000, -(1 << 20000)],
    ids=["negative", "upper", "huge-positive", "huge-negative"],
)
def test_indices_outside_bounds_are_structured_range_errors(index: int) -> None:
    values = RationalArray.create([(1, 2), (3, 4)]).unwrap()
    result = values.at(index)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.OUT_OF_RANGE


@pytest.mark.parametrize("index", [True, 1.0, "0", None])
def test_noninteger_index_is_failed(index: Any) -> None:
    assert RationalArray.create([(1, 2)]).unwrap().at(index).is_failed()


@pytest.mark.parametrize("operation", ["dot", "add", "subtract", "multiply", "divide"])
def test_shape_mismatch_and_wrong_domain_do_not_mutate(operation: str) -> None:
    left = RationalArray.create([(1, 2), (3, 4)]).unwrap()
    right = RationalArray.create([(5, 6)]).unwrap()
    for other in (right, 1, None):
        result = getattr(left, operation)(other)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert left.as_integer_ratios() == [(1, 2), (3, 4)]
    assert right.as_integer_ratios() == [(5, 6)]


def test_zero_divisor_in_last_position_does_not_publish_partial_results() -> None:
    left = RationalArray.create([(1, 2), (3, 4)]).unwrap()
    right = RationalArray.create([(5, 6), (0, 1)]).unwrap()
    result = left.divide(right)
    assert isinstance(result, Failed)
    assert "index: 1" in result.error.message
    assert left.as_integer_ratios() == [(1, 2), (3, 4)]
    assert right.as_integer_ratios() == [(5, 6), (0, 1)]


def test_exact_batch_operations_against_independent_fraction_oracle() -> None:
    rng = random.Random(20261027)
    for size in (1, 5, 30, 100):
        a = [
            Fraction(rng.randrange(-(1 << 128), 1 << 128), rng.choice([2, 3, 5, 7]))
            for _ in range(size)
        ]
        b = [
            Fraction(rng.randrange(1, 1 << 100), rng.choice([2, 3, 5, 11]))
            for _ in range(size)
        ]
        left = RationalArray.create([(x.numerator, x.denominator) for x in a]).unwrap()
        right = RationalArray.create([(x.numerator, x.denominator) for x in b]).unwrap()
        assert Fraction(*left.sum().as_integer_ratio()) == sum(a)
        assert Fraction(*left.dot(right).unwrap().as_integer_ratio()) == sum(
            x * y for x, y in zip(a, b, strict=True)
        )
        assert fractions(left.add(right).unwrap()) == [
            x + y for x, y in zip(a, b, strict=True)
        ]
        assert fractions(left.subtract(right).unwrap()) == [
            x - y for x, y in zip(a, b, strict=True)
        ]
        assert fractions(left.multiply(right).unwrap()) == [
            x * y for x, y in zip(a, b, strict=True)
        ]
        assert fractions(left.divide(right).unwrap()) == [
            x / y for x, y in zip(a, b, strict=True)
        ]


def test_batch_sum_is_not_limited_to_float64_or_python_decimal_digits() -> None:
    big = (1 << 20000) + 1
    values = RationalArray.create([(big, 3), (-big, 3), (1, 10)]).unwrap()
    assert values.sum().as_integer_ratio() == (1, 10)
    assert values.sum().to_float().is_failed()


def test_owned_results_survive_batch_gc_and_parallel_reductions() -> None:
    values = RationalArray.create([(i, 17) for i in range(100)]).unwrap()

    def total(_: int, captured: RationalArray = values) -> tuple[int, int]:
        return captured.sum().as_integer_ratio()

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert set(pool.map(total, range(100))) == {(4950, 17)}
    del total
    child = values.at(5).unwrap()
    summed = values.sum()
    product = values.multiply(values).unwrap()
    del values
    gc.collect()
    assert child.as_integer_ratio() == (5, 17)
    assert summed.as_integer_ratio() == (4950, 17)
    assert product.at(5).unwrap().as_integer_ratio() == (25, 289)
