"""公开整数保留精确域与不同钳制政策。 / Public integers retain exact domains and distinct clamp policies."""

from ospf_python.math.algebra.number.integer import Integer
from ospf_python.math.algebra.number.numeric_integer import NumericInteger
from ospf_python.math.algebra.number.numeric_u_integer import NumericUInteger
from ospf_python.math.algebra.number.uinteger import UInteger


def main() -> None:
    """运行无需 solver 的整数示例。 / Run the integer example without a solver."""
    value = 2**256
    assert (Integer(value) + Integer(7)).value == value + 7
    assert (Integer(-7) / Integer(3)).value == -3
    assert (Integer(7) / Integer(0)).value == 0
    assert (UInteger(3) - UInteger(7)).value == 0
    assert NumericInteger(-1).safe_mul(2**1000).value == NumericInteger.MIN_VALUE
    assert (NumericUInteger(value) * NumericUInteger(3)).value == 3 * value
    print("Integer: unbounded / floor(-7/3)=-3 / zero sentinel=0")
    print("UInteger: subtraction clamps to zero")
    print("NumericInteger: exact arithmetic before bounded result")
    print("NumericUInteger: nonnegative without a u64 ceiling")


if __name__ == "__main__":
    main()
