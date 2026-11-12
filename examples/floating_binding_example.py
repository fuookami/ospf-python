"""浮点 DTO、同单位量与历史比较政策。 / Floating DTOs, same-unit quantities, and legacy comparison policy."""

import math
import pickle

import ospf_python.utils.functional.ord as ord_module
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER


def main() -> None:
    """运行无需 solver 的浮点示例。 / Run the floating example without a solver."""
    left = Quantity(value=Floating(7.25), unit=METER)
    right = Quantity(value=Floating(2.5), unit=METER)
    total, remaining = pickle.loads(
        pickle.dumps(((left + right).unwrap(), (left - right).unwrap()))
    )
    assert total.value == Floating(9.75)
    assert remaining.value == Floating(4.75)
    assert math.copysign(1.0, (-Floating(0.0)).value) == -1.0
    assert (Floating(7.0) / Floating(-0.0)).value == 0.0
    assert Floating(math.nan).cmp(Floating(1.0)) is ord_module.Order.EQ
    print("Floating: same-unit total=9.75 m / remaining=4.75 m")
    print("Floating: signed zero and legacy zero-division/NaN policies preserved")


if __name__ == "__main__":
    main()
