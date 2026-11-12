"""共享数组的精确物理量归约 / Exact quantity reduction over a shared array."""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from ospf_python.multiarray import MultiArray, Shape1
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.functional.result import Failed, Ok


def main() -> None:
    """演示 Result、泛型叶和共享更新 / Demonstrate Result, generic leaves and shared updates."""
    values = np.empty(3, dtype=object)
    for index, numerator in enumerate((1, 2, 3)):
        values[index] = Quantity(Fraction(numerator, 2), METER)
    source: MultiArray[Quantity[Fraction], Shape1] = MultiArray(Shape1(3), values)

    def combine(
        left: Quantity[Fraction], right: Quantity[Fraction]
    ) -> Quantity[Fraction]:
        values[2] = Quantity(Fraction(5, 2), METER)
        output = (left + right).unwrap()
        assert isinstance(output, Quantity)
        return output

    match source.reduce(combine):
        case Ok(total):
            assert total == Quantity(Fraction(4), METER)
            print(f"Total length: {total.value} {total.unit.symbol}")
        case Failed(error):
            print(error.message)


if __name__ == "__main__":
    main()
