"""精确单位转换、Result 与自定义数值边界。 / Exact unit conversion, Result and custom numeric boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal
from fractions import Fraction
from typing import Any

from ospf_python.quantities import NumericAdapter, Quantity
from ospf_python.quantities.unit.length import KILOMETER, METER
from ospf_python.quantities.unit.mass import KILOGRAM
from ospf_python.utils.functional.result import Failed, Ok, Result


@dataclass(frozen=True)
class LengthValue:
    """业务精确值。 / Exact business value.

    Attributes:
        fraction: 不经 float 的值。 / Value without float conversion.
    """

    fraction: Fraction


class LengthAdapter(NumericAdapter[LengthValue]):
    """业务表示策略，不实现单位换算。 / Business representation policy, not unit conversion."""

    def to_fraction(self, value: LengthValue) -> Result[Fraction, Any, Any]:
        """导入业务值。 / Import a business value.

        Args:
            value: 业务长度数值。 / Business length value.

        Returns:
            精确分数。 / Exact fraction.
        """
        return Ok(value.fraction)

    def from_fraction(self, value: Fraction) -> Result[LengthValue, Any, Any]:
        """恢复业务表示。 / Restore the business representation.

        Args:
            value: Rust 换算结果。 / Rust conversion result.

        Returns:
            业务值。 / Business value.
        """
        return Ok(LengthValue(value))


def main() -> None:
    """运行不需要 solver 的自然入口示例。 / Run the natural-entry example without a solver."""
    exact = Quantity(value=Fraction(1, 3), unit=KILOMETER).to(METER).unwrap()
    business = (
        Quantity(value=LengthValue(Fraction(1, 3)), unit=KILOMETER)
        .to(METER, numeric_adapter=LengthAdapter())
        .unwrap()
    )
    decimal = (
        Quantity(value=Decimal("1.2300"), unit=METER)
        .to(METER, context=Context(prec=30))
        .unwrap()
    )
    assert exact.value == business.value.fraction == Fraction(1000, 3)
    assert decimal.value == Decimal("1.23")
    mismatch = Quantity(value=1, unit=METER).to(KILOGRAM)
    assert isinstance(mismatch, Failed)
    print("Quantity.to: 1/3 km -> 1000/3 m (Result, exact Fraction)")
    print("Quantity.to: explicit custom numeric adapter, no implicit float")
    print("Quantity.to: Decimal canonical export=1.23; dimension mismatch=Failed")


if __name__ == "__main__":
    main()
