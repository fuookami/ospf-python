"""普通 offset 视图的精确单位副本 / Exact-unit copy of a plain offset view."""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from ospf_python.multiarray import MultiArray, MultiArrayView, Shape2, StorageOrder
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.functional.result import Failed, Ok


def main() -> None:
    """验证两种布局的独立区域 / Verify a detached region in both layouts."""
    for order in StorageOrder:
        data = np.empty(12, dtype=object)
        for index in range(12):
            data[index] = Quantity(Fraction(index + 1, 2), METER)
        source: MultiArray[Quantity[Fraction], Shape2] = MultiArray(
            Shape2(3, 4, order), data
        )
        view = MultiArrayView(source, offsets=(1, 1))
        match view.materialize():
            case Ok(result):
                assert result.shape.dims == (2, 3)
                assert result.shape.storage_order is order
                assert not np.shares_memory(result._data, data)
                for row in range(2):
                    for column in range(3):
                        leaf = result.get(row, column)
                        assert leaf is source.get(row + 1, column + 1)
                        assert leaf.unit is METER
                assert view.shape is source.shape
            case Failed(error):
                print(error.message)
                return
    print("Offset materialization preserves exact units in both layouts.")


if __name__ == "__main__":
    main()
