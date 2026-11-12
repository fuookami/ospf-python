"""公开初等运算完整调用正确性，不冒充预算验收。 / Complete public elementary-operation correctness, not budget acceptance."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import pytest

from ospf_python.math.operator.exp import exp2_op, exp10_op, exp_op
from ospf_python.math.operator.log import log2_op, log10_op, log_op
from ospf_python.math.operator.trigonometry import (
    acos_op,
    asin_op,
    atan_op,
    cos_op,
    sin_op,
    tan_op,
)

CASES: tuple[
    tuple[str, Callable[[float], Any], Callable[[float], float], float], ...
] = (
    ("exp", exp_op, math.exp, 1.0),
    ("exp2", exp2_op, math.exp2, 10.0),
    ("exp10", exp10_op, lambda value: float(10.0**value), 2.0),
    ("ln", log_op, math.log, math.e),
    ("log2", log2_op, math.log2, 8.0),
    ("log10", log10_op, math.log10, 1000.0),
    ("sin", sin_op, math.sin, math.pi / 2),
    ("cos", cos_op, math.cos, math.pi),
    ("tan", tan_op, math.tan, math.pi / 4),
    ("asin", asin_op, math.asin, 1.0),
    ("acos", acos_op, math.acos, 0.0),
    ("atan", atan_op, math.atan, 1.0),
)


@pytest.mark.parametrize(
    ("name", "operation", "reference", "value"),
    CASES,
    ids=[name for name, _, _, _ in CASES],
)
def test_public_elementary_complete_call(
    *,
    benchmark: Any,
    name: str,
    operation: Callable[[float], Any],
    reference: Callable[[float], float],
    value: float,
) -> None:
    def invoke() -> float:
        return operation(value).unwrap()

    output = benchmark(invoke)
    expected = reference(value)
    assert type(output) is float
    assert output == pytest.approx(expected, rel=4e-15, abs=0.0)
