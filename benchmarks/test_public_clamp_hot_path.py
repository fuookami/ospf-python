"""对照公开调用与迁移前表达式，不代表性能验收。 / Compare public calls to the prior expression, not budget acceptance."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from ospf_python.math.ordinary.clamp import clamp


def _before(value: Any, *, min_val: Any, max_val: Any) -> object:
    return max(min_val, min(value, max_val))


@pytest.mark.parametrize(
    ("value", "lower", "upper"),
    [
        (5, 0, 10),
        (1 << 4096, -(1 << 4096), 1 << 4096),
        (Fraction(3, 2), Fraction(0), Fraction(1)),
    ],
    ids=("small-int", "wide-int", "fraction"),
)
@pytest.mark.parametrize("candidate", (False, True), ids=("before", "candidate"))
def test_complete_call(
    *, benchmark: Any, value: Any, lower: Any, upper: Any, candidate: bool
) -> None:
    def before() -> object:
        return _before(value, min_val=lower, max_val=upper)

    def current() -> object:
        return clamp(value, min_val=lower, max_val=upper).unwrap()

    output = benchmark(current if candidate else before)
    assert output is before()
