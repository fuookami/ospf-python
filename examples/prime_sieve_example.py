"""显式消费固定 Rust 素数筛的 Result。 / Explicitly consume the pinned Rust sieve Result."""

from __future__ import annotations

from ospf_python.math.ordinary.prime import primes_up_to


def main() -> None:
    """列出包含上界的素数。 / Show primes including the upper bound."""
    primes_up_to(29).on_success(
        lambda primes: print(f"Primes up to 29: {primes}")
    ).on_failure(lambda error: print(error.message))


if __name__ == "__main__":
    main()
