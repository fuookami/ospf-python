"""导出列布局精确物理量，不转换为 float / Export column-layout exact quantities without float coercion."""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from ospf_python.multiarray import MultiArray, Shape2, StorageOrder
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.functional.result import Failed


def main() -> None:
    """消费完整逻辑嵌套导出的 Result / Consume the Result of complete logical nested export."""
    values = np.empty(6, dtype=object)
    for index in range(6):
        values[index] = Quantity(Fraction(index + 1, 8), METER)
    source: MultiArray[Quantity[Fraction], Shape2] = MultiArray(
        Shape2(2, 3, StorageOrder.COLUMN_MAJOR), values
    )
    result = source.to_list()
    if isinstance(result, Failed):
        print(result.error.message)
        return
    nested = result.unwrap()
    assert nested == [
        [values[0], values[2], values[4]],
        [values[1], values[3], values[5]],
    ]
    assert nested[0][0] is values[0]
    assert nested[1][2].value == Fraction(3, 4)


if __name__ == "__main__":
    main()
