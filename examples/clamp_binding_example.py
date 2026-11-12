"""显式处理值域限制 Result。 / Explicitly consume the clamp Result."""

from __future__ import annotations

from fractions import Fraction

from ospf_python.math.ordinary.clamp import clamp


def main() -> None:
    """保留精确分数。 / Preserve exact fractions."""
    result = clamp(Fraction(3, 2), min_val=Fraction(0), max_val=Fraction(1))
    result.on_success(lambda value: print(f"clamp: {value}"))


if __name__ == "__main__":
    main()
