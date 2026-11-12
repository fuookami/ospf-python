"""公开对数完整调用正确性，不冒充预算验收。 / Complete public logarithm correctness, not budget acceptance."""

from __future__ import annotations

import math
from typing import Any

import pytest

from ospf_python.math.ordinary.log import log_base


@pytest.mark.parametrize(
    ("x", "base"),
    [
        (8.0, 2.0),
        (1e300, 10.0),
        (0.125, 0.5),
        ((1 << 2048) + 123, 2),
        (2, 1 << 2048),
        (1 << 4096, 1 << 2048),
    ],
    ids=("small", "large-float", "fractional", "wide-x", "wide-base", "both-wide"),
)
def test_public_logarithm_complete_call(*, benchmark: Any, x: Any, base: Any) -> None:
    def invoke() -> float:
        return log_base(x, base).unwrap()

    output = benchmark(invoke)
    assert type(output) is float
    assert math.isclose(output, math.log(x) / math.log(base), rel_tol=4e-15)
