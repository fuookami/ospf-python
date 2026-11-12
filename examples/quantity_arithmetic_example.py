"""受检四则保留精确数值并发布真实温差。 / Checked arithmetic keeps exact values and publishes real differences."""

from fractions import Fraction

from ospf_python.quantities import Quantity, QuantityValueRange, Unit
from ospf_python.quantities.unit.length import KILOMETER, METER
from ospf_python.quantities.unit.temperature import CELSIUS


def main() -> None:
    """消费每层 Result，不将控制值混作数量。 / Consume each Result, never confusing control values with quantities."""
    length = (
        Quantity(value=1, unit=METER) + Quantity(value=1, unit=KILOMETER)
    ).unwrap()
    assert length.value == 1001 and length.unit is METER
    third = (Quantity(value=1, unit=METER) / 3).unwrap()
    assert third.value == Fraction(1, 3)
    delta = (
        Quantity(value=80, unit=CELSIUS) - Quantity(value=20, unit=CELSIUS)
    ).unwrap()
    assert not delta.unit.is_affine and delta.value == 60
    scaled = (delta * 2).unwrap()
    assert scaled.value == 120
    assert QuantityValueRange(min_qty=delta, max_qty=scaled).contains(delta).unwrap()
    powers = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    point = Unit.create(
        name="point", symbol="P", powers=powers, scale=3, offset=1
    ).unwrap()
    difference = Unit.create(name="difference", symbol="D", powers=powers).unwrap()
    shifted = (
        Quantity(value=0, unit=point) + Quantity(value=1, unit=difference)
    ).unwrap()
    assert shifted.value == Fraction(1, 3) and shifted.unit is point


if __name__ == "__main__":
    main()
