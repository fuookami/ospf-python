"""公开整数完整调用基准。 / Complete-call public integer benchmarks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from ospf_python.math.algebra.number.integer import Integer
from ospf_python.math.algebra.number.numeric_integer import NumericInteger
from ospf_python.math.algebra.number.numeric_u_integer import NumericUInteger
from ospf_python.math.algebra.number.uinteger import UInteger

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


@pytest.mark.benchmark
@pytest.mark.parametrize("cls", (Integer, UInteger, NumericInteger, NumericUInteger))
@pytest.mark.parametrize("bits", (16, 1024, 16385))
@pytest.mark.parametrize("operation", ("construct", "add", "multiply", "less"))
def test_public_integer_complete_call(
    *, benchmark: BenchmarkFixture, cls: Any, bits: int, operation: str
) -> None:
    value = (1 << bits) + 7
    left, right = cls(value), cls(3)

    def invoke() -> Any:
        if operation == "construct":
            return cls(value).value
        if operation == "add":
            result = left.safe_add(right) if cls is NumericInteger else left + right
            return result.value
        if operation == "multiply":
            result = left.safe_mul(right) if cls is NumericInteger else left * right
            return result.value
        return left < right

    expected: int | bool
    if operation == "construct":
        expected = (
            min(value, NumericInteger.MAX_VALUE) if cls is NumericInteger else value
        )
    elif operation == "less":
        expected = False
    else:
        calculated = (
            left.value + right.value if operation == "add" else left.value * right.value
        )
        expected = (
            min(calculated, NumericInteger.MAX_VALUE)
            if cls is NumericInteger
            else calculated
        )
    assert benchmark(invoke) == expected
