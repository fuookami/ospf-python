"""带精确物理量的公共笛卡尔积 / Public Cartesian products retaining exact quantities."""

from __future__ import annotations

from fractions import Fraction

from ospf_python.math.combinatorics import cross
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.functional.result import Failed, Ok


def main() -> None:
    """消费现有 Result，不隐式转浮点 / Consume the existing Result without implicit floating conversion."""
    lengths = [Quantity(Fraction(1, 2), METER), Quantity(Fraction(3, 2), METER)]
    heights = [Quantity(Fraction(1), METER), Quantity(Fraction(2), METER)]
    result = cross((length for length in lengths), heights)
    match result:
        case Ok(patterns):
            for length, height in patterns:
                print(
                    f"{length.value} {length.unit.symbol} x {height.value} {height.unit.symbol}"
                )
        case Failed(error):
            print(error.message)


if __name__ == "__main__":
    main()
