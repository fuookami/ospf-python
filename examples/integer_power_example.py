"""显式消费固定Rust整数幂Result。 / Explicitly consume pinned Rust integer-power Results."""

from __future__ import annotations

from ospf_python.math.ordinary.pow import pow_int


def main() -> None:
    """保留大整数而不经过float。 / Keep the large integer without a float conversion."""
    pow_int(2, 256).on_success(
        lambda value: print(f"2**256 has {value.bit_length()} bits")
    ).on_failure(lambda error: print(error.message))


if __name__ == "__main__":
    main()
