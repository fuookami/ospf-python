"""公开素数筛完整调用合同，预算另做独立对照。 / Complete public sieve calls; budgets need independent comparison."""

from __future__ import annotations

from typing import Any

import pytest

from ospf_python.math.ordinary.prime import primes_up_to


@pytest.mark.parametrize(
    ("limit", "count"), [(100, 25), (10_000, 1229), (1_000_000, 78498)]
)
def test_public_prime_sieve_complete_call(
    *, benchmark: Any, limit: int, count: int
) -> None:
    def invoke() -> list[int]:
        return primes_up_to(limit).unwrap()

    output = benchmark(invoke)
    assert len(output) == count and output[0] == 2 and output[-1] <= limit
