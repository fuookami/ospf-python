"""原生温差单位的复制、pickle 和显式 DTO。 / Copy, pickle and explicit DTO for a native temperature difference."""

from __future__ import annotations

import copy
import pickle
from fractions import Fraction

from ospf_python.quantities import Quantity, QuantityValueRange, Unit
from ospf_python.quantities.unit.temperature import CELSIUS


def main() -> None:
    """恢复后继续公开四则及范围检查。 / Continue public arithmetic and range checks after restoration."""
    capacity = (
        Quantity(value=Fraction(80), unit=CELSIUS)
        .subtract(Quantity(value=Fraction(20), unit=CELSIUS))
        .unwrap()
    )
    assert isinstance(capacity.unit, Unit)
    restored = Quantity.from_json(capacity.to_json().unwrap()).unwrap()
    for quantity in (
        restored,
        copy.deepcopy(capacity),
        pickle.loads(pickle.dumps(capacity)),
    ):
        assert quantity.unit.descriptor() == capacity.unit.descriptor()
        assert not quantity.unit.is_affine
        quarter = quantity.divide(Fraction(4)).unwrap()
        assert quarter.value == 15
        assert quarter.multiply(Fraction(4)).unwrap().value == 60
        assert (
            QuantityValueRange(min_qty=capacity, max_qty=capacity)
            .contains(quantity)
            .unwrap()
        )
    print("Native quantity snapshot round trip: 60, quarter: 15")


if __name__ == "__main__":
    main()
