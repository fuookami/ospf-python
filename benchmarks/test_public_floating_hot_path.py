"""浮点公开完整调用基准。 / Complete-call public floating benchmarks."""

from __future__ import annotations

import math
import operator
from typing import TYPE_CHECKING, Any

import pytest

from ospf_python.math.algebra.number.floating import Floating

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "value",
    (1.25, math.ulp(0.0), math.inf, math.nan, (1 << 53) + 7, (1 << 1024) + 7),
    ids=("finite", "subnormal", "infinity", "nan", "integer53", "integer1024"),
)
@pytest.mark.parametrize(
    "operation",
    ("construct", "add", "subtract", "multiply", "divide", "negate", "less"),
)
def test_public_floating_complete_call(
    *, benchmark: BenchmarkFixture, value: Any, operation: str
) -> None:
    left, right = Floating(value), Floating(3 if type(value) is int else 3.0)
    binary = {
        "add": operator.add,
        "subtract": operator.sub,
        "multiply": operator.mul,
        "divide": operator.truediv,
        "less": operator.lt,
    }

    def invoke() -> Any:
        if operation == "construct":
            return Floating(value).value
        if operation == "negate":
            return (-left).value
        result = binary[operation](left, right)
        return result if operation == "less" else result.value

    if operation == "construct":
        expected = value
    elif operation == "negate":
        expected = -value
    else:
        expected = binary[operation](value, right.value)
    actual = benchmark(invoke)
    if isinstance(expected, float) and math.isnan(expected):
        assert math.isnan(actual)
    else:
        assert actual == expected
        if type(expected) is float and expected == 0.0:
            assert math.copysign(1.0, actual) == math.copysign(1.0, expected)
