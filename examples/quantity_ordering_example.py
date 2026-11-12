"""原生数量极值与范围示例。 / Native quantity extrema and range example."""

from fractions import Fraction

from ospf_python.quantities import (
    Quantity,
    QuantityValueRange,
    max_quantity,
    min_quantity,
)
from ospf_python.quantities.unit.length import KILOMETER, METER
from ospf_python.quantities.unit.mass import KILOGRAM


def main() -> None:
    """显式消费 Result 并保留原对象。 / Consume Result explicitly and retain original items."""
    first = Quantity(value=Fraction(1, 3), unit=KILOMETER)
    second = Quantity(value=Fraction(500), unit=METER)
    assert min_quantity([first, second]).unwrap() is first
    assert max_quantity([first, second]).unwrap() is second
    bounds = QuantityValueRange(min_qty=first, max_qty=second)
    assert bounds.contains(Quantity(value=Fraction(400), unit=METER)).unwrap()
    assert bounds.contains(Quantity(value=Fraction(400), unit=KILOGRAM)).is_failed()
    print("Quantity extrema: original objects, exact SI ordering, explicit Result")
    print("QuantityValueRange: inclusive Rust comparison; dimension mismatch=Failed")


if __name__ == "__main__":
    main()
