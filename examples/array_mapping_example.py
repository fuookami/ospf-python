"""共享物理量映射与展开 / Shared quantity mapping and expansion."""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from ospf_python.multiarray import MultiArray, Shape1
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.functional.result import Failed, Ok


def main() -> None:
    """演示 Result 与 live 精确单位 / Demonstrate Result and live exact units."""
    data = np.empty(2, dtype=object)
    data[0] = Quantity(Fraction(1, 2), METER)
    data[1] = Quantity(Fraction(2), METER)
    source: MultiArray[Quantity[Fraction], Shape1] = MultiArray(Shape1(2), data)

    def double(value: Quantity[Fraction]) -> Quantity[Fraction]:
        data[1] = Quantity(Fraction(3, 2), METER)
        output = (value * 2).unwrap()
        assert isinstance(output, Quantity)
        return output

    match source.map(double):
        case Ok(mapped):
            match mapped.flat_map(lambda value: (value, (value * 2).unwrap())):
                case Ok(expanded):
                    assert [leaf.value for leaf in expanded._data] == [1, 2, 3, 6]
                    assert all(leaf.unit is METER for leaf in expanded._data)
                    print("Mapped lengths: 1, 2, 3, 6 m")
                case Failed(error):
                    print(error.message)
        case Failed(error):
            print(error.message)


if __name__ == "__main__":
    main()
