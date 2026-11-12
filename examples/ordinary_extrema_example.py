"""显式消费普通极值 Result。 / Explicitly consume ordinary extrema Results."""

from __future__ import annotations

from fractions import Fraction

from ospf_python.math.ordinary.min_max import min_max_of


def main() -> None:
    """在不转换分数的情况下选择极值。 / Select extrema without converting fractions."""
    result = min_max_of([Fraction(1, 3), Fraction(-2, 7), Fraction(4, 5)])
    result.on_success(lambda values: print(f"Extrema: {values}"))


if __name__ == "__main__":
    main()
