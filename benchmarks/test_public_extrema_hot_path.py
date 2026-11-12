"""比较完整极值调用，不代表性能验收。 / Compare complete extrema calls, not acceptance."""

from __future__ import annotations

from typing import Any

import pytest

from ospf_python.math.ordinary.min_max import max_of, min_max_of, min_of


@pytest.mark.parametrize("count", (1, 16, 1024, 10000))
@pytest.mark.parametrize("operation", ("min", "max", "minmax"))
@pytest.mark.parametrize("candidate", (False, True), ids=("before", "candidate"))
def test_complete_call(
    *, benchmark: Any, count: int, operation: str, candidate: bool
) -> None:
    values = [(index * 104729) % 10007 for index in range(count)]

    def before() -> Any:
        if operation == "min":
            return min(values)
        if operation == "max":
            return max(values)
        collected = list(values)
        return min(collected), max(collected)

    def current() -> Any:
        if operation == "min":
            return min_of(values).unwrap()
        if operation == "max":
            return max_of(values).unwrap()
        return min_max_of(values).unwrap()

    expected = before()
    output = benchmark(current if candidate else before)
    if operation == "minmax":
        assert output[0] is expected[0] and output[1] is expected[1]
    else:
        assert output is expected
