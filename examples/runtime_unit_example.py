"""原生温差输出单位参与公开转换和范围。 / Native difference output units participate in public conversion and ranges."""

from fractions import Fraction

from ospf_python.quantities import Quantity, QuantityValueRange, Unit, min_quantity


def main() -> None:
    """演示真实原生输出单位而非点别名。 / Demonstrate a real native output unit, not a point alias."""
    powers = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    point = Unit.create(name="point", symbol="P", powers=powers, offset=273).unwrap()
    value, difference = point.binary_exact(
        value=80, other=20, other_unit=point, subtract=True
    ).unwrap()
    assert not difference.is_affine
    original = Quantity(value=Fraction(*value.as_integer_ratio()), unit=difference)
    target = Unit.create(name="linear difference", symbol="dK", powers=powers).unwrap()
    converted = original.to(target).unwrap()
    assert (
        converted.value == 60
        and min_quantity([original, converted]).unwrap() is original
    )
    assert (
        QuantityValueRange(min_qty=converted, max_qty=converted)
        .contains(original)
        .unwrap()
    )


if __name__ == "__main__":
    main()
