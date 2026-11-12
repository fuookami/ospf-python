"""公开整数幂完整调用合同，不冒充预算验收。 / Complete public integer-power calls, not budget acceptance."""

from __future__ import annotations

from typing import Any

import pytest

from ospf_python.math.ordinary.pow import pow_int


@pytest.mark.parametrize(
    ("base", "exp"),
    [
        (3, 64),
        (2**127 + 19, 257),
        (3, 65536),
        (2**257 + 13, 4096),
        (2, 1_000_000),
        (-3, 65535),
    ],
    ids=("small", "wide-base", "dense", "wide-dense", "sparse", "negative-dense"),
)
def test_public_integer_power_complete_call(
    *, benchmark: Any, base: int, exp: int
) -> None:
    def invoke() -> int:
        return pow_int(base, exp).unwrap()

    output = benchmark(invoke)
    assert type(output) is int and output == pow(base, exp)
