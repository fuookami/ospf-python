"""列布局惰性物化的精确单位示例 / Exact-unit lazy materialization in column layout."""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from ospf_python.multiarray import MultiArray, MultiArrayView, Shape2
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.functional.result import Failed, Ok


def main() -> None:
    """验证转置后每个物化坐标 / Verify every materialized coordinate after transpose."""
    data = np.empty(6, dtype=object)
    for index in range(6):
        data[index] = Quantity(Fraction(index + 1, 2), METER)
    source: MultiArray[Quantity[Fraction], Shape2] = MultiArray(Shape2(2, 3), data)
    match source.transpose():
        case Ok(transposed):
            pass
        case Failed(error):
            print(error.message)
            return
    lazy = MultiArrayView(transposed).map(lambda value: (value * 2).unwrap())
    match lazy.materialize():
        case Ok(result):
            assert result.shape is transposed.shape
            for row in range(3):
                for column in range(2):
                    assert (
                        result.get(row, column)
                        == (transposed.get(row, column) * 2).unwrap()
                    )
            print("Materialized lengths retain all transposed coordinates.")
        case Failed(error):
            print(error.message)


if __name__ == "__main__":
    main()
